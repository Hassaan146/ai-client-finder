# Workflow & Source Engine — full design

How requirements become flash cards, and how sources stay **evergreen** (never break, self-maintain, keep growing).

---

## 0. LLM layer — model-agnostic (no Anthropic keys)
You'll use Grok (xAI), Nvidia NIM, etc. So the app never hardcodes a provider.

- **Router/gateway:** LiteLLM (self-host) or OpenRouter — one OpenAI-compatible interface, swap any model by config.
- **Providers we can mix:** xAI Grok (bonus: native live X/web search → use as a *source* too), Nvidia NIM (Llama/DeepSeek/Qwen, cheap), Groq (ultra-fast for cheap tasks), DeepSeek (cheap reasoning), Gemini free tier.
- **Tier by task (cost):** fast/cheap model → scout, extract, dedupe, validate-rules. Bigger model → diagnosis + pitch.
- **Important:** open models hallucinate more than frontier → **validator agents are mandatory** (see §4). Keys server-side only, `max_tokens` capped, per-user budget (Security Rules 13).

---

## 1. User-facing flow (what the user sees)
1. **Input requirements** (form): what service you sell, target niche, location(s), ideal client (size/type), budget/intent signals, channel (email/WhatsApp/LinkedIn), how many leads.
2. Backend creates a **Run** (async job), returns `run_id` instantly. No blank 10-min wait.
3. **Live progress:** flash cards stream in as they're found/validated (progress bar: sourcing → validating → enriching → diagnosing → drafting). Partial results visible immediately.
4. **Receive:** flash cards in UI (filter/sort by fit score). Export CSV. Mark / send / save.

```
[Requirements form] → POST /runs → run_id
        ↓ (async)
  Orchestrator pipeline (below)
        ↓ (streaming)
  Flash cards populate live → user reviews → export/send
```

---

## 2. System overview
```
User → API Gateway → Job Queue → Orchestrator
                                    │
        ┌───────────────────────────┼───────────────────────────┐
     Planner   Scout pool   Validator-1   Enricher   Qualifier   Analyst   Validator-2   Closer
        │         │ (parallel across sources via MCP adapters)                              │
        └──────── Source Registry (DB) ◄── Health Monitor ◄── Source-Discovery agent ───────┘
                                    │
                            Results DB + Cache → Flash cards
```

---

## 3. Source management — the EVERGREEN system
This is the part that keeps the app alive. Five mechanisms:

### 3.1 Source Registry (sources are DATA, not code)
Every source is a DB record, not a hardcoded function:
```
Source {
  id, name, category (lead | company | contact | signal),
  access (api | feed | search | scrape),
  endpoint, auth_ref, rate_limit, parser_config,
  health (healthy | degraded | dead),
  last_success_at, reliability_score (0–1), avg_yield, cost_per_call,
  regions, niches[]
}
```
Add / disable / reprioritize a source = edit a row. **No redeploy.** This alone makes it maintainable.

### 3.2 Adapter pattern (one interface, many sources)
Single contract: `Source.search(requirements) -> Candidate[]`. Four adapter types: `APIAdapter`, `FeedAdapter`, `SearchAdapter` (dork layer), `ScrapeAdapter`. Each wrapped as an **MCP tool** → agents call all sources identically and never touch internals → swap freely.

### 3.3 Least-fragile-first (bias away from breakage)
Preference order: **API > Feed > Search-layer > Scrape.** The Tier-A search meta-layer (SerpAPI/Brave + dorks) is inherently evergreen — search APIs rarely change their contract, and one query reaches thousands of sites. Bias routing toward it → the app almost never breaks even when individual sites change.

### 3.4 Self-healing extraction (AI beats brittle selectors)
Scrapers break when HTML changes. Fix: **don't use fixed CSS selectors — use LLM extraction.** Feed the page to a cheap model: "extract company, contact, email, problem signals as JSON." Layout changes don't break it. When a source's yield drops to zero, a healer step re-derives extraction from the new page automatically. = self-healing scrapers.

### 3.5 Health monitor + circuit breaker + graceful degradation
- Each source has a health check + **circuit breaker**: N consecutive failures → mark `degraded` → auto-skip → alert.
- Orchestrator routes around dead sources → **response never empty** (degrades gracefully across the remaining 200+).
- Retry with backoff; rotate keys/proxies on rate-limit/block.
- **Reliability score** auto-updates from success rate × yield ÷ cost → best sources queried first, flaky ones demoted automatically. Sources self-rank.

### 3.6 Source-Discovery agent (sources keep GROWING = evergreen coverage)
Runs periodically. Uses the search layer to find NEW sources per niche:
`"best {niche} directories"`, `"where do {niche} businesses get listed"`, `"{niche} job boards / communities"`. Each find is auto-classified (category + access type), health-tested, and proposed to the Registry (auto-trust low-risk API/feed; human-approve scrapers). The catalog grows itself.

