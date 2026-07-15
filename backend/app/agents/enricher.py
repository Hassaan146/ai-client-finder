"""Enricher: identify the company + decision-maker + a VERIFIED contact to reach.

Contact waterfall (core/contacts): scrape contact pages -> pattern-guess ->
verify via Reoon/MillionVerifier. LLM adds company/person/role/context.
"""
from __future__ import annotations

import re

from ..config import get_settings
from ..core.contacts import best_contact
from ..core.security import safe_fetch_text, wrap_untrusted
from ..llm.client import get_llm
from ..sources.base import Candidate

EXTRACT_PROMPT = """{page}

From the page data above, extract as JSON (empty string if unknown, never invent):
{{"company":"", "person":"decision-maker name if shown", "role":"their title",
  "what_they_do":"one sentence", "signals":["notable facts, tech used, gaps, weaknesses"]}}"""


def enrich(cand: Candidate) -> dict:
    """Best-effort, never raises. Returns company/person/role/context + verified contact."""
    result = {"company": cand.extra.get("company", "") or cand.title, "person": "", "role": "",
              "what_they_do": cand.snippet[:150], "signals": [],
              "email": "", "email_status": "unverified", "phone": "", "socials": []}

    # 1) LLM context from the page (also gives us a person name for pattern-guessing)
    page_text = ""
    if cand.url:
        try:
            html = safe_fetch_text(cand.url, get_settings().NOMINATIM_USER_AGENT)
            page_text = re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", " ",
                                                       html, flags=re.S | re.I))
            page_text = re.sub(r"\s+", " ", page_text)[:6000]
            data = get_llm().chat_json(EXTRACT_PROMPT.format(page=wrap_untrusted(page_text, cand.url)),
                                       tier="cheap", max_tokens=400)
            if isinstance(data, dict):
                for k in ("company", "person", "role", "what_they_do"):
                    if data.get(k):
                        result[k] = data[k]
                if isinstance(data.get("signals"), list):
                    result["signals"] = data["signals"][:6]
        except Exception:  # noqa: BLE001 — page fetch/LLM failed; contact waterfall still runs
            pass

    # 2) contact waterfall (scrape contact pages + guess + verify)
    contact = best_contact(cand.url, result["person"], cand.contact_hint)
    result.update({k: contact[k] for k in ("email", "email_status", "phone")})
    result["socials"] = contact["socials"]
    return result
