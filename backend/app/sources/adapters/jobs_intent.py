"""Tier B/E adapters — jobs + intent: HN, Reddit, RemoteOK, Remotive, Adzuna, GitHub, NewsAPI."""
from __future__ import annotations

import base64
from typing import List

import httpx

from ...config import get_settings
from ..base import Candidate, SourceAdapter

T = 20.0


class HackerNewsAdapter(SourceAdapter):
    """No key — Algolia API. Who's-hiring + freelance threads."""
    name, tier = "hackernews", "B"

    def _search(self, query, *, location, limit) -> List[Candidate]:
        r = httpx.get("https://hn.algolia.com/api/v1/search",
                      params={"query": f"{query} {location}".strip(), "tags": "story", "hitsPerPage": limit},
                      timeout=T)
        r.raise_for_status()
        out = []
        for h in r.json().get("hits", []):
            out.append(Candidate(
                title=h.get("title") or (h.get("story_text") or "")[:80],
                url=h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                snippet=(h.get("story_text") or "")[:300], source=self.name, tier=self.tier, kind="post"))
        return out


class RedditAdapter(SourceAdapter):
    """App-only OAuth (client_credentials). Intent subs: r/forhire etc."""
    name, tier = "reddit", "E"
    SUBS = "forhire+jobbit+freelance_forhire+smallbusiness+Entrepreneur+SaaS"

    def available(self) -> bool:
        s = get_settings()
        return bool(s.REDDIT_CLIENT_ID and s.REDDIT_CLIENT_SECRET)

    def _token(self) -> str:
        s = get_settings()
        auth = base64.b64encode(f"{s.REDDIT_CLIENT_ID}:{s.REDDIT_CLIENT_SECRET}".encode()).decode()
        r = httpx.post("https://www.reddit.com/api/v1/access_token",
                       data={"grant_type": "client_credentials"},
                       headers={"Authorization": f"Basic {auth}", "User-Agent": s.REDDIT_USER_AGENT},
                       timeout=T)
        r.raise_for_status()
        return r.json()["access_token"]

    def _search(self, query, *, location, limit) -> List[Candidate]:
        s = get_settings()
        tok = self._token()
        r = httpx.get(f"https://oauth.reddit.com/r/{self.SUBS}/search",
                      params={"q": f"{query} {location}".strip(), "restrict_sr": 1,
                              "sort": "new", "limit": limit, "t": "month"},
                      headers={"Authorization": f"Bearer {tok}", "User-Agent": s.REDDIT_USER_AGENT},
                      timeout=T)
        r.raise_for_status()
        out = []
        for ch in r.json().get("data", {}).get("children", []):
            d = ch.get("data", {})
            out.append(Candidate(title=d.get("title", ""),
                                 url=f"https://www.reddit.com{d.get('permalink', '')}",
                                 snippet=(d.get("selftext") or "")[:300],
                                 source=self.name, tier=self.tier, kind="post",
                                 extra={"subreddit": d.get("subreddit", "")}))
        return out


class RemoteOKAdapter(SourceAdapter):
    """No key — public JSON."""
    name, tier = "remoteok", "B"

    def _search(self, query, *, location, limit) -> List[Candidate]:
        r = httpx.get("https://remoteok.com/api",
                      headers={"User-Agent": get_settings().NOMINATIM_USER_AGENT}, timeout=T)
        r.raise_for_status()
        ql = query.lower().split()
        out = []
        for j in r.json():
            if not isinstance(j, dict) or not j.get("position"):
                continue
            text = f"{j.get('position','')} {j.get('company','')} {' '.join(j.get('tags', []))}".lower()
            if any(w in text for w in ql):
                out.append(Candidate(title=f"{j.get('position')} @ {j.get('company')}",
                                     url=j.get("url", ""), snippet=(j.get("description") or "")[:300],
                                     source=self.name, tier=self.tier, kind="job",
                                     extra={"company": j.get("company", "")}))
        return out[:limit]


class RemotiveAdapter(SourceAdapter):
    """No key — public API."""
    name, tier = "remotive", "B"

    def _search(self, query, *, location, limit) -> List[Candidate]:
        r = httpx.get("https://remotive.com/api/remote-jobs",
                      params={"search": query, "limit": limit}, timeout=T)
        r.raise_for_status()
        return [Candidate(title=f"{j.get('title')} @ {j.get('company_name')}", url=j.get("url", ""),
                          snippet=(j.get("description") or "")[:300], source=self.name, tier=self.tier,
                          kind="job", extra={"company": j.get("company_name", "")})
                for j in r.json().get("jobs", [])]


class AdzunaAdapter(SourceAdapter):
    name, tier = "adzuna", "B"

    def available(self) -> bool:
        s = get_settings()
        return bool(s.ADZUNA_APP_ID and s.ADZUNA_APP_KEY)

    def _search(self, query, *, location, limit) -> List[Candidate]:
        s = get_settings()
        r = httpx.get("https://api.adzuna.com/v1/api/jobs/us/search/1",
                      params={"app_id": s.ADZUNA_APP_ID, "app_key": s.ADZUNA_APP_KEY,
                              "what": query, "where": location, "results_per_page": limit}, timeout=T)
        r.raise_for_status()
        return [Candidate(title=f"{j.get('title')} @ {(j.get('company') or {}).get('display_name', '?')}",
                          url=j.get("redirect_url", ""), snippet=(j.get("description") or "")[:300],
                          source=self.name, tier=self.tier, kind="job",
                          location=(j.get("location") or {}).get("display_name", ""),
                          extra={"company": (j.get("company") or {}).get("display_name", "")})
                for j in r.json().get("results", [])]


