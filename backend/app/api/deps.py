"""Shared FastAPI dependencies (auth)."""
from __future__ import annotations

import hmac

from fastapi import Header, HTTPException

from ..config import get_settings


def require_api_token(authorization: str = Header(default="")) -> None:
    """Optional shared-token auth for mutating endpoints.

    When API_TOKEN is unset (local dev) this is a no-op. When set, callers must
    send `Authorization: Bearer <token>` or get a 401.
    """
    token = get_settings().API_TOKEN
    if not token:
        return
    expected = f"Bearer {token}"
    if not hmac.compare_digest(authorization.encode(), expected.encode()):
        raise HTTPException(401, "missing or invalid API token")
