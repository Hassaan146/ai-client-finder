"""Closer: draft genre-tagged outreach for one analyzed lead."""
from __future__ import annotations

from ..llm.client import get_llm

SYSTEM = """You write short, sharp cold outreach for a freelancer. Pick the best genre:
problem-first | trigger-event | question | value-first | social-proof.
Rules:
- 90-140 words, plain text, short paragraphs. No generic flattery, no buzzwords.
- Open with something specific to THIS lead (a fact from the diagnosis), never
  "I hope this finds you well" or "I came across your company".
- Address the person by first name if known; otherwise write naturally WITHOUT any
  placeholder — never output brackets like [Name] or {{company}}.
- Percentages stay labelled as estimates. Never promise guaranteed results.
- Subject (email only): max 7 words, concrete, no clickbait, no ALL CAPS.
- End with ONE low-friction CTA (a question or a 15-min call), then for email a
  one-line opt-out: "If this isn't relevant, tell me and I won't follow up."."""

PROMPT = """Service: {service}
Lead: {title}
Contact person/role: {person} {role}
Diagnosis: {analysis}

JSON: {{"genre": "...", "why_this_genre": "1 sentence", "channel": "email|dm|comment",
        "subject": "for email, else empty", "message": "the outreach text"}}"""


def draft_outreach(title: str, analysis: dict, enrichment: dict, service: str) -> dict:
    out = get_llm().chat_json(
        PROMPT.format(service=service, title=title,
                      person=enrichment.get("person", ""), role=enrichment.get("role", ""),
                      analysis=str(analysis)[:900]),
        system=SYSTEM, tier="big", max_tokens=500)
    return out if isinstance(out, dict) else {"genre": "problem-first", "why_this_genre": "",
                                              "channel": "email", "subject": "", "message": str(out)[:800]}
