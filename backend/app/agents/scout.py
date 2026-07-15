"""Scout: run the plan's queries across ALL selected sources in parallel.

Every query is dispatched to every selected source (spread coverage). Local
adapters (maps) are run once per chosen location; search adapters carry the
location inside the planner's queries.
"""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, List

from ..sources.base import Candidate
from ..sources.registry import adapters_by_name

MAX_WORKERS = 10
PER_QUERY_LIMIT = 8
MAX_QUERIES_PER_SOURCE = 6
LOCAL_ADAPTERS = {"overpass", "yelp"}   # need a structured location arg


def _plan_queries(plan: dict) -> List[str]:
    seen, out = set(), []
    for tier in plan.get("tiers", []):
        for q in tier.get("queries", []):
            q = (q or "").strip()
            if q and q.lower() not in seen:
                seen.add(q.lower())
                out.append(q)
    return out


def run_scout(plan: dict, locations: Iterable[str] | str | None = None,
              source_names: Iterable[str] | None = None) -> tuple[List[Candidate], dict, dict]:
    """locations: list of cities (local adapters loop over them). source_names: explicit adapters.
    Returns (candidates, per-source result counts incl. zeros, per-source errors)."""
    if isinstance(locations, str):
        locations = [locations] if locations else []
    locs = [l for l in (locations or []) if l][:3]

    available = adapters_by_name()
    chosen = ({n: available[n] for n in source_names if n in available}
              if source_names else dict(available)) or dict(available)

    queries = _plan_queries(plan) or [""]
    jobs = []  # (adapter, query, location)
    for name, a in chosen.items():
        qs = queries[:MAX_QUERIES_PER_SOURCE]
        if name in LOCAL_ADAPTERS and locs:
            for q in qs[:3]:
                for loc in locs:
                    jobs.append((a, q, loc))
        else:
            for q in qs:
                jobs.append((a, q, ""))

    out: List[Candidate] = []
    per_source: Counter = Counter({name: 0 for name in chosen})  # zeros visible too
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(a.search, q, location=loc, limit=PER_QUERY_LIMIT): a.name
                for a, q, loc in jobs}
        for f in as_completed(futs):
            try:
                res = f.result()
                out.extend(res)
                per_source[futs[f]] += len(res)
            except Exception:  # noqa: BLE001
                pass
    errors = {name: a.last_error for name, a in chosen.items()
              if per_source[name] == 0 and a.last_error}
    return out, dict(per_source), errors
