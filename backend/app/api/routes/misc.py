"""Health + source-registry endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from ...llm.client import get_llm
from ...sources.registry import registry_status

router = APIRouter(prefix="/api", tags=["misc"])


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/sources")
def sources():
    return {"sources": registry_status(),
            "llm_providers": get_llm().pools.available_providers()}
