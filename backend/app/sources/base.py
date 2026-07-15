"""Source adapter contract. Every tier A–H adapter implements `search()`."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


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

    def available(self) -> bool:
        """False when required keys/config missing -> registry auto-skips."""
        return True

    def search(self, query: str, *, location: str = "", limit: int = 10) -> List[Candidate]:
        try:
            return self._search(query, location=location, limit=limit)[:limit]
        except Exception:  # noqa: BLE001 — one dead source never kills the run (vibe 28)
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
