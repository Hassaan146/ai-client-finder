"""Source adapter contract. Every tier A–H adapter implements `search()`."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

import httpx


@dataclass
class Candidate:
    """One raw lead/company found by a source (pre-validation)."""
    title: str
    url: str = ""
    snippet: str = ""
    source: str = ""            # adapter name
    tier: str = ""              # A..H
    kind: str = "company"       # company | job | post | signal
    location: str = ""
    contact_hint: str = ""      # email/phone found inline, unverified
    extra: dict = field(default_factory=dict)


class SourceAdapter:
    """Base adapter. Subclasses set name/tier and implement _search()."""
    name = "base"
    tier = "A"
    last_error = ""   # why the most recent search returned nothing (for run logs)

    def available(self) -> bool:
        """False when required keys/config missing -> registry auto-skips."""
        return True

    def search(self, query: str, *, location: str = "", limit: int = 10) -> List[Candidate]:
        """Never raises (one dead source never kills the run, vibe 28).
        Transient network errors get ONE retry so flaky sites still answer."""
        self.last_error = ""
        for attempt in (1, 2):
            try:
                return self._search(query, location=location, limit=limit)[:limit]
            except (httpx.TransportError, httpx.HTTPStatusError) as e:  # noqa: PERF203
                code = getattr(getattr(e, "response", None), "status_code", None)
                self.last_error = f"{type(e).__name__}" + (f"({code})" if code else "")
                if attempt == 1 and (code is None or code >= 500 or code == 429):
                    time.sleep(1.0)
                    continue
                return []
            except Exception as e:  # noqa: BLE001 — bad payload/parse: not retriable
                self.last_error = type(e).__name__
                return []
        return []

    def _search(self, query: str, *, location: str, limit: int) -> List[Candidate]:
        raise NotImplementedError


def dedupe(cands: List[Candidate]) -> List[Candidate]:
    seen: set[str] = set()
    out: List[Candidate] = []
    for c in cands:
        key = (c.url or c.title).lower().rstrip("/")
        if key and key not in seen:
            seen.add(key)
            out.append(c)
    return out
