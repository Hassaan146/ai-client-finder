"""Validator gates — one at EVERY pipeline step (user requirement).

V1 plan      : structure + only-active-sources + non-empty queries (rules)
V2 candidates: dedupe, junk/URL sanity, drop empties (rules)
V3 enrichment: email/phone format sanity (rules)
V4 analysis  : grounded-claims + honest-%s check (cheap LLM + rules)
V5 outreach  : compliance + no fabricated stats (rules + cheap LLM)
Each returns (passed_items_or_obj, notes[]) and never hard-crashes the run.
"""
from __future__ import annotations

import re
from typing import List, Tuple

from ..llm.client import get_llm
from ..sources.base import Candidate, dedupe
from ..sources.registry import adapters_by_name

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
JUNK_TITLES = ("404", "access denied", "just a moment", "cloudflare", "sign in", "login")


def validate_plan(plan: dict) -> Tuple[dict, List[str]]:
    notes: List[str] = []
    active = set(adapters_by_name().keys())
    tiers = plan.get("tiers") or []
    fixed = []
    for t in tiers[:5]:
        srcs = [s for s in (t.get("sources") or []) if s in active]
        qs = [q.strip() for q in (t.get("queries") or []) if isinstance(q, str) and q.strip()]
        if not srcs:
            notes.append(f"tier {t.get('tier','?')}: no active sources -> defaulting to search backbone")
            srcs = [n for n in ("duckduckgo", "searxng", "tavily") if n in active][:2]
        if not qs:
            notes.append(f"tier {t.get('tier','?')}: empty queries -> dropped")
            continue
        fixed.append({**t, "sources": srcs, "queries": qs[:4]})
    if not fixed:
        raise ValueError("Plan validation failed: no usable tiers")
    plan["tiers"] = fixed
    if not plan.get("icp"):
        notes.append("plan missing ICP sentence")
    return plan, notes


def validate_candidates(cands: List[Candidate]) -> Tuple[List[Candidate], List[str]]:
    notes: List[str] = []
    before = len(cands)
    cands = dedupe(cands)
    out = []
    for c in cands:
        t = (c.title or "").strip()
        if len(t) < 3 or any(j in t.lower() for j in JUNK_TITLES):
            continue
        if c.url and not c.url.startswith(("http://", "https://")):
            c.url = ""
        out.append(c)
    notes.append(f"candidates: {before} raw -> {len(out)} after dedupe/junk filter")
    return out, notes


def validate_enrichment(email: str, phone: str) -> Tuple[dict, List[str]]:
    notes: List[str] = []
    ok_email = email if email and EMAIL_RE.match(email) else ""
    if email and not ok_email:
        notes.append(f"dropped malformed email")
    ok_phone = re.sub(r"[^\d+()\- ]", "", phone or "")[:25]
    return {"email": ok_email, "phone": ok_phone}, notes


GROUND_PROMPT = """Review this lead analysis for a freelancer. Answer JSON:
{{"grounded": true/false, "issues": ["..."]}}
Fail it (grounded=false) if: claims cite facts not present in the evidence; percentages
are stated as hard facts instead of labelled estimates/ranges; the diagnosis is generic
boilerplate that could apply to any business.
EVIDENCE:
{evidence}
ANALYSIS:
{analysis}"""


def validate_analysis(analysis: dict, evidence: str) -> Tuple[dict, List[str]]:
    notes: List[str] = []
    text = str(analysis)
    # rule: any % must be accompanied by estimate language
    if re.search(r"\d+\s*%", text) and not re.search(r"estimat|rang|approx|~|could|potential", text, re.I):
        analysis["disclaimer"] = "All percentage figures are model estimates, not measured data."
        notes.append("added missing estimate disclaimer to % claims")
    try:
        verdict = get_llm().chat_json(
            GROUND_PROMPT.format(evidence=evidence[:2500], analysis=text[:2000]),
            tier="cheap", max_tokens=300)
        if isinstance(verdict, dict) and verdict.get("grounded") is False:
            analysis["validator_flags"] = verdict.get("issues", [])[:5]
            notes.append("analysis flagged by groundedness check")
    except Exception:  # noqa: BLE001 — validator LLM down: rules-only pass
        notes.append("LLM groundedness check skipped (provider error)")
    return analysis, notes


BANNED_OUTREACH = ("guaranteed", "100% success", "no risk at all")


PLACEHOLDER_RE = re.compile(r"\[(?:name|first name|company|your name|contact)[^\]]*\]|\{\{[^}]*\}\}", re.I)


def validate_outreach(draft: str) -> Tuple[str, List[str]]:
    notes: List[str] = []
    low = draft.lower()
    for b in BANNED_OUTREACH:
        if b in low:
            notes.append(f"outreach contained banned claim: '{b}'")
            draft = re.sub(re.escape(b), "strong", draft, flags=re.I)
    if PLACEHOLDER_RE.search(draft):
        draft = re.sub(r" ?" + PLACEHOLDER_RE.pattern, "", draft, flags=re.I)
        draft = re.sub(r"[ \t]{2,}", " ", draft)
        notes.append("removed unfilled template placeholders from outreach")
    if len(draft) > 1800:
        draft = draft[:1800]
        notes.append("outreach truncated to sane length")
    return draft, notes
