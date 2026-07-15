"""Planner: user requirements (multi service/niche/location) -> business-discovery plan."""
from __future__ import annotations

from ..llm.client import get_llm

LEAD_TYPE_GUIDE = {
    "local_business": "specific local businesses (directories, maps, 'best X in <city>')",
    "companies_web":  "company websites in the niche ('<niche> companies', 'top <niche>', directories)",
    "job_posts":      "businesses actively hiring/needing help ('<niche> hiring', 'looking for <service>')",
    "community_intent": "owners asking for help ('need a <service>', reddit/forum threads)",
    "news_signals":   "recently funded / launched / expanding companies in the niche",
}

SYSTEM = """You are the Planner for a freelancer's lead engine. GOAL: find real
BUSINESSES to pitch — companies with a likely problem the freelancer's service solves —
NOT job adverts (unless job_posts requested). Write concrete web-search queries that
surface businesses. Cover EVERY niche and EVERY location given (combine them)."""

PROMPT = """Freelancer sells (one or more): {services}
Target business types (niches): {niches}
Locations: {locations}
Extra notes: {notes}
Lead types requested: {lead_types_desc}
Leads wanted: {max_leads}

Return JSON:
{{
 "icp":"one-sentence ideal client",
 "tiers":[{{"tier":"A","goal":"...","queries":["6-10 word business-finding query","..."]}}],
 "ranking_criteria":["3 short criteria to rank found businesses"]
}}
Rules:
- Generate queries covering each niche x location combination (e.g. "dental clinics in Dubai",
  "top dental clinics London"). 3-6 tiers, 2-4 queries each, 10-18 queries total.
- Queries must find BUSINESSES to pitch, not job posts (unless job_posts requested).
- Bake each location into its queries."""


def _as_list(v) -> list[str]:
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [str(v).strip()] if str(v).strip() else []


def make_plan(requirements: dict) -> dict:
    services = _as_list(requirements.get("service"))
    niches = _as_list(requirements.get("niche"))
    locations = _as_list(requirements.get("location"))
    lead_types = requirements.get("lead_types") or ["companies_web", "local_business"]
    desc = "; ".join(f"{t} = {LEAD_TYPE_GUIDE.get(t, t)}" for t in lead_types)

    plan = get_llm().chat_json(
        PROMPT.format(services=", ".join(services) or "(unspecified)",
                      niches=", ".join(niches) or "(unspecified)",
                      locations=", ".join(locations) or "(no location — broad/global)",
                      notes=requirements.get("notes", "") or "-",
                      lead_types_desc=desc,
                      max_leads=requirements.get("max_leads", 10)),
        system=SYSTEM, tier="big", max_tokens=1400)
    if isinstance(plan, list):
        plan = {"icp": "", "tiers": plan, "ranking_criteria": []}

    if not any(t.get("queries") for t in plan.get("tiers", [])):
        base = []
        for n in (niches or ["businesses"]):
            for loc in (locations or [""]):
                base += [f"{n} in {loc}".strip(), f"top {n} {loc}".strip(), f"{n} companies directory"]
        plan["tiers"] = [{"tier": "A", "goal": "business discovery", "queries": base[:18]}]
    return plan
