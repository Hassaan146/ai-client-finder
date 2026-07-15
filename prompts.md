# Prompts Log — AI Client/Lead Finder

Running log of every prompt/requirement the user gives for this project.
Append-only. Newest at bottom. Each entry: ID, date, raw intent, distilled meaning, status.

Conventions:
- Status: `idea` → `planned` → `building` → `done`
- Keep the user's raw words AND a cleaned one-line distillation.

---

## P-001 — 2026-06-30 — Project genesis + scope
**Status:** planned

**Raw intent (user):**
> Started thinking about earning via freelancing (Fiverr/Upwork). Making gigs was slow.
> Wanted to "kill the real problem": **finding clients & leads**.
> Idea: an AI client/lead-finding agent. Find clients who can pay for projects in **any niche** (not hardcoded to AI/automation only — that limits the achievement).
> Return each lead as a **flash card**:
> - the requirement
> - the mapping
> - client name
> - client company + details, email, etc.
> - short **analyzer**: what the client wants
> - **solution**: how we solve their problem(s) + why it matters to the client and all stakeholders, in **% impact terms** (e.g. "WhatsApp automation → +15–20% of the 30% of sales done via WhatsApp marketing"). Percentages persuade.
> Sourcing: agent searches companies on **Google Maps**, analyzes the whole company (what it does, where its sales/operations come from, where it's weak), surfaces **problems we can solve** + solutions for each.
> Outreach: cold mail / WhatsApp etc. — cover the **different genres of cold mailing**, the approach, and **why each approach matters**.
> "Ideas are raw" — wants it planned out and simplified.

**Distilled:** Niche-agnostic AI agent that *finds* a business, *diagnoses* its problems, *maps* solutions with %-impact, *drafts* the outreach — delivered as flash cards. For solo freelancers/agencies.

**Decisions locked this session:**
- Positioning: NOT another contact-list tool (Apollo/Clay own that). Differentiator = **pre-diagnosed leads** (problem found + solution + pitch, ready to send).
- Build order: validate analysis quality first (Phase 0 script), UI later.
- Compliance is a product constraint, not an afterthought (CAN-SPAM / GDPR / data minimization / Google ToS).
- Security: provided Security Rules + vibe-coding 23-area checklist apply from day 1.

**Open questions for user (see PLAN.md §10):** primary niche to validate first, local-biz vs job-board sourcing first, send-or-draft-only for v1, budget for paid data/LLM APIs.

---

## P-002 — 2026-06-30 — Sources + agent count
**Status:** planned

**Raw intent (user):** Plan has some things off — will correct step by step while building. Next: clarify/complete the product idea, then tech stack (how to build, what agents, MCP, everything). Immediate question: **what is the source?** Wants MANY sources — 200+ sites/sources or n-number, "the bigger the source the better the result." Refuses LinkedIn-only or empty/thin responses; 10 leads = won't close. Asked: how many agents — 2–3? recommend.

**Distilled:** Maximize source coverage (volume) without thin/garbage output; recommend agent architecture for sourcing.

**Answer locked this session:**
- Source model = **Tier A meta-search (search API + Google dorks = ∞ sites)** as backbone + ~15 structured APIs + intent/trigger feeds → funnel (dedupe → score → enrich → diagnose). Volume solved at the *query* layer, not by 200 integrations. Full catalog → [SOURCES.md](SOURCES.md).
- Agents = **orchestrator + 3 workers** (Scout pool / Analyst / Closer). Scout fans out in parallel across all source-tools = where the 200+ coverage happens. Avoid 10-agent sprawl.
- Each source = one **MCP tool** behind a common interface (mcp-builder skill).

**Correction noted:** user says PLAN.md has inaccuracies — to be revised together, step by step, during build. Don't treat PLAN v0.1 as locked.

---

## P-003 — 2026-06-30 — Evergreen source engine + full workflow + LLM provider
**Status:** planned

**Raw intent (user):** No Anthropic keys → will use Grok/Nvidia API keys etc. Wants the complete source workflow: how sources are *found* and kept **evergreen** (app + sources never break, self-maintaining); all source possibilities; how to manage sources; how agents traverse them; how many agents; **validator agents?**; full backend + logic; user requirement → processing → delivery, step by step; and which sources serve which purpose (leads vs clients vs cold-email contacts vs free public contact lists).

**Distilled:** Design the end-to-end, self-healing, provider-agnostic source+agent pipeline.

**Answer locked this session → [WORKFLOW.md](WORKFLOW.md):**
- **LLM = model-agnostic router** (LiteLLM/OpenRouter) over Grok/Nvidia/Groq/DeepSeek. Tier cheap-vs-big by task. (PLAN §8 corrected — was Claude.)
- **Evergreen via:** sources-as-DATA (Source Registry, no redeploy) · adapter pattern + MCP · least-fragile-first (API>feed>search>scrape) · **LLM extraction not CSS selectors** (self-healing) · circuit breakers + reliability scoring (route around dead → never empty) · **Source-Discovery agent** (catalog grows itself).
- **Agents = orchestrator + 6 roles + 2 validator gates** (Validator-1 data/dedupe/email-MX, Validator-2 anti-hallucination/compliance). Validators mandatory *because* open models hallucinate.
- **Funnel:** 1000 raw → validate → enrich → qualify → diagnose → validate → ~150 send-worthy cards.
- **User flow:** async Run, results stream live (no blank wait).
- **Source routing by purpose** documented (intent/job vs directory/diagnose vs contact-finding).

---

## P-004 — 2026-06-30 — Hidden sources + where contacts come from
**Status:** planned

**Raw intent (user):** Beyond Google Maps/LinkedIn/Fiverr/Upwork — what other / **hidden** sites for clients, leads, cold-emailing? Where will we find the contacts of these people?

**Distilled:** Name the non-obvious lead sources + the contact/email-finding stack.

**Answer locked → [SOURCES.md](SOURCES.md) new sections "HIDDEN high-intent lead sources" + "CONTACT/EMAIL finding waterfall":**
- Hidden leads: HN Who's-Hiring (Algolia), Reddit r/forhire + complaint subs, X/Grok intent search, Indie Hackers, Product Hunt/BetaList, niche Slack/Discord #jobs, FB groups, job-board *aggregators* (Adzuna/Jooble/Google Jobs/JSearch = many boards in 1 call), Crunchbase/funding triggers, BuiltWith tech-gap lists, Trustpilot/G2 bad reviews, SAM.gov/TED/RFP, regional (IndiaMART/Justdial/Yell/Europages).
- Contacts waterfall: page/LLM-extract → social bios → Places → WHOIS → contact dorks → OpenCorporates/registries → finder APIs (Apollo/Hunter/Snov/ContactOut/etc.) → people DBs (PDL) → pattern-guess + **verify (NeverBounce/ZeroBounce)** → Common Crawl. Verify before send; compliance.

---

## P-005 — 2026-06-30 — Free-only sources + Brave question
**Status:** done (SOURCES.md rewritten)

**Raw intent (user):** SOURCES.md must include ONLY free resources — no paid. Also: are we using Brave Search API, for what, and where to get it?

**Distilled:** Strip paid from catalog; clarify Brave.

**Answer locked:**
- **SOURCES.md rewritten free-only.** Legend FREE/FREE-API/SELF-HOST/FEED/SCR/FREE-TIER. Added "Removed — PAID" section listing what was dropped + why.
- **Brave Search API = REMOVED.** It killed its free tier Feb 2026 (now $5/1k queries, card required, no spend cap). It *was* the planned Tier-A meta-search backbone (run dork queries → whole-web results). **Free replacement: SearXNG (self-host, primary) + DuckDuckGo + Google PSE (100/day).**
- New free maps primary = **OpenStreetMap/Overpass** (Google Places needs a billing account → dropped).

---

## P-006 — 2026-07-01 — Build workflow locked + GCF defined
**Status:** planned

**Raw intent (user):** Starting the project. Defined build order: (1) validate all sources at once, (2) find + test free API keys [both LOCKED first, non-negotiable], (3) orchestrator platform, (4) roles starting with Planner agent → Planner shows combined 4–5 tier meta-search plan report to user → after user finalizes, convert to **GCF** for token optimization + fast context sharing between agents; more agents TBD → backend → full workflow → database → basic frontend (test) → good frontend. Asked for recommendations (but won't change steps 1–2). Clarified **GCF = Graph Context Form**. Asked to save plan to plans.md.

**Distilled:** Lock build order; design graph-based shared context; capture recommendations.

**Answer locked → [plans.md](plans.md):**
- Full phased order 0a→8 saved. Steps 0a (validate sources) + 0b (validate keys) kept first per user.
- **Recommendations added:** Registry as Phase-0a output, reusable key-test harness, **thin vertical slice (0c)** before full orchestrator, cost/quota estimate in approval report, cost meter day 1, validators inside orchestrator.
- **GCF = Graph Context Form** designed: typed nodes (Run/Company/Problem/Solution/Contact/Card) + edges; agents read/write subgraphs, pass node refs not text = token savings.

---

## P-007 — 2026-07-01 — All sources on one page: .env.example + keys guide
**Status:** done

**Raw intent (user):** Won't hand-pick sources from the catalog — will provide free API keys. Wants: placeholders in dotenv for ALL mentioned sources + the real way/link to get each free key (even for no-key ones like Taha/vibe, give the link/method). Will use every source. Asked how all sources land "on one page" + recommendation.

**Answer locked:**
- **[.env.example](.env.example)** = the one page. Every source = empty placeholder + inline signup link + free-tier note. [CORE]/[OPTIONAL]/[NO KEY] tags. Grouped by tier + LLM providers + app/infra. Skills (Taha/vibe) flagged NO KEY (local docs).
- **[API_KEYS.md](API_KEYS.md)** = step-by-step how-to-get for each, grouped, verified URLs (web-checked, vibe rule 29).
- **Recommendation given:** grab ~6 CORE keys first (1 LLM + Tavily/SearXNG + Reddit + SECRET_KEY + DATABASE_URL) → run thin slice → backfill rest. Don't block on 40 keys.
- LLM providers verified: xAI console.x.ai, NVIDIA build.nvidia.com (best free), Groq, OpenRouter, DeepSeek, Gemini.
- Next: Phase 0b key-test harness (pings each configured key, ✅/❌ + quota, skips empty).

---

## P-008 — 2026-07-01 — Full project structure + multi-key .env + validator
**Status:** done (skeleton) / awaiting user to fill keys

**Raw intent (user):** Create whole project structure. Phase 0/1 = validate all API keys + configure all search engines + all tiers A–H. Asked how many tiers. Wants .env.example placeholders for everything incl. **multiple LLM/Grok keys** so LLM ops don't break mid-run. Don't ask for no-key engines (DuckDuckGo). After filling, tell them Phase 1 done → backend → orchestration platform (configure agents). Also: in chat list which keys are manual.

**Answer locked:**
- **8 tiers, A–H** (A = search backbone; B–H specialized).
- **Structure scaffolded** under `backend/` (49 files): app/{core,llm,sources/adapters,agents,pipeline,db,api/routes}, scripts/, tests/. Skeleton stubs w/ TODO headers + vibe-rule refs.
- **Cornerstones written:** `.env.example` (multi-key comma pools for all 6 LLM providers + Tavily), `app/config.py` (parses pools), `app/llm/key_pool.py` (rotation + failover), `scripts/validate_keys.py` (stdlib key-test harness, live /models checks), README, .gitignore, requirements.txt.
- **Multi-key design:** `XAI_API_KEYS=k1,k2,k3` etc. → KeyPool round-robin + cooldown on 429/quota → run never breaks.
- Manual keys (🔑) listed to user; 🆓 no-key engines excluded.
- Next after user fills + validates: Phase 1 done → backend → orchestration/agents.

---

## P-009 — 2026-07-01 — Full build: plan-approval flow + validators everywhere + running product
**Status:** built & running — awaiting user's real `.env` for LLM stages

**Raw intent (user):** Claims keys pasted+validated (NOT found on disk — no `.env` exists; flagged honestly). Wants: (1) user enters requirements → Planner makes plan → plan shown → user approves → workflow runs per WORKFLOW.md; (2) **validator agent at EVERY step**; (3) use free engines (DuckDuckGo, Wikipedia, …) + all keys/engines from .env.example; (4) after orchestration → basic frontend for testing, improve later; (5) deliver final running product; state time if long; (6) **rank all leads** for the user.

**Built (complete, compiles, server verified):**
- `llm/client.py` — provider-agnostic chat, key-pool rotation + cross-provider failover, live /models verification, tolerant JSON extractor.
- `core/security.py` — SSRF guard + untrusted-content wrapping.
- 15 source adapters (A: searxng/ddg/tavily/pse/wikipedia/marginalia · B: hn/remoteok/remotive/adzuna · C: overpass/yelp · D: github · E: reddit · G: newsapi); unconfigured auto-skip; 8 active with zero keys.
- 5 validator gates: V1 plan, V2 candidates, V3 contacts, V4 groundedness/honest-%, V5 outreach compliance.
- Agents: planner, scout (parallel fan-out), qualifier (**0-10 fit score = ranking**), enricher (SSRF-guarded page extract), analyst, closer.
- GCF graph store persisted per run; pipeline threads; Run/Card SQLite models; REST (`POST /api/runs`, `/approve`, `GET /api/runs/{id}`, `/api/sources`); rate-limit + security headers + generic errors.
- Basic frontend (`frontend/index.html`, XSS-safe): form → plan review → approve → live log → **ranked** flash cards w/ copy-outreach.
- Verified: `compileall` clean; uvicorn on :8000; /api/health, /api/sources, / all 200.

**Blocker for full E2E:** user must actually create `.env` (their pasted keys never landed on disk).

---

## P-010 — 2026-07-05 — Testing agent + keys live + system ALL GREEN
**Status:** done — product running end-to-end ready for user test

**Raw intent (user):** Pasted keys into .env. Wants: (1) deploy ONE testing agent that tests the whole project, (2) rerun frontend+backend, (3) give the URL.

**Done:**
- **Testing agent** built: `backend/scripts/test_agent.py` — 11 checks across every layer (config/pools, live LLM cheap+big generation, live source searches, SSRF guard, injection wrapper, validator gates, GCF, DB, API routes, frontend XSS-audit). `--fast` flag skips live LLM.
- **Bug found & fixed by the agent:** config loaded `.env` relative to CWD → repo-root `.env` invisible from `backend/`. Fixed with absolute env paths + `NoDecode` comma-pool parsing.
- **Result: 11/11 PASS.** All 6 LLM pools live (xai/nvidia/groq/openrouter/deepseek/gemini); 7 sources returning data live (ddg/tavily/hn/remoteok/remotive/github/newsapi).
- Server restarted w/ keys: health OK, 15 sources registered, frontend 200. URL: **http://127.0.0.1:8000**.
- Known minor: `.env` lines 58–60 unparseable (harmless paste artifact); google_pse returns 0 (check "Search entire web" toggle); reddit off (no client id/secret); searxng not self-hosted yet.

---

## P-011 — 2026-07-05 — Fix DDG monopoly, jobs-not-businesses, add multiselect dropdowns
**Status:** done

**User feedback (3 bugs):** (1) ~90% leads from DuckDuckGo — other sources/keys barely used; (2) results are mostly JOBS not businesses/clients/tenders — violates the original "find businesses + diagnose problems" vision; (3) frontend too simple — wants multi-select dropdowns to pick options/sources and widen search.

**Root causes (all mine):** (1) scout only ran the single source the planner named per tier → planner leaned on DDG. (2) planner prompt told it to use "looking for/need a/hiring" intent phrasing → surfaced job posts. (3) no source/type controls.

**Fixes:**
- `scout.py` rewrite: every query dispatched across ALL selected sources (cap 6/source) → balanced. Verified live: ddg 24, tavily 24, remoteok 16, github 15 (was 90% ddg). Adds `last_breakdown` per-source tally to the run log.
- `planner.py` rewrite: business-first (find BUSINESSES to diagnose, not jobs); lead-type aware; job/intent phrasing only when those types selected; fallback business queries.
- API `RequirementsIn`: added `lead_types[]` (enum allowlist) + `sources[]` (explicit override).
- `run_pipeline._resolve_sources`: lead_types → adapter map; explicit sources win; logs source list + breakdown.
- Frontend: two **multi-select checkbox dropdowns** (What to find / Sources — sources loaded live from /api/sources), better niche help ("business type, not 'clients'"), auto-scroll between steps.
- Earlier same session: fixed CSP-blocked inline JS (moved to external /app.js) — that was why "Build my plan" did nothing.

**Known weak spots:** Overpass (local maps) still returns 0 (OSM category keyword too strict, e.g. "dental"≠amenity=dentist) — search engines cover business discovery meanwhile. `.env` lines 58-60 unparseable (harmless paste artifact).

---

## P-012 — 2026-07-05 — Deep contact-finding + verification + "contact first" priority
**Status:** done

**User ask:** surface the mail + contact info for the most relevant leads — the ones to contact for major influence.

**Built:**
- `core/contacts.py` — contact waterfall: scrape root + /contact + /about + /about-us for mailto:/tel:/emails/phones/socials; rank emails (own-domain + role inboxes first); pattern-guess `first.last@domain` when person+domain known; verify via Reoon → MillionVerifier (free keys) → status valid|risky|invalid|guessed|unverified.
- `enricher.py` rewrite: LLM extracts company/person/role/context, then contact waterfall attaches verified email/phone/socials.
- `Card` model: +`email_status`, +`socials` (dev.db reset).
- API: returns email_status/socials + computes `priority` = fit≥7 AND usable email → "★ CONTACT FIRST".
- Frontend: prominent Contact block (clickable mailto, status dot, copy btn, phone, socials) + gold priority badge/border on best leads.
- Verified live: pattern-guess + social scrape working.

**Note:** email discovery depends on the business publishing one; many small sites do. Where none exists → pattern-guess (marked "guessed") + socials/website shown.

---

## P-013 — 2026-07-05 — Multi-select + Select-all + custom on every field
**Status:** done

**User ask:** every dropdown should allow multiple selection + a "Select all" + an "add custom" option (not just What-to-find/Sources).

**Built:**
- Frontend: generalized the multi-select dropdown component → optional **Select all** row + optional **Add-custom** input (type + Enter/Add → checked custom option). Applied to Service, Niche, Location (with curated option lists SERVICES/NICHES/LOCATIONS) + kept on What-to-find/Sources. Summary shows "N selected".
- Backend: `RequirementsIn.service/niche/location` now `list[str]` (service+niche require ≥1, coerce str→list, cap 12 items). `planner.make_plan` takes lists → generates queries per niche×location. `scout.run_scout(plan, locations, sources)` loops local adapters per location. Pipeline joins service list for analyst/closer; GCF stores joined strings.
- Verified: multi-value schema parse OK; run created with service/niche/location arrays; compile clean; server 200.

---

## P-014 — 2026-07-06 — Clean .env + refactor sources to match real keys
**Status:** done

**User ask:** clean the .env — check present vs absent keys, remove empty placeholders, properly format present ones, then refactor sources to match.

**Done:**
- Read `.env`; found junk lines 58-60 (stray `npm create devvit`/`cd`/`npm run dev` pasted in → the parse-error source) + `PRODUCTHUNT_TOKEN` had a mid-string space + `SEARXNG_BASE_URL` pointing at a non-running localhost.
- Rewrote `.env` clean: only present keys, formatted, empties removed (Reddit/Yelp/OpenCorporates/CompaniesHouse/Mastodon/Telegram/SAM/Redis), generated a real `SECRET_KEY`, joined the PH token, dropped SearXNG URL, set real NOMINATIM/SEC user-agents.
- **Refactored sources** to use the keys that were sitting idle: added `JoobleAdapter`, `USAJobsAdapter` (Tier B), `ProductHuntAdapter` (Tier G); registered + wired into LEAD_TYPE_SOURCES.
- Result: **15 active sources** (was ~13), no .env parse warnings. Live-tested: jooble 3, usajobs 1, producthunt 0 (token malformed → graceful skip). Inactive (correct): searxng, yelp, reddit.
- **Security flagged to user:** real keys now in transcript → rotate, esp. GITHUB_TOKEN (ghp_).

---

<!-- Add P-015 ... below as new prompts arrive -->













