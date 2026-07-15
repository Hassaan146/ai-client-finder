# Source Catalog — FREE resources only

Rule: **only free resources here.** No paid/card-required tools. Paid ones removed (list + reasons at bottom).

**Core principle:** Don't build 200 scrapers. Build ~15 source-tools, one of which (a free search layer + dorks) covers the whole web. The 200+ sources below are reachable through those tools — mostly via free search/feeds/APIs, not separate paid integrations.

**Legend:**
- `FREE` — fully free, no key, no account
- `FREE-API` — free API key, **no credit card**
- `SELF-HOST` — open-source, run it yourself = free + unlimited
- `FEED` — free RSS/JSON feed
- `SCR` — free to scrape (fragile → use LLM extraction, see WORKFLOW §3.4)
- `FREE-TIER` — free monthly quota, account only (no card to start)

---

## Tier A — Meta-search backbone (free = ∞ sites)
One layer → the whole web. This is 80% of coverage. (Brave used to be the pick — now paid, removed.)
- **SearXNG** `SELF-HOST` — open-source meta-search; aggregates Google/Bing/DDG/etc. behind one API. Self-host → unlimited, no key, no cost. **Primary backbone.**
- **DuckDuckGo** `FREE` — via `ddgs` / `duckduckgo_search` lib. No key.
- **Google Programmable Search Engine (PSE)** `FREE-API` — 100 queries/day free.
- **Marginalia Search** `FREE-API` — independent index, free API.
- **Mojeek** / **Common Crawl** `FREE` — independent index / web-scale public dataset.
- **Tavily** `FREE-TIER` — 1,000 searches/mo free, no card.
- **Google dork patterns** (run through any of the above):
  - `intitle:"looking for" {service}`
  - `intext:"hiring a freelance {role}"`
  - `"need a {service}" site:reddit.com`
  - `{niche} {city} -site:linkedin.com`

