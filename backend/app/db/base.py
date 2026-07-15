"""SQLAlchemy engine/session (SQLite dev default; Postgres via DATABASE_URL)."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from ..config import get_settings

engine = create_engine(get_settings().DATABASE_URL,
                       connect_args={"check_same_thread": False}
                       if get_settings().DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from . import models  # noqa: F401 — register tables
    Base.metadata.create_all(engine)
