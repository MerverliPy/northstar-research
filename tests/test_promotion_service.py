from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from chat_import_bridge.services.promotion import promote_to_agent, promote_all_pending

pytestmark = pytest.mark.asyncio


class FakeStagedEntry:
    id = 1
    title = "Test Import"
    source_type = "chat"
    status = "pending"
    raw_content = "raw content"
    cleaned_content = "cleaned text"


class FakePromotedEntry:
    id = 2
    title = "Already Import"
    source_type = "chat"
    status = "promoted"
    raw_content = "raw"
    cleaned_content = None


@pytest.fixture
def mock_staging():
    with patch("chat_import_bridge.services.promotion.svc") as svc:
        svc.get_staged = AsyncMock(return_value=FakeStagedEntry())
        svc.update_status = AsyncMock()
        yield svc


@pytest.fixture
def mock_staging_promoted():
    with patch("chat_import_bridge.services.promotion.svc") as svc:
        svc.get_staged = AsyncMock(return_value=FakePromotedEntry())
        yield svc


class TestPromoteToAgent:
    async def test_successful_promotion(self, mock_staging):
        resp = MagicMock()
        resp.status_code = 201
        resp.json = MagicMock(return_value={"id": "new-source-id"})
        resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            result = await promote_to_agent("http://127.0.0.1:8099", 1, AsyncMock())
            assert result["status"] == "promoted"
            assert result["source_id"] == "new-source-id"
            assert result["error"] is None

    async def test_already_promoted(self, mock_staging_promoted):
        result = await promote_to_agent("http://127.0.0.1:8099", 2, AsyncMock())
        assert result["status"] == "skipped"
        assert "Already promoted" in result["error"]

    async def test_import_not_found(self):
        with patch("chat_import_bridge.services.promotion.svc") as svc:
            svc.get_staged = AsyncMock(return_value=None)
            result = await promote_to_agent("http://127.0.0.1:8099", 999, AsyncMock())
            assert result["status"] == "failed"
            assert "not found" in result["error"].lower()

    async def test_http_error(self, mock_staging):
        error_resp = MagicMock()
        error_resp.status_code = 500
        error_resp.text = "Internal Server Error"
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=error_resp
        ))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await promote_to_agent("http://127.0.0.1:8099", 1, AsyncMock())
            assert result["status"] == "failed"
            assert result["error"]

    async def test_network_error(self, mock_staging):
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("no connection"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await promote_to_agent("http://127.0.0.1:8099", 1, AsyncMock())
            assert result["status"] == "failed"


class TestPromoteAllPending:
    async def test_batch_promotion(self):
        entry1 = FakeStagedEntry()
        entry2 = FakeStagedEntry()
        entry2.id = 2

        with patch("chat_import_bridge.services.promotion.svc") as svc, \
             patch("chat_import_bridge.services.promotion.promote_to_agent") as mock_promote:
            svc.list_staged = AsyncMock(return_value=[entry1, entry2])
            mock_promote.side_effect = [
                {"status": "promoted", "source_id": "s1", "error": None},
                {"status": "failed", "source_id": None, "error": "timeout"},
            ]

            result = await promote_all_pending("http://127.0.0.1:8099", AsyncMock())
            assert result["total"] == 2
            assert result["succeeded"] == 1
            assert result["failed"] == 1
