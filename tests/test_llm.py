import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from northstar_llm.cache import LLMResponseCache
from northstar_llm.service import EmbeddingService, LLMError, LLMService

pytestmark = pytest.mark.asyncio


class TestLLMServiceConfig:
    def test_default_config(self):
        svc = LLMService()
        assert svc._primary_model == "qwen3:14b"
        assert svc._fallback_model == "llama3.1:8b"
        assert svc._ollama_base_url == "http://localhost:11434"
        assert svc._timeout == 120

    def test_custom_config(self):
        svc = LLMService(
            primary_model="custom:latest",
            fallback_model="backup:latest",
            ollama_base_url="http://ollama:11434",
            timeout=60,
        )
        assert svc._primary_model == "custom:latest"
        assert svc._fallback_model == "backup:latest"
        assert svc._ollama_base_url == "http://ollama:11434"
        assert svc._timeout == 60

    def test_url_trailing_slash_stripped(self):
        svc = LLMService(ollama_base_url="http://localhost:11434/")
        assert svc._ollama_base_url == "http://localhost:11434"

    def test_cache_initialized(self):
        svc = LLMService()
        assert svc._cache is not None


class TestLLMResponseCache:
    def test_set_and_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(cache_dir=tmpdir, ttl=3600)
            cache.set("hello", "model1", "world")
            result = cache.get("hello", "model1")
            assert result == "world"

    def test_get_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(cache_dir=tmpdir)
            result = cache.get("nonexistent", "model1")
            assert result is None

    def test_get_wrong_model(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(cache_dir=tmpdir)
            cache.set("hello", "model1", "world")
            result = cache.get("hello", "model2")
            assert result is None

    def test_clear(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(cache_dir=tmpdir)
            cache.set("a", "m1", "1")
            cache.set("b", "m1", "2")
            cache.clear()
            assert cache.get("a", "m1") is None
            assert cache.get("b", "m1") is None

    def test_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(cache_dir=tmpdir)
            assert cache.size() == 0
            cache.set("a", "m1", "1")
            assert cache.size() == 1
            cache.set("b", "m1", "2")
            assert cache.size() == 2

    def test_ttl_expiry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(cache_dir=tmpdir, ttl=0)
            cache.set("a", "m1", "1")
            import time
            time.sleep(0.1)
            result = cache.get("a", "m1")
            assert result is None

    def test_key_uniqueness(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(cache_dir=tmpdir)
            cache.set("same", "model_a", "response_a")
            cache.set("same", "model_b", "response_b")
            assert cache.get("same", "model_a") == "response_a"
            assert cache.get("same", "model_b") == "response_b"


class TestLLMServiceGenerate:
    async def test_generate_success(self):
        import tempfile
        svc = LLMService(ollama_base_url="http://test:11434")
        svc._cache = LLMResponseCache(cache_dir=tempfile.mkdtemp(), ttl=1)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "Hello world"}

        svc._client.post = AsyncMock(return_value=mock_resp)
        result = await svc.generate("Say hello")
        assert result == "Hello world"

    async def test_generate_fallback(self):
        import tempfile
        svc = LLMService(
            primary_model="primary",
            fallback_model="fallback",
            ollama_base_url="http://test:11434",
        )
        svc._cache = LLMResponseCache(cache_dir=tempfile.mkdtemp(), ttl=1)

        call_count = [0]

        async def mock_post(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                resp = MagicMock()
                resp.status_code = 500
                resp.is_error = True
                raise httpx.HTTPStatusError(
                    "Primary failed",
                    request=MagicMock(),
                    response=resp,
                )
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"response": "fallback ok"}
            return mock_resp

        svc._client.post = mock_post
        result = await svc.generate("Hello")
        assert result == "fallback ok"
        assert call_count[0] == 2

    async def test_generate_both_fail(self):
        import tempfile
        svc = LLMService(
            primary_model="primary",
            fallback_model="fallback",
            ollama_base_url="http://test:11434",
        )
        svc._cache = LLMResponseCache(cache_dir=tempfile.mkdtemp(), ttl=1)

        async def mock_post(*args, **kwargs):
            resp = MagicMock()
            resp.status_code = 500
            resp.is_error = True
            raise httpx.HTTPStatusError(
                "fail",
                request=MagicMock(),
                response=resp,
            )

        svc._client.post = mock_post
        with pytest.raises(LLMError):
            await svc.generate("Hello")

    async def test_generate_uses_cache(self):
        import tempfile
        svc = LLMService(ollama_base_url="http://test:11434")
        svc._cache = LLMResponseCache(cache_dir=tempfile.mkdtemp(), ttl=3600)
        svc._cache.set("hello", svc._primary_model, "cached response")

        called = False

        async def mock_post(*args, **kwargs):
            nonlocal called
            called = True
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"response": "live"}
            return mock_resp

        svc._client.post = mock_post
        result = await svc.generate("hello")
        assert result == "cached response"
        assert not called


class TestLLMServiceGenerateStructured:
    async def test_generate_structured_parses_json(self):
        import tempfile
        svc = LLMService(ollama_base_url="http://test:11434")
        svc._cache = LLMResponseCache(cache_dir=tempfile.mkdtemp(), ttl=1)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": '{"score": 0.9, "reasoning": "good"}'}
        svc._client.post = AsyncMock(return_value=mock_resp)

        class FakeModel:
            def __init__(self, **kwargs):
                self.score = kwargs.get("score")
                self.reasoning = kwargs.get("reasoning")

            @classmethod
            def model_validate(cls, data):
                return cls(**data)

        result = await svc.generate_structured(
            "test_a", system_prompt=None, response_model=FakeModel
        )
        assert result.score == 0.9
        assert result.reasoning == "good"

    async def test_generate_structured_parses_json_block(self):
        import tempfile
        svc = LLMService(ollama_base_url="http://test:11434")
        svc._cache = LLMResponseCache(cache_dir=tempfile.mkdtemp(), ttl=1)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": "Here is the result:\n```json\n{\"score\": 0.8}\n```"
        }
        svc._client.post = AsyncMock(return_value=mock_resp)

        class FakeModel:
            def __init__(self, **kwargs):
                self.score = kwargs.get("score")

            @classmethod
            def model_validate(cls, data):
                return cls(**data)

        result = await svc.generate_structured(
            "test_b", system_prompt=None, response_model=FakeModel
        )
        assert result.score == 0.8

    async def test_generate_structured_fails_on_bad_json(self):
        import tempfile
        svc = LLMService(ollama_base_url="http://test:11434")
        svc._cache = LLMResponseCache(cache_dir=tempfile.mkdtemp(), ttl=1)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "not json at all"}
        svc._client.post = AsyncMock(return_value=mock_resp)

        class FakeModel:
            def __init__(self, **kwargs):
                self.score = kwargs.get("score")

            @classmethod
            def model_validate(cls, data):
                return cls(**data)

        with pytest.raises(LLMError):
            await svc.generate_structured(
                "test_c", system_prompt=None, response_model=FakeModel
            )


