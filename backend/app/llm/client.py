"""Model-agnostic LLM client. Key pools + provider failover so a run never dies.

- OpenAI-compatible providers (xai/nvidia/groq/openrouter/deepseek) + Gemini.
- Rotates keys inside a provider (429/quota -> bench key), then fails over to
  the next configured provider. vibe 13/28/29.
- Verifies model ids against the provider's live /models list (self-healing).
"""
from __future__ import annotations

import json
import re
from typing import Optional

import httpx

from ..config import get_settings
from .key_pool import PoolRegistry

TIMEOUT = 60.0

# provider -> (chat endpoint, models endpoint)
OAI_PROVIDERS = {
    "xai": ("https://api.x.ai/v1/chat/completions", "https://api.x.ai/v1/models"),
    "nvidia": ("https://integrate.api.nvidia.com/v1/chat/completions", "https://integrate.api.nvidia.com/v1/models"),
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "https://api.groq.com/openai/v1/models"),
    "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "https://openrouter.ai/api/v1/models"),
    "deepseek": ("https://api.deepseek.com/chat/completions", "https://api.deepseek.com/models"),
}
POOL_VARS = {
    "xai": "XAI_API_KEYS", "nvidia": "NVIDIA_API_KEYS", "groq": "GROQ_API_KEYS",
    "openrouter": "OPENROUTER_API_KEYS", "deepseek": "DEEPSEEK_API_KEYS", "gemini": "GEMINI_API_KEYS",
}


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self) -> None:
        s = get_settings()
        self.settings = s
        self.pools = PoolRegistry({p: getattr(s, v) for p, v in POOL_VARS.items()})
        self._model_cache: dict[str, list[str]] = {}

    # ── public API ──────────────────────────────────────────────────────────
    def chat(self, prompt: str, *, system: str = "", tier: str = "cheap",
             max_tokens: Optional[int] = None, json_mode: bool = False) -> str:
        """tier: 'cheap' (scout/validate) or 'big' (diagnosis/pitch)."""
        want = self.settings.LLM_MODEL_CHEAP if tier == "cheap" else self.settings.LLM_MODEL_BIG
        max_tokens = min(max_tokens or self.settings.MAX_TOKENS_PER_CALL, self.settings.MAX_TOKENS_PER_CALL)
        order = self._provider_order(want)
        errors: list[str] = []
        for provider in order:
            pool = self.pools.get(provider)
            if not pool:
                continue
            model = self._resolve_model(provider, want)
            for _ in range(len(pool)):
                key = pool.acquire()
                if not key:
                    break
                try:
                    out = (self._chat_gemini if provider == "gemini" else self._chat_oai)(
                        provider, key, model, prompt, system, max_tokens, json_mode)
                    pool.report(key, ok=True)
                    return out
                except httpx.HTTPStatusError as e:
                    retriable = e.response.status_code in (401, 402, 403, 429, 500, 502, 503)
                    pool.report(key, ok=False)
                    errors.append(f"{provider}:{e.response.status_code}")
                    if not retriable:
                        break
                except Exception as e:  # noqa: BLE001 — network problems: bench key, keep going
                    pool.report(key, ok=False)
                    errors.append(f"{provider}:{type(e).__name__}")
        raise LLMError(f"All LLM providers failed ({', '.join(errors) or 'no keys configured'}). "
                       f"Check .env pools + run validate_keys.py")

    def chat_json(self, prompt: str, *, system: str = "", tier: str = "cheap",
                  max_tokens: Optional[int] = None) -> dict | list:
        raw = self.chat(prompt, system=system + "\nRespond with valid JSON only.",
                        tier=tier, max_tokens=max_tokens, json_mode=True)
        try:
            return extract_json(raw)
        except (json.JSONDecodeError, ValueError):
            # one strict retry — open models occasionally emit broken JSON
            raw = self.chat(prompt, system=system + "\nReturn ONLY a valid JSON object/array. "
                            "No prose, no markdown fences, no trailing commas.",
                            tier=tier, max_tokens=max_tokens, json_mode=True)
            return extract_json(raw)

    # ── internals ───────────────────────────────────────────────────────────
    def _provider_order(self, want: str) -> list[str]:
        preferred = want.split("/", 1)[0] if want else ""
        avail = self.pools.available_providers()
        return ([preferred] if preferred in avail else []) + [p for p in avail if p != preferred]

    def _resolve_model(self, provider: str, want: str) -> str:
        """Use the wanted model if the provider actually serves it; else pick live one. vibe 29."""
        wanted = want.split("/", 1)[1] if want.startswith(provider + "/") else ""
        models = self._models(provider)
        if wanted and (not models or wanted in models):
            return wanted
        if models:
            for pat in ("instruct", "chat", "flash", "mini", "grok", "llama"):
                hit = next((m for m in models if pat in m.lower()), None)
                if hit:
                    return hit
            return models[0]
        return wanted or "auto"

    def _models(self, provider: str) -> list[str]:
        if provider in self._model_cache:
            return self._model_cache[provider]
        ids: list[str] = []
        try:
            key = self.pools.get(provider).acquire()
            if key:
                if provider == "gemini":
                    r = httpx.get("https://generativelanguage.googleapis.com/v1beta/models",
                                  params={"key": key}, timeout=20)
                    ids = [m["name"].split("/")[-1] for m in r.json().get("models", [])
                           if "generateContent" in m.get("supportedGenerationMethods", [])]
                else:
                    r = httpx.get(OAI_PROVIDERS[provider][1],
                                  headers={"Authorization": f"Bearer {key}"}, timeout=20)
                    ids = [m["id"] for m in r.json().get("data", [])]
        except Exception:  # noqa: BLE001 — cache empty list; resolve falls back to wanted id
            pass
        self._model_cache[provider] = ids
        return ids

    def _chat_oai(self, provider: str, key: str, model: str, prompt: str,
                  system: str, max_tokens: int, json_mode: bool) -> str:
        body: dict = {
            "model": model,
            "messages": ([{"role": "system", "content": system}] if system else [])
                        + [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        if json_mode and provider in ("openrouter", "groq", "deepseek"):
            body["response_format"] = {"type": "json_object"}
        r = httpx.post(OAI_PROVIDERS[provider][0], json=body, timeout=TIMEOUT,
                       headers={"Authorization": f"Bearer {key}"})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"] or ""

    def _chat_gemini(self, provider: str, key: str, model: str, prompt: str,
                     system: str, max_tokens: int, json_mode: bool) -> str:
        model = model or "gemini-2.0-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        body = {"contents": [{"parts": [{"text": (system + "\n\n" if system else "") + prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.3}}
        r = httpx.post(url, params={"key": key}, json=body, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def extract_json(text: str) -> dict | list:
    """Tolerant JSON extractor (open models wrap JSON in prose/fences, add trailing commas)."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    for attempt in (text, re.sub(r",\s*([}\]])", r"\1", text)):
        try:
            return json.loads(attempt)
        except json.JSONDecodeError:
            pass
    m = re.search(r"[\[{].*[\]}]", text, re.DOTALL)
    if m:
        blob = m.group(0)
        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            return json.loads(re.sub(r",\s*([}\]])", r"\1", blob))
    raise json.JSONDecodeError("no JSON found in model output", text[:80], 0)


_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
