"""LLM key pool: rotate across N keys per provider, fail over on 429/quota/error.

So one dead/exhausted key never breaks an LLM run. Round-robin + cooldown.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from ..config import get_settings


@dataclass
class _Key:
    value: str
    cooldown_until: float = 0.0        # epoch secs; >now = temporarily benched
    fails: int = 0


@dataclass
class KeyPool:
    """One provider's keys. Thread-safe. `acquire()` -> a usable key or None."""
    provider: str
    _keys: list[_Key] = field(default_factory=list)
    _idx: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    @classmethod
    def from_list(cls, provider: str, keys: list[str]) -> KeyPool:
        return cls(provider=provider, _keys=[_Key(k) for k in keys])

    def __bool__(self) -> bool:
        return len(self._keys) > 0

    def __len__(self) -> int:
        return len(self._keys)

    def acquire(self) -> str | None:
        """Next available key (round-robin), skipping cooling-down ones."""
        now = time.time()
        with self._lock:
            n = len(self._keys)
            for _ in range(n):
                k = self._keys[self._idx % n]
                self._idx += 1
                if k.cooldown_until <= now:
                    return k.value
            return None  # all cooling down -> caller should back off / try another provider

    def report(self, key: str, ok: bool, cooldown: float | None = None) -> None:
        """Feed back the result so bad keys get benched, good ones reset."""
        if cooldown is None:
            cooldown = get_settings().KEY_COOLDOWN_SECONDS
        with self._lock:
            for k in self._keys:
                if k.value == key:
                    if ok:
                        k.fails = 0
                    else:
                        k.fails += 1
                        k.cooldown_until = time.time() + cooldown * min(k.fails, 5)
                    return


class PoolRegistry:
    """All provider pools. LLMClient (llm/client.py) asks here for keys and reports results."""

    def __init__(self, pools: dict[str, list[str]]):
        self.pools: dict[str, KeyPool] = {
            name: KeyPool.from_list(name, keys) for name, keys in pools.items()
        }

    def get(self, provider: str) -> KeyPool:
        return self.pools.get(provider, KeyPool(provider))

    def available_providers(self) -> list[str]:
        return [name for name, pool in self.pools.items() if pool]
