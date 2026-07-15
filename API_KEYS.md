# API Keys & Sources — master list

Companion to [`.env.example`](.env.example). Every source below, in a list: its key, where to get it, a help note, and its **status**. Paste real keys into `.env` (never here), then run the Phase-0b key-test harness.

**Status legend:**
- 🔑 **Key — you get it** → sign up at the link, paste into `.env`.
- 🆓 **No key — engine figures it out** → nothing to do; the app queries it directly (library/public endpoint). *(e.g. DuckDuckGo)*
- ⚙️ **Self-host** → you run it (Docker); set a URL, no key.

> The `vibe-coding-rules` / Taha skills need **no key** — they're local Markdown docs, not sources.

**Recommendation:** grab the ~6 **[CORE]** keys first (marked below) → run the thin slice → backfill the rest later. Every source already has a placeholder, so nothing's lost.

---

## 1. LLM providers  (need at least one — no Anthropic)
| Platform | Key (env var) | Where to get | Help | Status |
|---|---|---|---|---|
| **NVIDIA NIM** | `NVIDIA_API_KEY` | [build.nvidia.com/settings/api-keys](https://build.nvidia.com/settings/api-keys) | 1000 free credits, 40 req/min, no card. Best free. Key = `nvapi-...` | 🔑 **[CORE]** |
| **xAI Grok** | `XAI_API_KEY` | [console.x.ai](https://console.x.ai) → API Keys | $25 promo/30d. Native live web+X search built in | 🔑 **[CORE]** |
| **Groq** | `GROQ_API_KEY` | [console.groq.com/keys](https://console.groq.com/keys) | Permanent free, no card. Ultra-fast → cheap scout/validate | 🔑 |
| **OpenRouter** | `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) | One key → many `:free` models (20/min, 1000/day) | 🔑 |
| **DeepSeek** | `DEEPSEEK_API_KEY` | [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys) | Cheap reasoning, OpenAI-compatible | 🔑 |
| **Google Gemini** | `GEMINI_API_KEY` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) | Free tier for eligible models | 🔑 |

## 2. Tier A — meta-search backbone
| Platform | Key (env var) | Where to get | Help | Status |
|---|---|---|---|---|
| **SearXNG** | `SEARXNG_BASE_URL` | self-host (Docker) | Aggregates Google/Bing/DDG, unlimited, no key. Primary backbone | ⚙️ **[CORE]** |
| **Tavily** | `TAVILY_API_KEY` | [tavily.com](https://tavily.com) → Get API Key | 1000/mo free, no card | 🔑 **[CORE]** |
| **Google PSE** | `GOOGLE_PSE_API_KEY` + `GOOGLE_PSE_CX` | [programmablesearchengine.google.com](https://programmablesearchengine.google.com) | 100 queries/day free. Need engine + key | 🔑 |
| **DuckDuckGo** | — | — | `ddgs` library, no key. Engine queries it directly | 🆓 |
| **Marginalia** | — | — | Independent index, public API, no key | 🆓 |
| **Common Crawl** | — | — | Web-scale public dataset, no key | 🆓 |

## 3. Tier B — freelance / job boards
| Platform | Key (env var) | Where to get | Help | Status |
|---|---|---|---|---|
| **Reddit** | `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) | Create a "script" app. Set `REDDIT_USER_AGENT` | 🔑 **[CORE]** |
| **Hacker News** | — | — | Algolia public API, no key | 🆓 |
| **Adzuna** | `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` | [developer.adzuna.com/signup](https://developer.adzuna.com/signup) | Job aggregator = many boards in one | 🔑 |
| **Jooble** | `JOOBLE_API_KEY` | [jooble.org/api/about](https://jooble.org/api/about) | Job aggregator | 🔑 |
| **USAJOBS** | `USAJOBS_API_KEY` + `USAJOBS_EMAIL` | [developer.usajobs.gov/apirequest](https://developer.usajobs.gov/apirequest) | Email = required User-Agent | 🔑 |
| **GitHub** | `GITHUB_TOKEN` | [github.com/settings/tokens](https://github.com/settings/tokens) | Classic token, read-only. Devs/orgs/tech | 🔑 |
| **Product Hunt** | `PRODUCTHUNT_TOKEN` | [api.producthunt.com/v2/oauth/applications](https://api.producthunt.com/v2/oauth/applications) | Just-launched founders | 🔑 |
| **RemoteOK** | — | — | Public JSON feed, no key | 🆓 |
| **Remotive** | — | — | Public API, no key | 🆓 |
| **We Work Remotely** | — | — | RSS feed, no key | 🆓 |
| **Himalayas** | — | — | Public API, no key | 🆓 |

## 4. Tier C — local / maps
| Platform | Key (env var) | Where to get | Help | Status |
|---|---|---|---|---|
| **OpenStreetMap / Overpass** | `OVERPASS_URL` | default endpoint | Primary maps source, no key | 🆓 **[CORE]** |
| **Nominatim** | `NOMINATIM_USER_AGENT` | — | Geocoding. No key, just a UA string | 🆓 |
| **Yelp Fusion** | `YELP_API_KEY` | [yelp.com/developers](https://www.yelp.com/developers/v3/manage_app) | Free tier, local businesses | 🔑 |

## 5. Tier D — company intel
| Platform | Key (env var) | Where to get | Help | Status |
|---|---|---|---|---|
| **OpenCorporates** | `OPENCORPORATES_API_KEY` | [opencorporates.com/api_accounts/new](https://opencorporates.com/api_accounts/new) | Free for open-data use; else limited | 🔑 |
| **Companies House (UK)** | `COMPANIES_HOUSE_API_KEY` | [developer.company-information.service.gov.uk](https://developer.company-information.service.gov.uk) | Free UK company data | 🔑 |
| **SEC EDGAR** | `SEC_USER_AGENT` | — | US filings, no key, just a UA | 🆓 |
| **Wikidata** | — | — | Public, no key | 🆓 |

## 6. Tier E — social / intent
| Platform | Key (env var) | Where to get | Help | Status |
|---|---|---|---|---|
| **X / Twitter** | *(uses `XAI_API_KEY`)* | via Grok | Grok's live search covers X intent | 🔑 |
| **Mastodon** | `MASTODON_ACCESS_TOKEN` + `MASTODON_INSTANCE` | `<instance>/settings/applications` | New app → token | 🔑 |
| **Bluesky** | `BLUESKY_IDENTIFIER` + `BLUESKY_APP_PASSWORD` | [bsky.app](https://bsky.app) → Settings → App Passwords | App password, NOT login pw | 🔑 |
| **Telegram** | `TELEGRAM_BOT_TOKEN` | @BotFather → `/newbot` | Community `#jobs` channels | 🔑 |

## 7. Tier F — tenders / government
| Platform | Key (env var) | Where to get | Help | Status |
|---|---|---|---|---|
| **api.data.gov** | `DATA_GOV_API_KEY` | [api.data.gov/signup](https://api.data.gov/signup) | One key unlocks many US gov APIs | 🔑 |
| **SAM.gov** | `SAM_GOV_API_KEY` | [sam.gov](https://sam.gov) → Profile → Account Details → Public API Key | 10/day public, 1000/day registered | 🔑 |
| **TED (EU)** | — | — | EU tenders, public API, no key | 🆓 |
| **Grants.gov / USASpending** | — | — | Public APIs, no key | 🆓 |

## 8. Tier G — trigger signals
| Platform | Key (env var) | Where to get | Help | Status |
|---|---|---|---|---|
| **NewsAPI** | `NEWSAPI_KEY` | [newsapi.org/register](https://newsapi.org/register) | Funding/news, 100/day free | 🔑 |
| **GDELT** | — | — | Global news/events, no key | 🆓 |
| **Google Trends** | — | — | `pytrends` library, no key | 🆓 |

## 9. Tier H — email verification (contact waterfall)
| Platform | Key (env var) | Where to get | Help | Status |
|---|---|---|---|---|
| **ZeroBounce** | `ZEROBOUNCE_API_KEY` | [zerobounce.net](https://www.zerobounce.net) | 100 free/mo. Verify before sending | 🔑 |
| **Reoon** | `REOON_API_KEY` | [reoon.com/email-verifier](https://reoon.com/email-verifier) | Free credits | 🔑 |
| **MillionVerifier** | `MILLIONVERIFIER_API_KEY` | [millionverifier.com](https://millionverifier.com) | Free credits | 🔑 |
| **WHOIS / RDAP** | — | — | Domain registrant email, no key | 🆓 |
| **Pattern-guess + LLM page-extract** | *(uses LLM key)* | — | Build + verify emails, no extra key | 🆓 |

---

## Quick split — what YOU get vs what the engine figures out itself
**🔑 You sign up (paste key):** NVIDIA, xAI, Groq, OpenRouter, DeepSeek, Gemini, Tavily, Google PSE, Reddit, Adzuna, Jooble, USAJOBS, GitHub, Product Hunt, Yelp, OpenCorporates, Companies House, Mastodon, Bluesky, Telegram, api.data.gov, SAM.gov, NewsAPI, ZeroBounce, Reoon, MillionVerifier.

**🆓 Engine figures it out (no key):** DuckDuckGo, Marginalia, Common Crawl, Hacker News, RemoteOK, Remotive, We Work Remotely, Himalayas, OpenStreetMap/Overpass, Nominatim, SEC EDGAR, Wikidata, TED, Grants.gov, USASpending, GDELT, Google Trends, WHOIS/RDAP.

**⚙️ Self-host:** SearXNG.

---

### Next (Phase 0b)
Paste the CORE keys → I build the **key-test harness**: pings each configured key, prints ✅/❌ + quota, skips empty placeholders (test incrementally).

Verified links: [xAI](https://console.x.ai/home) · [NVIDIA](https://build.nvidia.com/settings/api-keys) · [Groq](https://console.groq.com/keys) · [OpenRouter](https://openrouter.ai/) · [DeepSeek](https://platform.deepseek.com/) · [Gemini](https://aistudio.google.com/app/apikey) · [Adzuna](https://developer.adzuna.com/signup) · [Tavily](https://help.tavily.com/articles/9170796666-how-can-i-create-an-api-key) · [SAM.gov](https://open.gsa.gov/api/get-opportunities-public-api/) · [USAJOBS](https://developer.usajobs.gov/apirequest/) · [OpenCorporates](https://api.opencorporates.com/) · [Reddit](https://www.reddit.com/prefs/apps).
