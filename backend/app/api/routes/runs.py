"""Run endpoints: create (-> plan), approve (-> execute), poll status + ranked cards."""
from __future__ import annotations

import json
import threading
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from ...config import get_settings
from ...core.text import as_list
from ...db.base import SessionLocal
from ...db.models import Card, Run
from ...pipeline.run_pipeline import build_plan, execute_run
from ..deps import require_api_token

router = APIRouter(prefix="/api/runs", tags=["runs"])


LEAD_TYPES = {"local_business", "companies_web", "job_posts", "community_intent", "news_signals"}


def _req_list(v):
    return as_list(v, max_items=12, max_chars=120)


class RequirementsIn(BaseModel):
    """Server-side validation (vibe 3). service/niche/location accept multiple values."""
    service: list[str]
    niche: list[str]
    location: list[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=500)
    max_leads: int = Field(default=10, ge=3, le=25)
    lead_types: list[str] = Field(default_factory=lambda: ["companies_web", "local_business"])
    sources: list[str] = Field(default_factory=list)

    @field_validator("service", "niche", mode="before")
    @classmethod
    def _req_multi(cls, v):
        v = _req_list(v)
        if not v:
            raise ValueError("select or type at least one value")
        return v

    @field_validator("location", mode="before")
    @classmethod
    def _opt_multi(cls, v):
        return _req_list(v)

    @field_validator("lead_types")
    @classmethod
    def _clean_types(cls, v):
        return [t for t in v if t in LEAD_TYPES] or ["companies_web", "local_business"]

    @field_validator("sources")
    @classmethod
    def _clean_sources(cls, v):
        return v[:20]


@router.post("", dependencies=[Depends(require_api_token)])
def create_run(req: RequirementsIn):
    db = SessionLocal()
    try:
        # daily free-tier cap: count runs created since UTC midnight
        limit = get_settings().USER_DAILY_RUN_LIMIT
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        used = db.query(Run).filter(Run.created_at >= today_start).count()
        if used >= limit:
            raise HTTPException(429, f"daily run limit reached ({limit}/day) — try again tomorrow")
        run = Run(status="planning", requirements=req.model_dump_json())
        db.add(run)
        db.commit()
        threading.Thread(target=build_plan, args=(run.id,), daemon=True).start()
        return {"id": run.id, "status": run.status}
    finally:
        db.close()


@router.post("/{run_id}/approve", dependencies=[Depends(require_api_token)])
def approve_run(run_id: int):
    db = SessionLocal()
    try:
        # atomic conditional update: only ONE approve can win the plan_ready -> sourcing
        # transition, so execute_run can never be spawned twice for the same run.
        claimed = (db.query(Run)
                   .filter(Run.id == run_id, Run.status == "plan_ready")
                   .update({"status": "sourcing"}, synchronize_session=False))
        db.commit()
        if claimed != 1:
            run = db.get(Run, run_id)
            if not run:
                raise HTTPException(404, "run not found")
            raise HTTPException(409, f"run is '{run.status}', not awaiting approval")
        threading.Thread(target=execute_run, args=(run_id,), daemon=True).start()
        return {"id": run_id, "status": "sourcing"}
    finally:
        db.close()


@router.get("/{run_id}")
def get_run(run_id: int):
    priority_min_fit = get_settings().PRIORITY_MIN_FIT
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        if not run:
            raise HTTPException(404, "run not found")
        cards = (db.query(Card).filter(Card.run_id == run_id)
                 .order_by(Card.fit_score.desc()).all())          # ranked best-first
        return {
            "id": run.id, "status": run.status, "error": run.error,
            "plan": json.loads(run.plan) if run.plan else None,
            "log": json.loads(run.log or "[]"),
            "cards": [{
                "rank": i + 1, "title": c.title, "url": c.url, "source": c.source,
                "tier": c.tier, "kind": c.kind, "fit_score": c.fit_score,
                "fit_reason": c.fit_reason, "company": c.company, "email": c.email,
                "email_status": c.email_status, "phone": c.phone,
                "socials": json.loads(c.socials or "[]"),
                "person": c.person, "role": c.role,
                # "contact first": strong fit AND a deliverable email (guessed ones stay normal)
                "priority": bool(c.fit_score >= priority_min_fit and c.email
                                 and c.email_status in ("valid", "risky")),
                "analysis": json.loads(c.analysis or "{}"),
                "outreach": json.loads(c.outreach or "{}"),
                "validator_notes": json.loads(c.validator_notes or "[]"),
            } for i, c in enumerate(cards)],
        }
    finally:
        db.close()