class TestLLMServiceIsAvailable:
    async def test_is_available_true(self):
        svc = LLMService(ollama_base_url="http://test:11434")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "qwen3:14b"}]}
        svc._client.get = AsyncMock(return_value=mock_resp)
        result = await svc.is_available("qwen3:14b")
        assert result is True

    async def test_is_available_false(self):
        svc = LLMService(ollama_base_url="http://test:11434")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "other"}]}
        svc._client.get = AsyncMock(return_value=mock_resp)
        result = await svc.is_available("qwen3:14b")
        assert result is False

    async def test_is_available_on_error(self):
        svc = LLMService(ollama_base_url="http://test:11434")

        svc._client.get = AsyncMock(side_effect=httpx.RequestError("connection failed"))
        result = await svc.is_available()
        assert result is False


class TestEmbeddingService:
    async def test_default_config(self):
        svc = EmbeddingService()
        assert svc._model == "nomic-embed-text"
        assert svc._ollama_base_url == "http://localhost:11434"

    async def test_custom_config(self):
        svc = EmbeddingService(model="custom-model", ollama_base_url="http://custom:11434")
        assert svc._model == "custom-model"
        assert svc._ollama_base_url == "http://custom:11434"

    async def test_embed_success(self):
        svc = EmbeddingService(ollama_base_url="http://test:11434")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
        svc._client.post = AsyncMock(return_value=mock_resp)
        result = await svc.embed("hello")
        assert result == [0.1, 0.2, 0.3]

    async def test_embed_empty_response(self):
        svc = EmbeddingService(ollama_base_url="http://test:11434")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"embeddings": []}
        svc._client.post = AsyncMock(return_value=mock_resp)
        with pytest.raises(LLMError):
            await svc.embed("hello")

    async def test_embed_batch(self):
        svc = EmbeddingService(ollama_base_url="http://test:11434")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"embeddings": [[0.1, 0.2], [0.3, 0.4]]}
        svc._client.post = AsyncMock(return_value=mock_resp)
        result = await svc.embed_batch(["a", "b"])
        assert len(result) == 2

    async def test_embed_dimension(self):
        svc = EmbeddingService(ollama_base_url="http://test:11434")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"embeddings": [[0.1] * 768]}
        svc._client.post = AsyncMock(return_value=mock_resp)
        dim = await svc.embed_dimension()
        assert dim == 768


class TestLLMServiceContextManager:
    async def test_async_context_manager(self):
        svc = LLMService(ollama_base_url="http://test:11434")
        svc._client.aclose = AsyncMock()
        async with svc as s:
            assert s is svc
        svc._client.aclose.assert_awaited_once()
