"""Small shared text/list normalization helpers (used across routes, agents, pipeline)."""
from __future__ import annotations


def as_list(v, *, max_items: int | None = None, max_chars: int | None = None) -> list[str]:
    """Normalize a str-or-list value to a clean list[str] (strip, drop empties)."""
    if isinstance(v, list):
        items = [str(x).strip() for x in v if str(x).strip()]
    else:
        s = str(v).strip() if v is not None else ""
        items = [s] if s else []
    if max_chars is not None:
        items = [i[:max_chars] for i in items]
    return items[:max_items] if max_items is not None else items


def join_str(v, sep: str = ", ") -> str:
    """Join a str-or-list value into one display string."""
    return sep.join(as_list(v))
