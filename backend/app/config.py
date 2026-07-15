"""Central config. Loads env (incl. comma-separated LLM key pools). vibe rule 1: secrets from env only."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# .env lives at repo root (backend/app/config.py -> parents[2]); backend/.env as fallback
_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILES = (str(_ROOT / ".env"), str(_ROOT / "backend" / ".env"))

# NoDecode: stop pydantic-settings JSON-decoding these; we comma-split ourselves
KeyPoolField = Annotated[list[str], NoDecode]


def _split(v: str | list[str] | None) -> list[str]:
    """'k1,k2, k3' -> ['k1','k2','k3']; '' -> []. Lets each provider hold N keys."""
    if not v:
        return []
    if isinstance(v, list):
        return [s.strip() for s in v if s and s.strip()]
    return [s.strip() for s in str(v).split(",") if s.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILES, env_file_encoding="utf-8", extra="ignore")

    # app / infra
    APP_ENV: str = "development"
    SECRET_KEY: str = ""
    API_TOKEN: str = ""            # bearer token for mutating endpoints; "" = auth off (local dev)
    DATABASE_URL: str = "sqlite:///./dev.db"
    REDIS_URL: str = ""
    ALLOWED_ORIGIN: str = "http://localhost:3000"
    MAX_TOKENS_PER_CALL: int = 2000
    USER_DAILY_TOKEN_BUDGET: int = 200_000
    USER_DAILY_RUN_LIMIT: int = 20

    # tuning knobs (all optional; defaults match previous hardcoded values)
    CARD_WORKERS: int = 4                  # parallel card builders in the pipeline
    SCOUT_MAX_WORKERS: int = 10            # parallel source queries
    SCOUT_PER_QUERY_LIMIT: int = 8         # results per (source, query)
    SCOUT_MAX_QUERIES_PER_SOURCE: int = 6
    SCOUT_MAX_LOCATIONS: int = 3           # locations looped by local adapters
    QUALIFIER_BATCH_SIZE: int = 20         # leads per scoring LLM call
    QUALIFIER_MAX_CANDIDATES: int = 100    # hard cap on candidates scored
    QUALIFIER_MIN_FIT: float = 4.0         # drop leads scored below this
    PRIORITY_MIN_FIT: float = 7.0          # "contact first" threshold
    LLM_TIMEOUT: float = 60.0
    LLM_TEMPERATURE: float = 0.3
    SOURCE_TIMEOUT: float = 20.0           # per-source HTTP timeout
    FETCH_TIMEOUT: float = 15.0            # SSRF-guarded page fetch timeout
    MAX_FETCH_BYTES: int = 500_000
    KEY_COOLDOWN_SECONDS: float = 60.0     # bench time for a failing LLM key
    RATE_LIMIT_PER_MIN: int = 120          # general per-IP limit
    RUN_CREATES_PER_MIN: int = 10          # per-IP POST /api/runs limit

    # LLM provider key POOLS (multi-key failover)
    XAI_API_KEYS: KeyPoolField = Field(default_factory=list)
    NVIDIA_API_KEYS: KeyPoolField = Field(default_factory=list)
    GROQ_API_KEYS: KeyPoolField = Field(default_factory=list)
    OPENROUTER_API_KEYS: KeyPoolField = Field(default_factory=list)
    DEEPSEEK_API_KEYS: KeyPoolField = Field(default_factory=list)
    GEMINI_API_KEYS: KeyPoolField = Field(default_factory=list)
    LLM_MODEL_CHEAP: str = ""
    LLM_MODEL_BIG: str = ""

    # Tier A search
    SEARXNG_BASE_URL: str = ""
    TAVILY_API_KEYS: KeyPoolField = Field(default_factory=list)
    GOOGLE_PSE_API_KEY: str = ""
    GOOGLE_PSE_CX: str = ""

    # Tier B-H single keys (add pools later if a source gets rate-limited)
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "leadfinder/0.1"
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    JOOBLE_API_KEY: str = ""
    USAJOBS_API_KEY: str = ""
    USAJOBS_EMAIL: str = ""
    GITHUB_TOKEN: str = ""
    PRODUCTHUNT_TOKEN: str = ""
    OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
    NOMINATIM_USER_AGENT: str = "leadfinder/0.1"
    YELP_API_KEY: str = ""
    OPENCORPORATES_API_KEY: str = ""
    COMPANIES_HOUSE_API_KEY: str = ""
    SEC_USER_AGENT: str = "leadfinder"
    MASTODON_INSTANCE: str = ""
    MASTODON_ACCESS_TOKEN: str = ""
    BLUESKY_IDENTIFIER: str = ""
    BLUESKY_APP_PASSWORD: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    DATA_GOV_API_KEY: str = ""
    SAM_GOV_API_KEY: str = ""
    NEWSAPI_KEY: str = ""
    ZEROBOUNCE_API_KEY: str = ""
    REOON_API_KEY: str = ""
    MILLIONVERIFIER_API_KEY: str = ""

    @field_validator(
        "XAI_API_KEYS", "NVIDIA_API_KEYS", "GROQ_API_KEYS", "OPENROUTER_API_KEYS",
        "DEEPSEEK_API_KEYS", "GEMINI_API_KEYS", "TAVILY_API_KEYS", mode="before",
    )
    @classmethod
    def _parse_pools(cls, v):
        return _split(v)


@lru_cache
def get_settings() -> Settings:
    return Settings()
