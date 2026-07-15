#!/usr/bin/env python3
"""Phase 0b — key-test harness.

Reads .env, pings every key you filled, prints OK/FAIL (+ model count / quota),
and SKIPS empty placeholders. Stdlib only — run before installing anything:

    python backend/scripts/validate_keys.py

LLM providers are live-tested via their (free) GET /models endpoint = verifies
the key without spending tokens. Multi-key pools: every key is tested.
No-key sources (DuckDuckGo, HN, Overpass...) are not tested — nothing to check.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TIMEOUT = 15
OK, FAIL, SKIP = "\033[92mOK  \033[0m", "\033[91mFAIL\033[0m", "\033[90mSKIP\033[0m"


def load_env() -> dict:
    """Minimal .env parser (no dependency). Looks in repo root then backend/."""
    env = dict(os.environ)
    here = Path(__file__).resolve()
    for cand in (here.parents[2] / ".env", here.parents[1] / ".env"):
        if cand.exists():
            for line in cand.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.split("#")[0].strip())
    return env


def pool(env: dict, name: str) -> list[str]:
    return [s.strip() for s in env.get(name, "").split(",") if s.strip()]


def _get(url: str, headers: dict) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read().decode("utf-8", "ignore")
            try:
                data = json.loads(body)
                n = len(data.get("data", data.get("models", []))) if isinstance(data, dict) else 0
                return True, f"{n} models" if n else "200"
            except Exception:
                return True, "200"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, type(e).__name__


# provider -> models endpoint (OpenAI-compatible, Bearer auth)
OAI = {
    "XAI_API_KEYS": "https://api.x.ai/v1/models",
    "NVIDIA_API_KEYS": "https://integrate.api.nvidia.com/v1/models",
    "GROQ_API_KEYS": "https://api.groq.com/openai/v1/models",
    "OPENROUTER_API_KEYS": "https://openrouter.ai/api/v1/models",
    "DEEPSEEK_API_KEYS": "https://api.deepseek.com/models",
}


def check_llm(env: dict) -> tuple[int, int]:
    ok = tested = 0
    print("\n== LLM providers (key pools) ==")
    for var, url in OAI.items():
        keys = pool(env, var)
        if not keys:
            print(f"  {SKIP} {var:<22} (empty)")
            continue
        for i, key in enumerate(keys, 1):
            tested += 1
            good, msg = _get(url, {"Authorization": f"Bearer {key}"})
            ok += good
            print(f"  {OK if good else FAIL} {var:<22} key#{i}  {msg}")
    # Gemini uses a different (Google) endpoint
    for i, key in enumerate(pool(env, "GEMINI_API_KEYS"), 1):
        tested += 1
        good, msg = _get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={urllib.parse.quote(key)}", {}
        )
        ok += good
        print(f"  {OK if good else FAIL} {'GEMINI_API_KEYS':<22} key#{i}  {msg}")
    if not pool(env, "GEMINI_API_KEYS"):
        print(f"  {SKIP} {'GEMINI_API_KEYS':<22} (empty)")
    return ok, tested


def check_misc(env: dict) -> None:
    """A few free live checks; the rest are reported as configured-only."""
    print("\n== Other live-tested keys ==")
    if env.get("GITHUB_TOKEN"):
        good, msg = _get("https://api.github.com/rate_limit", {"Authorization": f"Bearer {env['GITHUB_TOKEN']}"})
        print(f"  {OK if good else FAIL} GITHUB_TOKEN           {msg}")
    else:
        print(f"  {SKIP} GITHUB_TOKEN           (empty)")

    print("\n== Configured (paste-only; live test added when its adapter is built) ==")
    single = [
        "SEARXNG_BASE_URL", "GOOGLE_PSE_API_KEY", "REDDIT_CLIENT_ID", "ADZUNA_APP_ID",
        "JOOBLE_API_KEY", "USAJOBS_API_KEY", "PRODUCTHUNT_TOKEN", "YELP_API_KEY",
        "OPENCORPORATES_API_KEY", "COMPANIES_HOUSE_API_KEY", "MASTODON_ACCESS_TOKEN",
        "BLUESKY_APP_PASSWORD", "TELEGRAM_BOT_TOKEN", "DATA_GOV_API_KEY", "SAM_GOV_API_KEY",
        "NEWSAPI_KEY", "ZEROBOUNCE_API_KEY", "REOON_API_KEY", "MILLIONVERIFIER_API_KEY",
    ]
    for name in single:
        mark = "set " if env.get(name) else "----"
        print(f"  [{mark}] {name}")
    for name in ("TAVILY_API_KEYS",):
        mark = f"{len(pool(env, name))} key(s)" if pool(env, name) else "----"
        print(f"  [{mark}] {name}")


def main() -> int:
    env = load_env()
    ok, tested = check_llm(env)
    check_misc(env)
    print(f"\nLLM live checks: {ok}/{tested} keys OK.")
    if tested == 0:
        print("No LLM keys filled yet. Add at least one provider pool to .env, then re-run.")
        return 1
    print("Fill remaining pools any time and re-run — empties are skipped.")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