---

## 4. Agents & validators (the pipeline)
Orchestrator + **6 worker roles + 2 validator gates**. Pools run in parallel.

| # | Agent | Job | Model tier | Gate? |
|---|---|---|---|---|
| — | **Orchestrator** | Own the Run, sequence stages, handle failures | mid | — |
| 1 | **Planner** | Requirements → ICP + source plan + dork query set | big | — |
| 2 | **Scout** (pool, parallel) | Hit every selected source via MCP → raw candidates. *This is where volume happens* | cheap/fast | — |
| 3 | **Validator-1 (Data)** | Dedupe; is it a real entity? contact syntactically valid? email MX check? drop dead/spam | cheap + rules | ✅ |
| 4 | **Enricher** | Fill company + decision-maker + email/phone/LinkedIn (waterfall APIs) | cheap | — |
| 5 | **Qualifier/Scorer** | Fit score vs requirements; drop low-fit before expensive work | cheap | ✅ |
| 6 | **Analyst** | Diagnose problems → map solution + %-impact (labelled estimates) | big | — |
| 7 | **Validator-2 (Quality)** | Anti-hallucination: are claims grounded? %-figures labelled not faked? contact compliant (CAN-SPAM/GDPR)? reject/flag bad cards | big + rules | ✅ |
| 8 | **Closer** | Draft outreach per genre + contact strategy | mid/big | — |

**Why validators are non-negotiable here:** you're on open models (Grok/Nvidia), which hallucinate more than frontier. Validator-1 keeps junk data out (saves cost). Validator-2 keeps fake diagnoses/stats away from the user (saves credibility). Without them, volume = volume of garbage.

**Funnel (volume → quality):**
```
Scout: 1000+ raw → Validator-1: ~400 real → Enricher → Qualifier: ~200 fit
   → Analyst → Validator-2: ~150 trustworthy cards → Closer → user
```

---

## 5. Source routing by PURPOSE (which source for what)
The Planner routes to different source sets depending on intent:

- **Find clients actively needing work (highest intent):** Upwork/Freelancer feeds, HN "Who's Hiring", RemoteOK/WWR, Reddit r/forhire + niche subs, X/Grok live search ("looking for {service}"), tenders/RFP (SAM.gov, TED).
- **Find businesses to cold-diagnose & pitch:** Google Places/Yelp/Maps (local), Clutch/GoodFirms (agencies), Crunchbase (funded = budget), **BuiltWith/Wappalyzer** (sites *missing* the tool you sell = perfect pitch).
- **Find the contact/email (the "free contacts" layer):** website contact/about page (LLM extract), WHOIS, Hunter/Apollo/RocketReach free tiers, LinkedIn, email-pattern guess + **verify (MX/SMTP)**. Public business data only; respect ToS + data-minimization (PLAN §9).

Full named catalog (200+, 8 tiers) → [SOURCES.md](SOURCES.md).

---

## 6. Backend components
- **API gateway** (FastAPI/Node) — requirements in, runs/results out. Rate-limited, validated (Zod/Pydantic).
- **Job queue + workers** (BullMQ/Celery) — long runs async; horizontal scale = more Scout workers.
- **Source Registry DB** — the evergreen config (§3.1).
- **Results DB** (Postgres) — runs, candidates, cards; indexed, transactional.
- **Cache** (Redis) — company analyses + enrichment (don't re-pay per run).
- **LLM Router** (LiteLLM/OpenRouter) — provider-agnostic (§0).
- **MCP source servers** — each adapter exposed as MCP tools.
- **Monitoring** — Sentry + source health dashboard.

---

## 7. Why this is evergreen (summary)
1. Sources are **data** → add/remove without code change.
2. **Search-layer backbone** rarely breaks + reaches the whole web.
3. **LLM extraction** instead of brittle selectors → survives layout changes.
4. **Circuit breakers + reliability scoring** → auto-route around dead sources, never empty.
5. **Source-Discovery agent** → catalog grows itself per niche.
6. **Provider-agnostic LLM** → if Grok/Nvidia changes pricing/limits, swap by config.

---

## 8. Phase 0 cut (build the spine small first)
Don't build all 8 agents day 1. Minimal evergreen spine:
- Registry with **3 sources** (Places API + dork-search + Reddit).
- **Scout → Validator-1 → Enricher → Analyst → Validator-2** (skip Qualifier/Closer pooling; inline them).
- LLM router with **one cheap + one big** model from your providers.
- Output markdown flash cards for 10 companies, one niche/city.
- Prove: validators catch hallucinations + cards are send-worthy. Then expand sources + agents.
