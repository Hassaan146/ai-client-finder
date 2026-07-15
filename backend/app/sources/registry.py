"""Source Registry: every adapter registered here; unconfigured ones auto-skip.

Sources are data-driven (availability from env) so adding keys later
lights up new sources without code changes. vibe 25 / WORKFLOW §3.
"""
from __future__ import annotations

from .adapters.jobs_intent import (
    AdzunaAdapter,
    GitHubAdapter,
    HackerNewsAdapter,
    JoobleAdapter,
    NewsAPIAdapter,
    ProductHuntAdapter,
    RedditAdapter,
    RemoteOKAdapter,
    RemotiveAdapter,
    USAJobsAdapter,
)
from .adapters.local_maps import OverpassAdapter, YelpAdapter
from .adapters.search_engines import (
    DuckDuckGoAdapter,
    GooglePSEAdapter,
    MarginaliaAdapter,
    SearxngAdapter,
    TavilyAdapter,
    WikipediaAdapter,
)
from .base import SourceAdapter

ALL_ADAPTERS: list[SourceAdapter] = [
    # Tier A — search backbone
    SearxngAdapter(), DuckDuckGoAdapter(), TavilyAdapter(), GooglePSEAdapter(),
    WikipediaAdapter(), MarginaliaAdapter(),
    # Tier B — jobs / business boards
    HackerNewsAdapter(), RemoteOKAdapter(), RemotiveAdapter(), AdzunaAdapter(),
    JoobleAdapter(), USAJobsAdapter(),
    # Tier C — local
    OverpassAdapter(), YelpAdapter(),
    # Tier D — company intel
    GitHubAdapter(),
    # Tier E — intent
    RedditAdapter(),
    # Tier G — signals
    NewsAPIAdapter(), ProductHuntAdapter(),
]


def active_adapters() -> list[SourceAdapter]:
    return [a for a in ALL_ADAPTERS if a.available()]


def adapters_by_name() -> dict[str, SourceAdapter]:
    return {a.name: a for a in active_adapters()}


def registry_status() -> list[dict]:
    return [{"name": a.name, "tier": a.tier, "active": a.available()} for a in ALL_ADAPTERS]
