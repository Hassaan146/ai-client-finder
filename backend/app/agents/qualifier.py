"""Qualifier: score fit vs requirements 0-10 -> ranking + cut low-fit before expensive analysis."""
from __future__ import annotations

from typing import List

from ..llm.client import get_llm
from ..sources.base import Candidate

BATCH_PROMPT = """Freelancer requirements:
service: {service} | niche: {niche} | location: {location} | ICP: {icp}

Score each lead 0-10 for fit (10 = ideal paying client for this service).
Consider: real business/person with a need, budget likelihood, match to service, intent strength.
Leads:
{leads}

JSON only: [{{"i": 0, "score": 7, "reason": "one short sentence"}}, ...]"""


def qualify(cands: List[Candidate], requirements: dict, icp: str,
            keep: int) -> List[tuple[Candidate, float, str]]:
    """Returns [(candidate, score, reason)] sorted best-first, trimmed to `keep`."""
    if not cands:
        return []
    scored: List[tuple[Candidate, float, str]] = []
    B = 20
    for start in range(0, min(len(cands), 100), B):
        batch = cands[start:start + B]
        lead_lines = "\n".join(
            f"{i}. [{c.source}/{c.kind}] {c.title} — {c.snippet[:120]}" for i, c in enumerate(batch))
        try:
            rows = get_llm().chat_json(
                BATCH_PROMPT.format(service=requirements.get("service", ""),
                                    niche=requirements.get("niche", ""),
                                    location=requirements.get("location", ""),
                                    icp=icp, leads=lead_lines),
                tier="cheap", max_tokens=1000)
            for r in rows if isinstance(rows, list) else []:
                i = int(r.get("i", -1))
                if 0 <= i < len(batch):
                    scored.append((batch[i], float(r.get("score", 0)), str(r.get("reason", ""))[:200]))
        except Exception:  # noqa: BLE001 — scoring fallback: neutral score, keep pipeline alive
            scored.extend((c, 5.0, "unscored (LLM error)") for c in batch)
    scored.sort(key=lambda t: t[1], reverse=True)
    return [t for t in scored if t[1] >= 4.0][:keep] or scored[:keep]
