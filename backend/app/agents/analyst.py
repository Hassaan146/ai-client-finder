"""Analyst: diagnose problems -> map solutions with honest %-impact ranges (the wedge)."""
from __future__ import annotations

from ..llm.client import get_llm
from ..sources.base import Candidate

SYSTEM = """You are a sharp business analyst helping a freelancer pitch. You diagnose a
prospect's likely problems from EVIDENCE ONLY and map the freelancer's service to them.
Percentages must be honest labelled estimates/ranges ("est. 10-20%"), never invented facts.
If evidence is thin, say so — a smaller honest card beats a fabricated one."""

PROMPT = """Freelancer service: {service}
Lead evidence:
- title: {title}
- source: {source} ({kind})
- snippet: {snippet}
- enrichment: {enrichment}

Produce JSON:
{{
 "requirement": "what this lead most likely needs (1 sentence)",
 "analyzer": "what the client wants, in their words (1-2 sentences)",
 "problems": [{{"problem": "...", "evidence": "which fact above supports this"}}],
 "solutions": [{{"solution": "...", "maps_to_problem": 0,
                 "impact": "est. X-Y% improvement in <metric> (estimate)",
                 "why_it_matters": "stakeholder value, 1 sentence"}}],
 "confidence": "high|medium|low"
}}
Max 3 problems, max 3 solutions. Evidence-grounded only."""


def analyze(cand: Candidate, enrichment: dict, service: str) -> dict:
    out = get_llm().chat_json(
        PROMPT.format(service=service, title=cand.title, source=cand.source,
                      kind=cand.kind, snippet=cand.snippet[:400],
                      enrichment=str(enrichment)[:600]),
        system=SYSTEM, tier="big", max_tokens=900)
    return out if isinstance(out, dict) else {"requirement": "", "analyzer": "",
                                              "problems": [], "solutions": [],
                                              "confidence": "low"}
