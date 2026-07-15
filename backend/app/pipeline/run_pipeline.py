"""Orchestrator: the full funnel with a validator gate after EVERY step.

requirements -> Planner -> V1(plan) -> [user approves] -> Scout -> V2(candidates)
-> Qualifier(rank) -> Enricher -> V3(contacts) -> Analyst -> V4(grounded)
-> Closer -> V5(compliance) -> ranked flash cards.
Runs in a background thread; progress + cards live in the DB (frontend polls).
"""
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

from ..agents import analyst, closer, enricher, planner, qualifier, scout, validators
from ..config import get_settings
from ..core.text import as_list, join_str
from ..db.base import SessionLocal
from ..db.models import Card, Run
from ..sources.registry import adapters_by_name
from .gcf import GCF

log = logging.getLogger(__name__)

# lead type -> candidate source adapters (business-first)
LEAD_TYPE_SOURCES = {
    "local_business": ["overpass", "yelp"],
    "companies_web": ["duckduckgo", "tavily", "google_pse", "marginalia", "wikipedia", "github"],
    "job_posts": ["hackernews", "remoteok", "remotive", "adzuna", "jooble", "usajobs"],
    "community_intent": ["reddit", "duckduckgo"],
    "news_signals": ["newsapi", "producthunt"],
}


def _resolve_sources(req: dict) -> list[str]:
    """Explicit source picks win; else derive from lead_types. Intersect with active."""
    active = set(adapters_by_name().keys())
    explicit = [s for s in req.get("sources", []) if s in active]
    if explicit:
        return explicit
    want: set[str] = set()
    for lt in req.get("lead_types") or ["companies_web", "local_business"]:
        want.update(LEAD_TYPE_SOURCES.get(lt, []))
    resolved = [s for s in want if s in active]
    return resolved or list(active)


def _log(db, run: Run, msg: str) -> None:
    log = json.loads(run.log or "[]")
    log.append(f"{datetime.now(UTC).strftime('%H:%M:%S')} {msg}")
    run.log = json.dumps(log[-80:])
    db.commit()


def build_plan(run_id: int) -> None:
    """Stage 1 (sync-ish, fast): Planner + V1. Sets status plan_ready for user approval."""
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        req = json.loads(run.requirements)
        _log(db, run, "planner: building multi-tier plan")
        plan = planner.make_plan(req)
        plan, notes = validators.validate_plan(plan)
        for n in notes:
            _log(db, run, f"V1(plan): {n}")
        run.plan = json.dumps(plan)
        run.status = "plan_ready"
        _log(db, run, "plan ready — waiting for user approval")
        db.commit()
    except Exception as e:
        db.rollback()  # session may be dirty after a DB error; clear before writing status
        run = db.get(Run, run_id)
        if run:
            run.status = "failed"
            run.error = str(e)[:500]
            _log(db, run, f"FAILED at planning: {type(e).__name__}")
            db.commit()
        log.exception("build_plan failed for run %s", run_id)
    finally:
        db.close()


def execute_run(run_id: int) -> None:
    """Stage 2 (after approval): the full funnel."""
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        req = json.loads(run.requirements)
        plan = json.loads(run.plan or "{}")
        service_str = join_str(req.get("service"))
        locations = as_list(req.get("location"))
        gcf = GCF()
        run_node = gcf.add("Run", service=service_str,
                           niche=join_str(req.get("niche")),
                           location=join_str(locations))
        plan_node = gcf.add("Plan", icp=plan.get("icp", ""))
        gcf.link(run_node, "has_plan", plan_node)

        # ── Scout + V2 ──────────────────────────────────────────────
        run.status = "sourcing"
        source_names = _resolve_sources(req)
        _log(db, run, f"scout: hunting across {len(source_names)} sources: {', '.join(sorted(source_names))}")
        db.commit()
        raw, bd, src_errors = scout.run_scout(plan, locations, source_names)
        if bd:
            counts = ", ".join(f"{k}={v}" for k, v in sorted(bd.items(), key=lambda x: -x[1]))
            _log(db, run, f"scout results by source: {counts}")
        if src_errors:
            fails = ", ".join(f"{k} ({v})" for k, v in sorted(src_errors.items()))
            _log(db, run, f"sources that failed to respond: {fails}")
        cands, notes = validators.validate_candidates(raw)
        for n in notes:
            _log(db, run, f"V2(candidates): {n}")
        if not cands:
            raise RuntimeError("No candidates survived sourcing — try broader niche/location.")

        # ── Qualify / rank ─────────────────────────────────────────
        run.status = "ranking"
        _log(db, run, f"qualifier: scoring {len(cands)} candidates")
        db.commit()
        keep = max(int(req.get("max_leads", 10)), 3)
        ranked = qualifier.qualify(cands, req, plan.get("icp", ""), keep=keep)
        _log(db, run, f"qualifier: kept top {len(ranked)}")

        # ── Per-lead: enrich -> V3 -> analyze -> V4 -> close -> V5 ──
        run.status = "diagnosing"
        db.commit()
        service = service_str

        def build_card(item):
            cand, score, reason = item
            enr = enricher.enrich(cand)
            contact, n3 = validators.validate_enrichment(enr.get("email", ""), enr.get("phone", ""))
            enr.update(contact)
            evidence = f"{cand.title} | {cand.snippet} | {enr}"
            ana = analyst.analyze(cand, enr, service)
            ana, n4 = validators.validate_analysis(ana, evidence)
            out = closer.draft_outreach(cand.title, ana, enr, service)
            msg, n5 = validators.validate_outreach(out.get("message", ""))
            out["message"] = msg
            return cand, score, reason, enr, ana, out, (n3 + n4 + n5)

        done = 0
        with ThreadPoolExecutor(max_workers=get_settings().CARD_WORKERS) as ex:
            futs = [ex.submit(build_card, item) for item in ranked]
            for f in as_completed(futs):
                try:
                    cand, score, reason, enr, ana, out, vnotes = f.result()
                except Exception:
                    continue
                # GCF wiring (persisted with the run)
                c_node = gcf.add("Company", name=cand.title, url=cand.url, source=cand.source)
                gcf.link(run_node, "found", c_node)
                card = Card(
                    run_id=run.id, title=cand.title, url=cand.url, source=cand.source,
                    tier=cand.tier, kind=cand.kind, fit_score=score, fit_reason=reason,
                    company=enr.get("company", ""), email=enr.get("email", ""),
                    email_status=enr.get("email_status", "unverified"),
                    phone=enr.get("phone", ""), socials=json.dumps(enr.get("socials", [])),
                    person=enr.get("person", ""), role=enr.get("role", ""),
                    analysis=json.dumps(ana), outreach=json.dumps(out),
                    validator_notes=json.dumps(vnotes[:6]),
                )
                db.add(card)
                done += 1
                _log(db, run, f"card {done}/{len(ranked)}: {cand.title[:40]} (fit {score:.0f}/10)")

        run.gcf = json.dumps(gcf.to_dict())[:200_000]
        run.status = "done" if done else "failed"
        if not done:
            run.error = "No cards could be built (all leads failed analysis)."
        run.finished_at = datetime.now(UTC)
        _log(db, run, f"done — {done} ranked flash cards")
        db.commit()
    except Exception as e:
        db.rollback()  # session may be dirty after a DB error; clear before writing status
        run = db.get(Run, run_id)
        if run:
            run.status = "failed"
            run.error = str(e)[:500]
            _log(db, run, f"FAILED: {type(e).__name__}: {str(e)[:120]}")
            db.commit()
        log.exception("execute_run failed for run %s", run_id)
    finally:
        db.close()
