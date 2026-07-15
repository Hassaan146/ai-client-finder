# AI Client/Lead Finder — Project Plan (v0.1)

Date: 2026-06-30 · Status: planning · Owner: Hassaan

---

## 1. One-line vision
An AI agent that **finds a business, diagnoses its problems, maps solutions with %-impact, and drafts the outreach** — delivered as a flash card. Niche-agnostic. Built for solo freelancers and small agencies who hate manual prospecting.

## 2. The problem we kill
Freelancing is slow because *finding paying clients* is slow: build gigs, wait, manually hunt leads, guess what to pitch. We remove the hunting **and** the guessing.

## 3. Why this is different (positioning)
The market is crowded — Apollo, Clay, Lemlist, AiSDR, ZoomInfo. **They all sell the same thing: contact lists you must analyze yourself.** You bring the ICP, they enrich.

**Our wedge:** we deliver a *pre-diagnosed lead*. Not "here's a company + email" but "here's a company, here's the 3 problems it has, here's the solution you can sell, here's the projected %-impact, here's the email — send it." Diagnosis + solution + pitch, not a spreadsheet.

> Tagline candidate: *"We don't find you contacts. We find you problems you can get paid to fix."*

## 4. Core loop (the agent)
```
[1 SOURCE] → [2 ENRICH] → [3 ANALYZE] → [4 MAP SOLUTION] → [5 DRAFT OUTREACH] → [6 FLASH CARD]
```

1. **Source** — find candidate businesses. Two modes:
   - *Local mode:* Google Places/Maps — "{niche} in {city}" → business list.
   - *Job mode (later):* scan Upwork/job boards/LinkedIn for posted needs.
2. **Enrich** — website, socials, contact + decision-maker via enrichment API (Hunter/Apollo/PDL). Prefer official APIs over scraping (legal + reliable).
3. **Analyze** — LLM reads the company's digital footprint → diagnoses gaps: no online booking, no WhatsApp automation, weak SEO, slow site, no review responses, no cold-outreach motion, thin content, etc. Scores opportunity 1–10.
4. **Map solution** — per problem → concrete solution + **projected %-impact (as a labelled estimate/range, never a fake hard stat)** + why it matters to the client and stakeholders.
5. **Draft outreach** — tailored message in a chosen *genre* (see §6). Channel: cold email / WhatsApp / LinkedIn.
6. **Flash card** — final deliverable (see §5).

## 5. Flash card schema (the deliverable)
Maps 1:1 to the `lead-research-assistant` skill output + your idea:

| Field | Source |
|---|---|
| Client name + company | Source/Enrich |
| Company details (industry, size, location, website, socials) | Enrich |
| Contact (decision-maker role, email, LinkedIn) | Enrich |
| **Fit score (1–10)** + why | Analyze |
| **Requirement** (what they need) | Analyze |
| **Analyzer** (what the client wants — short) | Analyze |
| **Problems found** (ranked) | Analyze |
| **Solution mapping** (problem → solution → %-impact → why it matters) | Map |
| **Outreach draft** (genre-tagged) | Draft |
| Confidence + data sources (for honesty/GDPR) | All |

## 6. Cold-outreach genres (cover these)
- **Problem-first / diagnostic** — "Noticed X is costing you Y." (our default — fits the diagnosis engine)
- **Trigger-event** — react to news/hiring/launch.
- **Social proof / case study** — "did this for a similar business → +Z%."
- **Question / curiosity** — one sharp question, low friction.
- **Value-first / loom-video** — give a mini audit free.
- **Referral / warm-intro angle.**
Each card picks the genre with the best fit and says **why** that approach for that client.

## 7. Skill → module mapping (which provided/Anthropic skills power what)
| Module | Skill used |
|---|---|
| Lead diagnosis + flash-card format | `lead-research-assistant` |
| ICP, account tiering, signals, cadences | `prospecting` |
| Channel choice (email vs LinkedIn vs WhatsApp), CAC sanity | `channel-expert` |
| Outreach copy per genre | `copywriter-skill` |
| Opportunity scoring / metrics | `data-analysis` |
| System design + stack | `software-architect` |
| Don't-break-after-deploy | `build-for-maintenance` |
| **Security (keys, injection, cost)** | provided **Security Rules** + `vibe-coding-rules` (23 areas) |
| Token efficiency | `caveman` |
| Market research / grounding | `WebSearch` / research skills |

