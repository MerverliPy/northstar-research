import uuid
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.asyncio


class TestScrapingAPI:
    def _fake_source(self, pid, sid):
        return MagicMock(
            id=sid,
            project_id=pid,
            title="Mock Page",
            url="https://example.com",
            content_type="web",
            raw_content="Mock extracted text content",
            cleaned_content=None,
            metadata=None,
            word_count=5,
            created_at=MagicMock(),
            updated_at=MagicMock(),
        )

    async def test_scrape_returns_source(self, agent_client, mock_db):
        pid = uuid.uuid4()
        sid = uuid.uuid4()
        mock_db.get_project.return_value = MagicMock(id=pid, name="Test")
        mock_db.create_source.return_value = self._fake_source(pid, sid)

        response = await agent_client.post(
            "/api/v1/scraping/scrape",
            json={
                "project_id": str(pid),
                "url": "https://example.com",
                "title": "Test Page",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "source" in data
        assert data["title"] == "Mock Page"
        assert data["url"] == "https://example.com"
        assert data["word_count"] == 5

    async def test_scrape_404_missing_project(self, agent_client, mock_db):
        mock_db.get_project.return_value = None
        pid = uuid.uuid4()

        response = await agent_client.post(
            "/api/v1/scraping/scrape",
            json={
                "project_id": str(pid),
                "url": "https://example.com",
            },
        )
        assert response.status_code == 404

    async def test_scrape_400_bad_url(self, agent_client, mock_db, mock_scraper):
        mock_scraper.scrape.side_effect = ValueError("Unsupported URL scheme: ftp")
        mock_db.get_project.return_value = MagicMock(id=uuid.uuid4(), name="Test")

        pid = uuid.uuid4()
        response = await agent_client.post(
            "/api/v1/scraping/scrape",
            json={
                "project_id": str(pid),
                "url": "ftp://bad.com",
            },
        )
        assert response.status_code == 400

    async def test_scrape_503_scraper_not_enabled(self, agent_client, mock_db):
        mock_db.get_project.return_value = MagicMock(id=uuid.uuid4(), name="Test")
        with patch("research_agent.dependencies._scraper", None):
            pid = uuid.uuid4()
            response = await agent_client.post(
                "/api/v1/scraping/scrape",
                json={
                    "project_id": str(pid),
                    "url": "https://example.com",
                },
            )
            assert response.status_code == 503

    async def test_scrape_with_extract_triggers_background_task(
        self, agent_client, mock_db, mock_scraper
    ):
        pid = uuid.uuid4()
        sid = uuid.uuid4()
        mock_db.get_project.return_value = MagicMock(id=pid, name="Test")
        mock_db.create_source.return_value = self._fake_source(pid, sid)

        response = await agent_client.post(
            "/api/v1/scraping/scrape",
            json={
                "project_id": str(pid),
                "url": "https://example.com",
                "extract": True,
            },
        )
        assert response.status_code == 201

    async def test_scrape_with_fingerprint(self, agent_client, mock_db):
        pid = uuid.uuid4()
        sid = uuid.uuid4()
        mock_db.get_project.return_value = MagicMock(id=pid, name="Test")
        mock_db.create_source.return_value = self._fake_source(pid, sid)

        response = await agent_client.post(
            "/api/v1/scraping/scrape",
            json={
                "project_id": str(pid),
                "url": "https://example.com",
                "fingerprint": {
                    "seed": 12345,
                    "platform": "windows",
                    "viewport_width": 1920,
                    "viewport_height": 1080,
                },
            },
        )
        assert response.status_code == 201

    async def test_scrape_with_proxy(self, agent_client, mock_db):
        pid = uuid.uuid4()
        sid = uuid.uuid4()
        mock_db.get_project.return_value = MagicMock(id=pid, name="Test")
        mock_db.create_source.return_value = self._fake_source(pid, sid)

        response = await agent_client.post(
            "/api/v1/scraping/scrape",
            json={
                "project_id": str(pid),
                "url": "https://example.com",
                "proxy": {
                    "server": "http://proxy:8080",
                    "username": "user",
                    "password": "pass",
                },
            },
        )
        assert response.status_code == 201

    async def test_scrape_sets_content_type_web(self, agent_client, mock_db):
        pid = uuid.uuid4()
        sid = uuid.uuid4()
        mock_db.get_project.return_value = MagicMock(id=pid, name="Test")
        mock_db.create_source.return_value = self._fake_source(pid, sid)

        response = await agent_client.post(
            "/api/v1/scraping/scrape",
            json={
                "project_id": str(pid),
                "url": "https://example.com",
            },
        )
        assert response.status_code == 201

        created = mock_db.create_source.call_args[0][0]
        assert created.content_type == "web"
        assert created.url == "https://example.com"
