from __future__ import annotations

import asyncio
import json
import re
from typing import Any, TypeVar

import httpx
import structlog
from pydantic import BaseModel

from northstar_llm.cache import LLMResponseCache

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    pass


class LLMService:
    def __init__(
        self,
        primary_model: str = "qwen3:14b",
        fallback_model: str = "llama3.1:8b",
        ollama_base_url: str = "http://localhost:11434",
        timeout: int = 120,
    ):
        self._primary_model = primary_model
        self._fallback_model = fallback_model
        self._ollama_base_url = ollama_base_url.rstrip("/")
        self._timeout = timeout
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))
        self._cache = LLMResponseCache()

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        models_to_try = [self._primary_model, self._fallback_model]

        for model in models_to_try:
            cached = self._cache.get(prompt, model, system_prompt, temperature, max_tokens)
            if cached is not None:
                return cached

        last_error: Exception | None = None

        for model in models_to_try:
            for attempt in range(3):
                try:
                    response = await self._call_ollama(
                        model=model,
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    self._cache.set(prompt, model, response, system_prompt, temperature, max_tokens)
                    return response
                except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as exc:
                    logger.warning(
                        "llm_attempt_failed",
                        model=model,
                        attempt=attempt + 1,
                        error=str(exc),
                    )
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        last_error = exc
                        break
                except Exception as exc:
                    logger.warning(
                        "llm_model_failed",
                        model=model,
                        error=str(exc),
                        falling_back=(model == self._primary_model),
                    )
                    last_error = exc
                    break

        raise LLMError(
            f"Both primary ({self._primary_model}) and fallback ({self._fallback_model}) models failed"
        ) from last_error

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str | None,
        response_model: type[T],
    ) -> T:
        text = await self.generate(prompt, system_prompt=system_prompt)

        try:
            parsed = json.loads(text)
            return response_model.model_validate(parsed)
        except (json.JSONDecodeError, ValueError):
            pass

        json_block = re.search(
            r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL
        )
        if json_block:
            try:
                parsed = json.loads(json_block.group(1))
                return response_model.model_validate(parsed)
            except (json.JSONDecodeError, ValueError):
                pass

        raise LLMError(
            f"Could not parse structured output from model response for {response_model.__name__}"
        )

    async def is_available(self, model: str | None = None) -> bool:
        target = model or self._primary_model
        try:
            response = await self._client.get(
                f"{self._ollama_base_url}/api/tags"
            )
            response.raise_for_status()
            data = response.json()
            models = data.get("models", [])
            return any(m.get("name") == target for m in models)
        except Exception:
            return False

    async def _call_ollama(
        self,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system_prompt is not None:
            payload["system"] = system_prompt

        response = await self._client.post(
            f"{self._ollama_base_url}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    async def close(self) -> None:
        if self._cache:
            self._cache.close()
        await self._client.aclose()

    async def __aenter__(self) -> LLMService:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()


class EmbeddingService:
    def __init__(
        self,
        model: str = "nomic-embed-text",
        ollama_base_url: str = "http://localhost:11434",
    ):
        self._model = model
        self._ollama_base_url = ollama_base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))

    async def embed(self, text: str) -> list[float]:
        payload = {
            "model": self._model,
            "input": text,
        }
        response = await self._client.post(
            f"{self._ollama_base_url}/api/embed",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings", [])
        if not embeddings:
            raise LLMError(f"Empty embedding response for model {self._model}")
        return embeddings[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        payload = {
            "model": self._model,
            "input": texts,
        }
        response = await self._client.post(
            f"{self._ollama_base_url}/api/embed",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("embeddings", [])

    async def embed_dimension(self) -> int:
        test = await self.embed("test")
        return len(test)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> EmbeddingService:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
