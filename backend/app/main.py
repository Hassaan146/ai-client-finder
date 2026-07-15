"""FastAPI entrypoint. CORS allowlist (vibe 6), security headers (7), rate limit (2),
generic errors (9), static basic frontend."""
from __future__ import annotations

import time
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .api.routes import misc, runs
from .config import get_settings
from .db.base import init_db

app = FastAPI(title="AI Client/Lead Finder", docs_url="/api/docs", openapi_url="/api/openapi.json")
settings = get_settings()

app.add_middleware(CORSMiddleware, allow_origins=[settings.ALLOWED_ORIGIN],
                   allow_methods=["GET", "POST"], allow_headers=["content-type"])

# simple in-memory per-IP limiter: 60 req/min general, 10/min run-creation
_hits: dict = defaultdict(list)


@app.middleware("http")
async def guard(request: Request, call_next):
    ip = request.client.host if request.client else "?"
    now = time.time()
    bucket = "runs" if (request.url.path == "/api/runs" and request.method == "POST") else "all"
    key = f"{ip}:{bucket}"
    _hits[key] = [t for t in _hits[key] if now - t < 60]
    limit = 10 if bucket == "runs" else 120
    if len(_hits[key]) >= limit:
        return JSONResponse({"detail": "rate limit exceeded"}, status_code=429,
                            headers={"Retry-After": "60"})
    _hits[key].append(now)
    try:
        resp = await call_next(request)
    except Exception:  # noqa: BLE001 — generic out, detail stays server-side (vibe 9)
        import traceback
        traceback.print_exc()
        return JSONResponse({"detail": "internal error"}, status_code=500)
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'"
    return resp


FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/app.js")
def app_js():
    # external JS (no inline scripts) so the strict CSP can stay on (vibe 7/11)
    return FileResponse(FRONTEND_DIR / "app.js", media_type="application/javascript")


app.include_router(runs.router)
app.include_router(misc.router)


@app.on_event("startup")
def _startup() -> None:
    init_db()
