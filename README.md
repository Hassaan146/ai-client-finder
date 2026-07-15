# AI Client/Lead Finder

Niche-agnostic AI agent that **finds a business → diagnoses its problems → maps solutions with %-impact → drafts the outreach**, delivered as flash cards. For solo freelancers/agencies.

Docs: [PLAN.md](PLAN.md) (product) · [plans.md](plans.md) (build order) · [WORKFLOW.md](WORKFLOW.md) (source engine) · [SOURCES.md](SOURCES.md) (free catalog) · [API_KEYS.md](API_KEYS.md) (keys) · [prompts.md](prompts.md) (log).
Security standard: `vibe-coding-rules` v2.0 (31 areas).

## Where things are
```
ai-client-finder/
├─ .env.example            # ALL source/LLM placeholders (multi-key pools). Copy -> .env
├─ API_KEYS.md             # where/how to get each free key
├─ backend/
│  ├─ requirements.txt
│  ├─ scripts/
│  │  ├─ validate_keys.py  # Phase 0b: test every key (stdlib, run first)
│  │  └─ seed_sources.py   # seed the Source Registry
│  └─ app/
│     ├─ config.py         # env loader (parses LLM key pools)
│     ├─ main.py           # FastAPI entry
│     ├─ core/             # security (SSRF/injection), rate_limit, errors, logging
│     ├─ llm/              # router + key_pool (multi-key failover) + providers
│     ├─ sources/          # base + registry + tiers + adapters/ (A–H)
│     ├─ agents/           # orchestrator, planner, scout, validators, analyst, closer
│     ├─ pipeline/         # gcf (Graph Context Form) + run_pipeline
│     ├─ db/               # models, schemas, crud
│     └─ api/routes/       # health, runs, sources
└─ frontend/               # later (basic -> pro)
```

## Phase 0/1 — validate keys (do this now)
1. `cp .env.example .env`
2. Paste your free keys (see [API_KEYS.md](API_KEYS.md)). LLM vars are **comma-separated pools** — add 2–3 keys each so runs never break.
3. Validate: `python backend/scripts/validate_keys.py` → OK/FAIL + quota per key, empties skipped.
4. When your CORE keys pass → **Phase 1 done** → backend → orchestration/agents.

## Source tiers (8: A–H)
A search backbone · B jobs/freelance · C local/maps · D company intel · E social/intent · F tenders/gov · G trigger signals · H contact/email. No-key sources (DuckDuckGo, HN, Overpass, WHOIS…) are engine-handled — no placeholder needed.
