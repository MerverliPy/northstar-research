import hashlib
import os
from pathlib import Path

import structlog
from diskcache import Cache

logger = structlog.get_logger(__name__)


class LLMResponseCache:
    def __init__(self, cache_dir: str = "~/.cache/northstar/llm", ttl: int = 86400):
        resolved = os.path.expanduser(cache_dir)
        Path(resolved).mkdir(parents=True, exist_ok=True)
        self._cache = Cache(resolved)
        self._ttl = ttl

    def _key(
        self,
        prompt: str,
        model: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        raw = f"{prompt}|||{model}|||{system_prompt or ''}|||{temperature}|||{max_tokens}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(
        self,
        prompt: str,
        model: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str | None:
        key = self._key(prompt, model, system_prompt, temperature, max_tokens)
        value = self._cache.get(key)
        if value is not None:
            logger.debug("llm_cache_hit", model=model)
        return value

    def set(
        self,
        prompt: str,
        model: str,
        response: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> None:
        key = self._key(prompt, model, system_prompt, temperature, max_tokens)
        self._cache.set(key, response, expire=self._ttl)
        logger.debug("llm_cache_set", model=model)

    def clear(self) -> None:
        self._cache.clear()
        logger.debug("llm_cache_cleared")

    def size(self) -> int:
        return len(self._cache)

    def close(self) -> None:
        self._cache.close()
        logger.debug("llm_cache_closed")
