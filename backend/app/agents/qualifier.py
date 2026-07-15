"""Qualifier: score fit vs requirements 0-10 -> ranking + cut low-fit before expensive analysis."""
from __future__ import annotations

from ..config import get_settings
from ..core.text import join_str
from ..llm.client import get_llm
from ..sources.base import Candidate

BATCH_PROMPT = """Freelancer requirements:
service: {service} | niche: {niche} | location: {location} | ICP: {icp}

Score each lead 0-10 for fit (10 = ideal paying client for this service).
Consider: real business/person with a need, budget likelihood, match to service, intent strength.
Leads:
{leads}

JSON only: [{{"i": 0, "score": 7, "reason": "one short sentence"}}, ...]"""


def qualify(cands: list[Candidate], requirements: dict, icp: str,
            keep: int) -> list[tuple[Candidate, float, str]]:
    """Returns [(candidate, score, reason)] sorted best-first, trimmed to `keep`."""
    if not cands:
        return []
    s = get_settings()
    scored: list[tuple[Candidate, float, str]] = []
    batch_size = s.QUALIFIER_BATCH_SIZE
    for start in range(0, min(len(cands), s.QUALIFIER_MAX_CANDIDATES), batch_size):
        batch = cands[start:start + batch_size]
        lead_lines = "\n".join(
            f"{i}. [{c.source}/{c.kind}] {c.title} — {c.snippet[:120]}" for i, c in enumerate(batch))
        try:
            rows = get_llm().chat_json(
                BATCH_PROMPT.format(service=join_str(requirements.get("service", "")),
                                    niche=join_str(requirements.get("niche", "")),
                                    location=join_str(requirements.get("location", "")),
                                    icp=icp, leads=lead_lines),
                tier="cheap", max_tokens=1000)
            for r in rows if isinstance(rows, list) else []:
                i = int(r.get("i", -1))
                if 0 <= i < len(batch):
                    scored.append((batch[i], float(r.get("score", 0)), str(r.get("reason", ""))[:200]))
        except Exception:
            scored.extend((c, 5.0, "unscored (LLM error)") for c in batch)
    scored.sort(key=lambda t: t[1], reverse=True)
    return [t for t in scored if t[1] >= s.QUALIFIER_MIN_FIT][:keep] or scored[:keep]
