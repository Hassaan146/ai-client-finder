"""Run endpoints: create (-> plan), approve (-> execute), poll status + ranked cards."""
from __future__ import annotations

import json
import threading

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from ...db.base import SessionLocal
from ...db.models import Card, Run
from ...pipeline.run_pipeline import build_plan, execute_run

router = APIRouter(prefix="/api/runs", tags=["runs"])


LEAD_TYPES = {"local_business", "companies_web", "job_posts", "community_intent", "news_signals"}


def _as_list(v):
    if isinstance(v, list):
        return [str(x).strip()[:120] for x in v if str(x).strip()][:12]
    return [str(v).strip()[:120]] if str(v).strip() else []


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
        v = _as_list(v)
        if not v:
            raise ValueError("select or type at least one value")
        return v

    @field_validator("location", mode="before")
    @classmethod
    def _opt_multi(cls, v):
        return _as_list(v)

    @field_validator("lead_types")
    @classmethod
    def _clean_types(cls, v):
        return [t for t in v if t in LEAD_TYPES] or ["companies_web", "local_business"]

    @field_validator("sources")
    @classmethod
    def _clean_sources(cls, v):
        return v[:20]


@router.post("")
def create_run(req: RequirementsIn):
    db = SessionLocal()
    try:
        run = Run(status="planning", requirements=req.model_dump_json())
        db.add(run)
        db.commit()
        threading.Thread(target=build_plan, args=(run.id,), daemon=True).start()
        return {"id": run.id, "status": run.status}
    finally:
        db.close()


@router.post("/{run_id}/approve")
def approve_run(run_id: int):
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        if not run:
            raise HTTPException(404, "run not found")
        if run.status != "plan_ready":
            raise HTTPException(409, f"run is '{run.status}', not awaiting approval")
        run.status = "sourcing"
        db.commit()
        threading.Thread(target=execute_run, args=(run_id,), daemon=True).start()
        return {"id": run_id, "status": "sourcing"}
    finally:
        db.close()


@router.get("/{run_id}")
def get_run(run_id: int):
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
                # "contact first": strong fit AND a usable, non-invalid email
                "priority": bool(c.fit_score >= 7 and c.email and c.email_status in ("valid", "risky", "guessed")),
                "analysis": json.loads(c.analysis or "{}"),
                "outreach": json.loads(c.outreach or "{}"),
                "validator_notes": json.loads(c.validator_notes or "[]"),
            } for i, c in enumerate(cards)],
        }
    finally:
        db.close()