## Tier B — Freelance & job boards (high intent, free access)
Free APIs/feeds: **Reddit** `FREE-API` · **HN Algolia** (Who's Hiring) `FREE-API` · **Upwork RSS** `FEED` · **Freelancer.com API** `FREE-API` · **RemoteOK** `FEED` · **We Work Remotely** `FEED` · **Remotive** `FREE-API` · **Himalayas** `FREE-API` · **Adzuna** `FREE-API` (job aggregator = many boards) · **Jooble** `FREE-API` · **USAJOBS** `FREE-API` · **Product Hunt** `FREE-API`.

Scrape (free): PeoplePerHour, Guru, Contra, Twine, Workana, Truelancer, 99designs, Wellfound/AngelList, YC "Work at a Startup", Indie Hackers, BetaList, Dribbble Jobs, Behance, ProBlogger, Authentic Jobs, Working Nomads, Nodesk, JustRemote, Jobspresso, Pangian, Dynamite Jobs, Built In, Otta, Careerjet.

## Tier C — Local / maps directories (free)
- **OpenStreetMap / Overpass API** `FREE` — **primary maps source**, no key, no card.
- **Nominatim** `FREE` — geocoding.
- **Yelp Fusion** `FREE-TIER` — free quota.
- Scrape: YellowPages, Manta, Hotfrog, Brownbook, Cylex, Europages, Kompass, Yell (UK), Houzz, Thumbtack, Bark, BBB, Justdial / IndiaMART / TradeIndia / Sulekha (IN), Chamber of Commerce member lists.

## Tier D — Company intel (free)
- **OpenCorporates** `FREE-API` (attribution) — company + director data.
- **Wikidata / Wikipedia** `FREE-API` · **SEC EDGAR** `FREE` (US filings) · **Companies House UK** `FREE-API` · national business registries `FREE`.
- **GitHub API** `FREE-API` (devs/orgs/tech) · **Hacker News** `FREE-API`.
- **Wappalyzer (open-source)** `SELF-HOST` — detect a site's tech stack (find sites missing the tool you sell).
- BuiltWith free site lookup, Crunchbase web, G2/Capterra/TrustRadius reviews — `SCR`.

## Tier E — Social / intent listening (free)
Reddit `FREE-API` (r/forhire, r/jobbit, r/hireawriter, r/DesignJobs, r/smallbusiness, r/SaaS) · X/Twitter via **Grok** (your LLM does live search) · **Mastodon API** `FREE-API` · **Bluesky / AT Protocol** `FREE-API` · **Telegram Bot API** `FREE-API` · Quora, Indie Hackers, Facebook groups, Nextdoor `SCR` · niche **Slack/Discord `#jobs`** (join the community).

## Tier F — Tenders / RFP / government (free, public)
**SAM.gov** `FREE-API` (US) · **TED europa** `FREE-API` (EU) · **Grants.gov** `FREE-API` · **USAspending** `FREE-API` · **RFPDB** · national e-procurement portals `SCR`.

## Tier G — Trigger / signal feeds (free)
- **GDELT** `FREE-API` (global news/events) · **Google Trends** via `pytrends` `FREE` · Wikipedia pageviews `FREE-API`.
- Product Hunt / BetaList (just launched), GitHub Trending, HN front page (momentum) `SCR`/`FREE-API`.
- Tech-gap: Wappalyzer self-host + BuiltWith free lookup → sites using/missing a tool.

## Tier H — Contact / email finding (free waterfall)
Run top→bottom, stop when verified:
1. **Page extract** `SCR`+LLM — contact/about/team page → email/phone/WhatsApp. Most small biz list it openly.
2. **Social bios** `SCR` — IG/FB/X business profiles show email + WhatsApp directly.
3. **WHOIS / RDAP** `FREE` — domain registrant email.
4. **Contact dorks** `FREE` — `site:{domain} "@{domain}"`, `"{role}" "{niche}" email`.
5. **OpenCorporates + gov registries** `FREE-API` — director names.
6. **Email pattern guess** `FREE` — `first@domain`, `first.last@domain`.
7. **Verify (free tiers / self-host):** Reoon, MillionVerifier (free credits), ZeroBounce (100 free), or **self-host MX/SMTP check** `SELF-HOST` `FREE`. Never send unverified.

---

## How this maps to build
- Phase 0: pick **2–3 free sources per mode** (local = Overpass + dork-search via SearXNG + Reddit; freelance = HN Algolia + Reddit + RemoteOK feed).
- Everything else reached through the **Tier A free search layer**.
- Each = one **MCP tool** behind a common `Source` interface → Scout agent calls all uniformly, parallel.
- Legal: public business data only, verify before send, comply (PLAN §9).

## Coverage math
1 dork on SearXNG ≈ results from dozens–hundreds of sites. 20 query variants × 10 free tools = thousands of raw candidates/run → funnel trims to closeable. Volume solved at the *query* layer, free.

---

## ❌ Removed — PAID / card-required (do NOT use, per free-only rule)
- **Brave Search API** — killed free tier Feb 2026; now $5/1k queries, **credit card required, no spend cap**. (Was the meta-search pick → replaced by SearXNG + DuckDuckGo + Google PSE.)
- **Search:** SerpAPI, Serper.dev, Bing Web Search, Exa/Metaphor, You.com.
- **Contact/data vendors:** Apollo, Hunter, RocketReach, Snov, ContactOut, Wiza, People Data Labs, Clearbit, ZoomInfo, Cognism, Lusha, Seamless, Datanyze.
- **Intel:** PitchBook, CB Insights, SimilarWeb, BuiltWith API (paid endpoints).
- **Maps:** Google Places / Maps Platform API — requires a **billing account** (free credit but card on file) → use OpenStreetMap/Overpass instead.

> Note: some removed tools have tiny "free tiers" but require a card or are fundamentally paid products — excluded to honor the free-only rule. If you ever opt into one, add it to a separate `PAID-SOURCES.md`, not here.
