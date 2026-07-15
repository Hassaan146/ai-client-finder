# Build Plan — AI Client/Lead Finder

Date: 2026-07-01 · Status: build starting · Team: Hassaan + partner (working together, not split)
Companion docs: [PLAN.md](PLAN.md) (product) · [WORKFLOW.md](WORKFLOW.md) (source engine) · [SOURCES.md](SOURCES.md) (free catalog) · [prompts.md](prompts.md) (prompt log)
Security standard: `vibe-coding-rules` v2.0 (31 areas) applied throughout.

---

## Locked build order (user's workflow + accepted recommendations)

### Phase 0a — Validate sources  🔒 (user-locked, first)
- Confirm every **free** source actually works (responds, is free, rate limits).
- **Output = Source Registry** (structured data, seeds the DB): `{name, category(lead|company|contact|signal), access(api|feed|search|scrape|self-host), endpoint, needs_key, free, rate_limit, health, region, niches[]}`.
- Not a doc — reusable data the orchestrator reads.

### Phase 0b — Validate API keys  🔒 (user-locked, second)
- Get free keys, test each: lives? quota left?
- **Deliverable = key-test harness:** one script that pings every provider, prints ✅/❌ + remaining quota. Reusable forever (re-run when a key dies). Covers Grok (xAI), Nvidia NIM, SearXNG, Reddit, OpenCorporates, etc.

### Phase 0c — Thin vertical slice  ⭐ (recommended, de-risks everything)
- Wire **1 source → 1 LLM call → 1 flash card**, end-to-end, ugly, no orchestrator.
- Goal: prove the whole pipe + prove the diagnosis is send-worthy *before* building 6 agents on assumptions.

### Phase 1 — Orchestrator platform (shell)
- The coordinator that owns a Run and sequences agents.

### Phase 2 — Planner agent + plan-approval gate
- Planner runs the **4–5 tier meta-search plan** → shows **combined plan report to user** (with **estimated cost + quota use per tier** — added rec) → user approves before execution.

### Phase 3 — GCF (Graph Context Form)
- Approved plan → serialized into a **graph context** shared across agents (see design below).

### Phase 4 — Additional agents
- Scout (pool) · Validator-1 (data) · Enricher · Qualifier · Analyst · Validator-2 (quality) · Closer. (User to finalize exact set.)

### Phase 5 — Backend + full workflow wiring
- API/services layered on the registry + orchestrator. FastAPI, model-agnostic LLM router (LiteLLM over Grok/Nvidia).

### Phase 6 — Database
- Postgres. NOTE: minimal DB already seeded in Phase 0a (registry). This phase = full schema (runs, candidates, cards, users, quota).

### Phase 7 — Basic frontend (test harness)
- Minimal UI to exercise every path. Not pretty — functional.

### Phase 8 — Professional frontend
- After everything tested → polished / 3D live frontend.

---

## GCF — Graph Context Form (design)
Shared context between agents represented as a **graph**, not passed-around text.

- **Nodes (typed):** `Run`, `SourcePlan`, `SearchTier`, `Source`, `Candidate`, `Company`, `Problem`, `Solution`, `Contact`, `OutreachDraft`, `Card`.
- **Edges (relations):** `Run→SourcePlan`, `SourcePlan→SearchTier→Source`, `Source→Candidate`, `Candidate→Company`, `Company→Problem`, `Problem→Solution`, `Company→Contact`, `Card→(Company,Solution,Contact,OutreachDraft)`.
- **Why it saves tokens:** each agent reads/writes only its **subgraph** and passes **node IDs/references**, not full payloads. Serialize the minimal subgraph an agent needs, with a compact node schema.
- **Store:** graph held on a blackboard (Redis/DB or in-memory per run); persisted to Postgres for the Run record.
- **Flow:** Planner builds the plan subgraph → user approves → Scout appends Candidate nodes → Validators/Enricher/Analyst enrich the graph → Closer attaches OutreachDraft → Card node assembled for the UI.

---

## Recommendations folded in (steps 0a/0b unchanged)
1. Source validation outputs structured **Registry** data (Phase 0a).
2. Reusable **key-test harness** (Phase 0b).
3. **Thin vertical slice** before full orchestrator (Phase 0c). ← biggest de-risk.
4. Plan-approval report shows **cost + quota estimate** (Phase 2).
5. **Cost/quota meter** from day 1 (free-tier safety).
6. **Validators** stay inside the orchestrator (open models hallucinate).
7. DB seed starts at Phase 0a; "backend" = services on top.

---

## Open items (need decisions as we go)
- Final agent roster + count (user to specify in Phase 4).
- First niche + city/region for Phase 0c slice.
- Which cheap + which big model from Grok/Nvidia for the router.
- GCF store: Redis vs in-process for v1 (lean: in-process first).
