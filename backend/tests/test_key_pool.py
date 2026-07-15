"""Tests for LLM key-pool rotation/failover + small pure helpers."""
from __future__ import annotations

import pytest

from app.core.contacts import _domain, guess_email
from app.llm.client import extract_json
from app.llm.key_pool import KeyPool, PoolRegistry
from app.sources.base import Candidate, dedupe


# ── KeyPool ─────────────────────────────────────────────────────────────────

def test_empty_pool_is_falsy_and_acquires_none():
    pool = KeyPool("xai")
    assert not pool
    assert len(pool) == 0
    assert pool.acquire() is None


def test_round_robin_rotation():
    pool = KeyPool.from_list("xai", ["k1", "k2", "k3"])
    assert [pool.acquire() for _ in range(4)] == ["k1", "k2", "k3", "k1"]


def test_failed_key_is_benched_then_skipped():
    pool = KeyPool.from_list("xai", ["bad", "good"])
    assert pool.acquire() == "bad"
    pool.report("bad", ok=False, cooldown=60)
    # bad is cooling down -> only good comes back
    assert pool.acquire() == "good"
    assert pool.acquire() == "good"


def test_all_benched_returns_none():
    pool = KeyPool.from_list("xai", ["k1"])
    pool.report("k1", ok=False)
    assert pool.acquire() is None


def test_success_resets_fail_count():
    pool = KeyPool.from_list("xai", ["k1"])
    pool.report("k1", ok=False, cooldown=0)  # fails=1, no bench
    pool.report("k1", ok=True)
    assert pool._keys[0].fails == 0


def test_registry_available_providers():
    reg = PoolRegistry({"xai": ["k"], "groq": []})
    assert reg.available_providers() == ["xai"]
    assert reg.get("missing").acquire() is None


# ── extract_json (tolerant parser for open models) ──────────────────────────

def test_extract_json_plain():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_wrapped_in_prose():
    assert extract_json('Sure! Here is the data: [{"i": 0}] hope it helps') == [{"i": 0}]


def test_extract_json_trailing_comma():
    assert extract_json('{"a": 1, "b": [1, 2,],}') == {"a": 1, "b": [1, 2]}


def test_extract_json_garbage_raises():
    with pytest.raises(Exception):
        extract_json("no json here at all")


# ── source adapter error reporting ──────────────────────────────────────────

def test_adapter_records_last_error_and_returns_empty():
    from app.sources.base import SourceAdapter

    class Boom(SourceAdapter):
        name = "boom"

        def _search(self, query, *, location, limit):
            raise ValueError("bad payload")

    a = Boom()
    assert a.search("x") == []
    assert a.last_error == "ValueError"


def test_outreach_placeholders_stripped():
    from app.agents.validators import validate_outreach
    msg, notes = validate_outreach("Hi [Name], I saw {{company}} is growing.")
    assert "[Name]" not in msg and "{{company}}" not in msg
    assert any("placeholder" in n for n in notes)


# ── contacts helpers ────────────────────────────────────────────────────────

def test_domain_strips_www_prefix_only():
    assert _domain("https://www.example.com/x") == "example.com"
    # must not eat leading letters that happen to be w/. (old lstrip bug)
    assert _domain("https://web.com") == "web.com"
    assert _domain("https://w3.org/spec") == "w3.org"


def test_guess_email():
    assert guess_email("Jane Doe", "acme.com") == "jane.doe@acme.com"
    assert guess_email("Cher", "acme.com") == "cher@acme.com"
    assert guess_email("", "acme.com") == ""
    assert guess_email("Jane", "") == ""


# ── candidate dedupe ────────────────────────────────────────────────────────

def test_dedupe_by_url_then_title():
    cands = [Candidate(title="A", url="https://x.com/"),
             Candidate(title="B", url="https://x.com"),   # same url modulo slash
             Candidate(title="A"),                        # no url -> title key
             Candidate(title="a")]                        # case-insensitive dup
    out = dedupe(cands)
    assert len(out) == 2