## 8. Architecture (first pass)
- **Frontend:** Next.js — flash-card UI, run dashboard, export CSV.
- **Backend:** API service (FastAPI or Node). **All LLM + 3rd-party keys server-side only** — never in browser (Security Rule 1 & 13).
- **Agent orchestration:** pipeline/graph of nodes (source→enrich→analyze→map→draft), e.g. LangGraph or a plain typed pipeline.
- **LLM layer — model-agnostic (no Anthropic keys).** Provider-agnostic router (LiteLLM/OpenRouter) over Grok/xAI, Nvidia NIM, Groq, DeepSeek, etc. Tier: cheap/fast model for scout/extract/validate, bigger model for diagnosis/pitch. `max_tokens` capped, per-user token budget (Security Rule 13, Eng Rule 16). Open models hallucinate more → **validator agents mandatory** (see WORKFLOW §4). Full pipeline → [WORKFLOW.md](WORKFLOW.md).
- **Data:** Postgres (users, runs, leads). Indexes + transactions on multi-step writes (Eng Rules 15, 18). Cache company analysis to avoid re-paying.
- **Jobs:** background queue (scraping/enrichment is slow) — BullMQ/Celery.
- **External:** Google Places API, enrichment API (waterfall: Hunter → Apollo → PDL), web search.

## 9. Hard constraints (security + legal — baked in, not bolted on)
**Security (from your Security Rules + 23-area checklist):**
- Secrets in `.env` only; `.gitignore` them; `.env.example` committed.
- Rate-limit every public endpoint (LLM proxy: 10/min/user).
- Validate all input server-side (Zod/Pydantic).
- **Treat ALL scraped/enriched web text as UNTRUSTED → prompt-injection guard before it reaches the LLM.** (A scraped site could contain "ignore previous instructions.")
- Sanitize LLM output before rendering (XSS).
- Per-user token + spend budget (cost-attack defense).
- Generic errors to client; full logs server-side.

**Legal (research-confirmed, 2026):**
- Scraping *public* business data (name/address/phone/site) is legal in the US; ToS breach risks only your Google account → prefer the **official Places API**. Don't resell Google's DB structure.
- Cold email: **CAN-SPAM (US)** → unsubscribe link + physical address + honest subject. **GDPR (EU)** → legitimate-interest basis, opt-out everywhere, **name the data source** in the message.
- **Data minimization** — collect only what the pitch needs.
- **Honesty rule:** %-impact figures must be labelled estimates/ranges with reasoning shown — never fabricated hard stats. Fake numbers kill credibility and create legal risk.

## 10. Phasing (ship small, validate the risky bit first)
- **Phase 0 — Validate the brain (no UI).** Script: Places search → 10 companies (one niche, one city) → enrich → Claude diagnosis → markdown flash cards. **Goal: prove the analysis + pitch are good enough that a real freelancer would send them.** This is the make-or-break assumption.
- **Phase 1 — MVP app.** Web UI, local mode only, flash cards, CSV export, auth, 1 enrichment source. Security baseline in place.
- **Phase 2 — Outreach.** Genre engine + send (or copy-to-send) + open/reply tracking + compliance footer.
- **Phase 3 — Scale.** Job-board mode, waterfall enrichment, scoring model, dashboards, caching, cost caps.

## 11. Top risks
1. **Analysis credibility** (biggest). If diagnosis/%-impact feels generic or fake → no replies. Mitigate: grounded reasoning, honest ranges, human-review step in v1.
2. **Email deliverability** — sending infra (domains, warmup) is its own hard problem. v1 = **draft-only, user sends** to sidestep it.
3. **Cost per lead** — LLM + enrichment add up. Cache + tier models + per-user caps.
4. **Legal/ToS** — handled via official APIs + compliance fields.

## 12. Open questions (need user input)
1. **First niche** to validate in Phase 0? (sharper = better demo)
2. **Sourcing first:** local-biz (Google Maps) or job-board/Upwork posts?
3. **v1 sends email, or draft-only?** (recommend draft-only)
4. **Budget** for paid Places + enrichment + LLM during build?
5. Target user = **you only**, or a product for other freelancers?
