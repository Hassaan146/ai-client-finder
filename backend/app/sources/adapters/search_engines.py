"""Tier A adapters — meta-search backbone: SearXNG, DuckDuckGo, Tavily, Google PSE, Wikipedia, Marginalia."""
from __future__ import annotations

from typing import List

import httpx

from ...config import get_settings
from ..base import Candidate, SourceAdapter

T = 20.0


class SearxngAdapter(SourceAdapter):
    name, tier = "searxng", "A"

    def available(self) -> bool:
        return bool(get_settings().SEARXNG_BASE_URL)

    def _search(self, query, *, location, limit) -> List[Candidate]:
        base = get_settings().SEARXNG_BASE_URL.rstrip("/")
        r = httpx.get(f"{base}/search", params={"q": f"{query} {location}".strip(), "format": "json"},
                      timeout=T)
        r.raise_for_status()
        return [Candidate(title=i.get("title", ""), url=i.get("url", ""),
                          snippet=i.get("content", ""), source=self.name, tier=self.tier)
                for i in r.json().get("results", [])[:limit]]


class DuckDuckGoAdapter(SourceAdapter):
    """No key — engine-handled via ddgs library."""
    name, tier = "duckduckgo", "A"

    def available(self) -> bool:
        try:
            import ddgs  # noqa: F401
            return True
        except ImportError:
            try:
                import duckduckgo_search  # noqa: F401
                return True
            except ImportError:
                return False

    def _search(self, query, *, location, limit) -> List[Candidate]:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS  # type: ignore
        q = f"{query} {location}".strip()
        with DDGS() as d:
            rows = list(d.text(q, max_results=limit))
        return [Candidate(title=r.get("title", ""), url=r.get("href", r.get("link", "")),
                          snippet=r.get("body", ""), source=self.name, tier=self.tier)
                for r in rows]


class TavilyAdapter(SourceAdapter):
    name, tier = "tavily", "A"

    def available(self) -> bool:
        return bool(get_settings().TAVILY_API_KEYS)

    def _search(self, query, *, location, limit) -> List[Candidate]:
        keys = get_settings().TAVILY_API_KEYS
        last: Exception | None = None
        for key in keys:  # mini pool failover
            try:
                r = httpx.post("https://api.tavily.com/search",
                               json={"api_key": key, "query": f"{query} {location}".strip(),
                                     "max_results": limit}, timeout=T)
                r.raise_for_status()
                return [Candidate(title=i.get("title", ""), url=i.get("url", ""),
                                  snippet=i.get("content", ""), source=self.name, tier=self.tier)
                        for i in r.json().get("results", [])]
            except Exception as e:  # noqa: BLE001
                last = e
        if last:
            raise last
        return []


class GooglePSEAdapter(SourceAdapter):
    name, tier = "google_pse", "A"

    def available(self) -> bool:
        s = get_settings()
        return bool(s.GOOGLE_PSE_API_KEY and s.GOOGLE_PSE_CX)

    def _search(self, query, *, location, limit) -> List[Candidate]:
        s = get_settings()
        r = httpx.get("https://www.googleapis.com/customsearch/v1",
                      params={"key": s.GOOGLE_PSE_API_KEY, "cx": s.GOOGLE_PSE_CX,
                              "q": f"{query} {location}".strip(), "num": min(limit, 10)}, timeout=T)
        r.raise_for_status()
        return [Candidate(title=i.get("title", ""), url=i.get("link", ""),
                          snippet=i.get("snippet", ""), source=self.name, tier=self.tier)
                for i in r.json().get("items", [])]


class WikipediaAdapter(SourceAdapter):
    """No key. Background/company info."""
    name, tier = "wikipedia", "A"

    def _search(self, query, *, location, limit) -> List[Candidate]:
        r = httpx.get("https://en.wikipedia.org/w/api.php",
                      params={"action": "query", "list": "search", "srsearch": f"{query} {location}".strip(),
                              "format": "json", "srlimit": limit},
                      headers={"User-Agent": get_settings().NOMINATIM_USER_AGENT}, timeout=T)
        r.raise_for_status()
        return [Candidate(title=i["title"],
                          url=f"https://en.wikipedia.org/wiki/{i['title'].replace(' ', '_')}",
                          snippet=i.get("snippet", "").replace('<span class="searchmatch">', "").replace("</span>", ""),
                          source=self.name, tier=self.tier, kind="signal")
                for i in r.json().get("query", {}).get("search", [])]


class MarginaliaAdapter(SourceAdapter):
    """No key — independent index (public endpoint; skipped silently if down)."""
    name, tier = "marginalia", "A"

    def _search(self, query, *, location, limit) -> List[Candidate]:
        r = httpx.get(f"https://search.marginalia.nu/api/search/{httpx.QueryParams({'q': query})['q']}",
                      params={"count": limit}, timeout=T)
        r.raise_for_status()
        return [Candidate(title=i.get("title", ""), url=i.get("url", ""),
                          snippet=i.get("description", ""), source=self.name, tier=self.tier)
                for i in r.json().get("results", [])]
