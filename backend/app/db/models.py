"""ORM models: Run (one pipeline execution) + Card (one ranked flash card)."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="planning", index=True)
    # planning -> plan_ready -> sourcing -> ranking -> diagnosing -> done | failed
    requirements: Mapped[str] = mapped_column(Text, default="{}")   # json
    plan: Mapped[str] = mapped_column(Text, default="")             # json
    gcf: Mapped[str] = mapped_column(Text, default="")              # json graph snapshot
    log: Mapped[str] = mapped_column(Text, default="[]")            # json list[str]
    error: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Card(Base):
    __tablename__ = "cards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(500), default="")
    source: Mapped[str] = mapped_column(String(40), default="")
    tier: Mapped[str] = mapped_column(String(2), default="")
    kind: Mapped[str] = mapped_column(String(20), default="company")
    fit_score: Mapped[float] = mapped_column(Float, default=0)      # ranking key
    fit_reason: Mapped[str] = mapped_column(String(250), default="")
    company: Mapped[str] = mapped_column(String(200), default="")
    email: Mapped[str] = mapped_column(String(200), default="")
    # valid | risky | invalid | guessed | unverified
    email_status: Mapped[str] = mapped_column(String(16), default="unverified")
    phone: Mapped[str] = mapped_column(String(50), default="")
    socials: Mapped[str] = mapped_column(Text, default="[]")   # json list
    person: Mapped[str] = mapped_column(String(120), default="")
    role: Mapped[str] = mapped_column(String(120), default="")
    analysis: Mapped[str] = mapped_column(Text, default="{}")   # json (requirement/problems/solutions)
    outreach: Mapped[str] = mapped_column(Text, default="{}")       # json (genre/channel/subject/message)
    validator_notes: Mapped[str] = mapped_column(Text, default="[]")
