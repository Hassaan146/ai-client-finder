"""API tests: daily run limit, approve race (atomic claim), guessed-not-priority, auth."""
from __future__ import annotations

import json

import pytest
from app import main as main_module
from app.api.routes import runs as runs_module
from app.config import get_settings
from app.db.base import Base
from app.db.models import Card, Run
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

VALID_BODY = {"service": ["SEO"], "niche": ["Cafes"], "location": ["Lahore"]}


@pytest.fixture()
def client(monkeypatch, tmp_path):
    """Isolated sqlite DB + no background threads + fresh rate-limit buckets."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}",
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(runs_module, "SessionLocal", session_factory)
    monkeypatch.setattr(runs_module, "build_plan", lambda run_id: None)
    monkeypatch.setattr(runs_module, "execute_run", lambda run_id: None)
    main_module._hits.clear()  # rate limiter is module-global; reset between tests
    c = TestClient(app)  # no context manager: skip lifespan (would touch the real dev DB)
    c.db = session_factory
    yield c
    engine.dispose()


# ── daily run limit ──────────────────────────────────────────────────────────

def test_daily_run_limit_returns_429(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "USER_DAILY_RUN_LIMIT", 2)
    assert client.post("/api/runs", json=VALID_BODY).status_code == 200
    assert client.post("/api/runs", json=VALID_BODY).status_code == 200
    r = client.post("/api/runs", json=VALID_BODY)
    assert r.status_code == 429
    assert "daily run limit" in r.json()["detail"]


# ── approve race: atomic conditional update ──────────────────────────────────

def test_approve_transitions_only_once(client):
    db = client.db()
    run = Run(status="plan_ready", requirements="{}", plan="{}")
    db.add(run)
    db.commit()
    run_id = run.id
    db.close()

    first = client.post(f"/api/runs/{run_id}/approve")
    assert first.status_code == 200
    assert first.json()["status"] == "sourcing"
    second = client.post(f"/api/runs/{run_id}/approve")  # lost the race -> conflict
    assert second.status_code == 409


def test_approve_missing_run_404(client):
    assert client.post("/api/runs/99999/approve").status_code == 404


def test_approve_wrong_state_409(client):
    db = client.db()
    run = Run(status="planning", requirements="{}")
    db.add(run)
    db.commit()
    run_id = run.id
    db.close()
    assert client.post(f"/api/runs/{run_id}/approve").status_code == 409


# ── priority: guessed emails must not be "contact first" ────────────────────

def _card(run_id: int, email_status: str, fit: float = 9.0) -> Card:
    return Card(run_id=run_id, title="Acme", email="jane@acme.com",
                email_status=email_status, fit_score=fit)


@pytest.mark.parametrize(("status", "priority"), [
    ("valid", True), ("risky", True),
    ("guessed", False), ("unverified", False), ("invalid", False),
])
def test_priority_excludes_guessed(client, status, priority):
    db = client.db()
    run = Run(status="done", requirements="{}")
    db.add(run)
    db.commit()
    db.add(_card(run.id, status))
    db.commit()
    run_id = run.id
    db.close()

    d = client.get(f"/api/runs/{run_id}").json()
    assert d["cards"][0]["priority"] is priority


def test_priority_needs_high_fit(client):
    db = client.db()
    run = Run(status="done", requirements="{}")
    db.add(run)
    db.commit()
    db.add(_card(run.id, "valid", fit=5.0))  # below PRIORITY_MIN_FIT
    db.commit()
    run_id = run.id
    db.close()
    d = client.get(f"/api/runs/{run_id}").json()
    assert d["cards"][0]["priority"] is False


# ── optional shared-token auth ───────────────────────────────────────────────

def test_api_token_enforced_when_set(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "API_TOKEN", "s3cret")
    assert client.post("/api/runs", json=VALID_BODY).status_code == 401
    ok = client.post("/api/runs", json=VALID_BODY,
                     headers={"Authorization": "Bearer s3cret"})
    assert ok.status_code == 200
    run_id = ok.json()["id"]
    # GET stays open (read-only), approve requires the token
    assert client.get(f"/api/runs/{run_id}").status_code == 200
    assert client.post(f"/api/runs/{run_id}/approve").status_code == 401
    assert client.post(f"/api/runs/{run_id}/approve",
                       headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_created_run_persists_requirements(client):
    r = client.post("/api/runs", json=VALID_BODY)
    assert r.status_code == 200
    db = client.db()
    run = db.get(Run, r.json()["id"])
    assert json.loads(run.requirements)["service"] == ["SEO"]
    db.close()