class GitHubAdapter(SourceAdapter):
    """Orgs/devs by topic. Token optional (higher limit with it)."""
    name, tier = "github", "D"

    def _search(self, query, *, location, limit) -> List[Candidate]:
        tok = get_settings().GITHUB_TOKEN
        headers = {"Accept": "application/vnd.github+json"}
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
        r = httpx.get("https://api.github.com/search/repositories",
                      params={"q": query, "per_page": limit}, headers=headers, timeout=T)
        r.raise_for_status()
        return [Candidate(title=i.get("full_name", ""), url=i.get("html_url", ""),
                          snippet=(i.get("description") or "")[:300], source=self.name, tier=self.tier,
                          kind="signal", extra={"stars": i.get("stargazers_count", 0)})
                for i in r.json().get("items", [])]


class NewsAPIAdapter(SourceAdapter):
    """Funding/growth trigger signals."""
    name, tier = "newsapi", "G"

    def available(self) -> bool:
        return bool(get_settings().NEWSAPI_KEY)

    def _search(self, query, *, location, limit) -> List[Candidate]:
        r = httpx.get("https://newsapi.org/v2/everything",
                      params={"q": f"{query} {location}".strip(), "pageSize": limit,
                              "sortBy": "publishedAt", "apiKey": get_settings().NEWSAPI_KEY}, timeout=T)
        r.raise_for_status()
        return [Candidate(title=a.get("title", ""), url=a.get("url", ""),
                          snippet=(a.get("description") or "")[:300], source=self.name,
                          tier=self.tier, kind="signal") for a in r.json().get("articles", [])]


class JoobleAdapter(SourceAdapter):
    """Job aggregator (many boards in one)."""
    name, tier = "jooble", "B"

    def available(self) -> bool:
        return bool(get_settings().JOOBLE_API_KEY)

    def _search(self, query, *, location, limit) -> List[Candidate]:
        r = httpx.post(f"https://jooble.org/api/{get_settings().JOOBLE_API_KEY}",
                       json={"keywords": query, "location": location}, timeout=T)
        r.raise_for_status()
        return [Candidate(title=f"{j.get('title','')} @ {j.get('company','')}".strip(" @"),
                          url=j.get("link", ""), snippet=(j.get("snippet") or "")[:300],
                          source=self.name, tier=self.tier, kind="job",
                          location=j.get("location", ""), extra={"company": j.get("company", "")})
                for j in r.json().get("jobs", [])[:limit]]


class USAJobsAdapter(SourceAdapter):
    """US federal jobs (needs key + email as User-Agent)."""
    name, tier = "usajobs", "B"

    def available(self) -> bool:
        s = get_settings()
        return bool(s.USAJOBS_API_KEY and s.USAJOBS_EMAIL)

    def _search(self, query, *, location, limit) -> List[Candidate]:
        s = get_settings()
        r = httpx.get("https://data.usajobs.gov/api/search",
                      params={"Keyword": query, "LocationName": location, "ResultsPerPage": min(limit, 25)},
                      headers={"Host": "data.usajobs.gov", "User-Agent": s.USAJOBS_EMAIL,
                               "Authorization-Key": s.USAJOBS_API_KEY}, timeout=T)
        r.raise_for_status()
        out = []
        for it in r.json().get("SearchResult", {}).get("SearchResultItems", []):
            d = it.get("MatchedObjectDescriptor", {})
            out.append(Candidate(title=f"{d.get('PositionTitle','')} @ {d.get('OrganizationName','')}".strip(" @"),
                                 url=d.get("PositionURI", ""),
                                 snippet=(d.get("QualificationSummary") or "")[:300],
                                 source=self.name, tier=self.tier, kind="job",
                                 location=(d.get("PositionLocation") or [{}])[0].get("LocationName", ""),
                                 extra={"company": d.get("OrganizationName", "")}))
        return out


class ProductHuntAdapter(SourceAdapter):
    """Recently launched products/founders (buying-trigger signal). GraphQL v2."""
    name, tier = "producthunt", "G"

    def available(self) -> bool:
        return bool(get_settings().PRODUCTHUNT_TOKEN)

    def _search(self, query, *, location, limit) -> List[Candidate]:
        gql = "{ posts(first: 20, order: RANKING) { edges { node { name tagline website url } } } }"
        r = httpx.post("https://api.producthunt.com/v2/api/graphql", json={"query": gql},
                       headers={"Authorization": f"Bearer {get_settings().PRODUCTHUNT_TOKEN}",
                                "Content-Type": "application/json"}, timeout=T)
        r.raise_for_status()
        ql = query.lower().split()
        out = []
        for e in r.json().get("data", {}).get("posts", {}).get("edges", []):
            n = e.get("node", {})
            text = f"{n.get('name','')} {n.get('tagline','')}".lower()
            if not ql or any(w in text for w in ql):
                out.append(Candidate(title=n.get("name", ""), url=n.get("website") or n.get("url", ""),
                                     snippet=n.get("tagline", ""), source=self.name, tier=self.tier, kind="signal"))
        return out[:limit]
