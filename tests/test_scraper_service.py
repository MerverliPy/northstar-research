import uuid
from unittest.mock import AsyncMock, patch

import pytest

from northstar_models import ScrapeRequest, ScraperFingerprint, ScraperProxy
from research_agent.services.scraper import WebScraper

pytestmark = pytest.mark.asyncio


class FakeSettings:
    scraper_enabled = True
    cloakbrowser_binary = None
    scraper_default_headless = True
    scraper_timeout_seconds = 60
    scraper_max_content_length = 10000
    scraper_url_allowlist = None


class TestWebScraperInit:
    async def test_initializes_when_enabled(self):
        with patch(
            "research_agent.services.scraper.WebScraper.initialize", AsyncMock()
        ):
            scraper = WebScraper(FakeSettings())
            assert scraper._enabled is True

    async def test_skips_init_when_disabled(self):
        settings = FakeSettings()
        settings.scraper_enabled = False
        scraper = WebScraper(settings)
        assert scraper._enabled is False


class TestWebScraperValidateUrl:
    def setup_method(self):
        self.scraper = WebScraper(FakeSettings())
        self.scraper._initialized = True

    async def test_accepts_http(self):
        assert self.scraper._validate_url("http://example.com") == "http://example.com"

    async def test_accepts_https(self):
        assert self.scraper._validate_url("https://example.com") == "https://example.com"

    async def test_rejects_ftp(self):
        with pytest.raises(ValueError, match="Unsupported URL scheme"):
            self.scraper._validate_url("ftp://example.com")

    async def test_rejects_domain_not_in_allowlist(self):
        self.scraper._allowlist = ["allowed.com"]
        with pytest.raises(ValueError, match="URL domain not in allowlist"):
            self.scraper._validate_url("https://evil.com")

    async def test_allows_domain_in_allowlist(self):
        self.scraper._allowlist = ["allowed.com"]
        url = self.scraper._validate_url("https://sub.allowed.com/page")
        assert url == "https://sub.allowed.com/page"


class TestWebScraperFingerprintArgs:
    def setup_method(self):
        self.scraper = WebScraper(FakeSettings())

    async def test_empty_when_no_fingerprint(self):
        assert self.scraper._build_fingerprint_args(None) == []

    async def test_sets_seed(self):
        fp = ScraperFingerprint(seed=12345)
        args = self.scraper._build_fingerprint_args(fp)
        assert "--fingerprint=12345" in args

    async def test_sets_platform(self):
        fp = ScraperFingerprint(platform="windows")
        args = self.scraper._build_fingerprint_args(fp)
        assert "--fingerprint-platform=windows" in args

    async def test_sets_viewport(self):
        fp = ScraperFingerprint(viewport_width=1920, viewport_height=1080)
        args = self.scraper._build_fingerprint_args(fp)
        assert "--fingerprint-screen-width=1920" in args
        assert "--fingerprint-screen-height=1080" in args

    async def test_sets_user_agent(self):
        fp = ScraperFingerprint(user_agent="Mozilla/5.0 Custom")
        args = self.scraper._build_fingerprint_args(fp)
        assert "--user-agent=Mozilla/5.0 Custom" in args


class TestWebScraperProxy:
    def setup_method(self):
        self.scraper = WebScraper(FakeSettings())

    async def test_none_when_no_proxy(self):
        assert self.scraper._build_proxy_config(None) is None

    async def test_simple_proxy(self):
        proxy = ScraperProxy(server="http://proxy:8080")
        config = self.scraper._build_proxy_config(proxy)
        assert config == {"server": "http://proxy:8080"}

    async def test_proxy_with_auth(self):
        proxy = ScraperProxy(server="http://proxy:8080", username="user", password="pass")
        config = self.scraper._build_proxy_config(proxy)
        assert config == {"server": "http://proxy:8080", "username": "user", "password": "pass"}


class TestWebScraperScrape:
    async def test_scrape_without_init_initializes(self):
        scraper = WebScraper(FakeSettings())
        req = ScrapeRequest(project_id=uuid.uuid4(), url="https://example.com")

        with patch.object(scraper, "initialize", AsyncMock()) as mock_init:
            with patch(
                "research_agent.services.scraper.WebScraper._validate_url",
                return_value="https://example.com",
            ):
                with patch(
                    "research_agent.services.scraper.WebScraper._build_fingerprint_args",
                    return_value=[],
                ):
                    with patch(
                        "research_agent.services.scraper.WebScraper._build_proxy_config",
                        return_value=None,
                    ):
                        with patch(
                            "cloakbrowser.launch_async", AsyncMock()
                        ) as mock_launch:
                            mock_browser = AsyncMock()
                            mock_page = AsyncMock()
                            mock_page.title = AsyncMock(return_value="Test Page")
                            mock_page.evaluate = AsyncMock(
                                return_value="Hello world content"
                            )
                            mock_page.goto = AsyncMock()
                            mock_browser.new_page = AsyncMock(return_value=mock_page)
                            mock_launch.return_value = mock_browser

                            result = await scraper.scrape(req)

                            assert result.title == "Test Page"
                            assert result.content == "Hello world content"
                            assert result.word_count == 3
                            mock_init.assert_called_once()

    async def test_scrape_calls_cloakbrowser(self):
        scraper = WebScraper(FakeSettings())
        scraper._initialized = True
        req = ScrapeRequest(project_id=uuid.uuid4(), url="https://example.com")

        with patch(
            "research_agent.services.scraper.WebScraper._validate_url",
            return_value="https://example.com",
        ):
            with patch(
                "research_agent.services.scraper.WebScraper._build_fingerprint_args",
                return_value=["--fingerprint=42"],
            ):
                with patch(
                    "research_agent.services.scraper.WebScraper._build_proxy_config",
                    return_value=None,
                ):
                    with patch(
                        "cloakbrowser.launch_async", AsyncMock()
                    ) as mock_launch:
                        mock_browser = AsyncMock()
                        mock_page = AsyncMock()
                        mock_page.title = AsyncMock(return_value="Test Page")
                        mock_page.evaluate = AsyncMock(
                            return_value="Hello world content"
                        )
                        mock_page.goto = AsyncMock()
                        mock_browser.new_page = AsyncMock(return_value=mock_page)
                        mock_launch.return_value = mock_browser

                        result = await scraper.scrape(req)

                        mock_launch.assert_called_once()
                        call_kwargs = mock_launch.call_args.kwargs
                        assert call_kwargs["headless"] is True
                        assert call_kwargs["proxy"] is None
                        assert "--fingerprint=42" in call_kwargs.get("args", [])
                        assert result.title == "Test Page"
                        assert result.word_count == 3
                        mock_page.goto.assert_called_once_with(
                            "https://example.com", wait_until="networkidle", timeout=60000
                        )

    async def test_scrape_closes_browser_in_finally_on_error(self):
        scraper = WebScraper(FakeSettings())
        scraper._initialized = True
        req = ScrapeRequest(project_id=uuid.uuid4(), url="https://example.com")

        with patch(
            "research_agent.services.scraper.WebScraper._validate_url",
            return_value="https://example.com",
        ):
            with patch(
                "research_agent.services.scraper.WebScraper._build_fingerprint_args",
                return_value=[],
            ):
                with patch(
                    "research_agent.services.scraper.WebScraper._build_proxy_config",
                    return_value=None,
                ):
                    with patch("cloakbrowser.launch_async", AsyncMock()) as mock_launch:
                        mock_browser = AsyncMock()
                        mock_page = AsyncMock()
                        mock_page.title = AsyncMock(return_value="Test Page")
                        mock_page.evaluate = AsyncMock(
                            return_value="Hello world content"
                        )
                        mock_page.goto = AsyncMock(
                            side_effect=Exception("Navigation failed")
                        )
                        mock_browser.new_page = AsyncMock(return_value=mock_page)
                        mock_launch.return_value = mock_browser

                        with pytest.raises(Exception, match="Navigation failed"):
                            await scraper.scrape(req)

                        mock_browser.close.assert_called_once()

    async def test_scrape_respects_max_content_length(self):
        scraper = WebScraper(FakeSettings())
        scraper._max_content_length = 10
        scraper._initialized = True
        req = ScrapeRequest(project_id=uuid.uuid4(), url="https://example.com")

        with patch(
            "research_agent.services.scraper.WebScraper._validate_url",
            return_value="https://example.com",
        ):
            with patch(
                "research_agent.services.scraper.WebScraper._build_fingerprint_args",
                return_value=[],
            ):
                with patch(
                    "research_agent.services.scraper.WebScraper._build_proxy_config",
                    return_value=None,
                ):
                    with patch("cloakbrowser.launch_async", AsyncMock()) as mock_launch:
                        mock_browser = AsyncMock()
                        mock_page = AsyncMock()
                        mock_page.title = AsyncMock(return_value="Test")
                        mock_page.evaluate = AsyncMock(
                            return_value="A" * 100
                        )
                        mock_page.goto = AsyncMock()
                        mock_browser.new_page = AsyncMock(return_value=mock_page)
                        mock_launch.return_value = mock_browser

                        result = await scraper.scrape(req)

                        assert len(result.content) == 10

    async def test_scrape_raises_runtime_error_when_disabled(self):
        settings = FakeSettings()
        settings.scraper_enabled = False
        scraper = WebScraper(settings)
        req = ScrapeRequest(project_id=uuid.uuid4(), url="https://example.com")

        with pytest.raises(RuntimeError, match="not enabled"):
            await scraper.scrape(req)

    async def test_scrape_with_proxy(self):
        scraper = WebScraper(FakeSettings())
        scraper._initialized = True
        req = ScrapeRequest(
            project_id=uuid.uuid4(),
            url="https://example.com",
            proxy=ScraperProxy(server="http://proxy:8080", username="u", password="p"),
        )

        with patch(
            "research_agent.services.scraper.WebScraper._validate_url",
            return_value="https://example.com",
        ):
            with patch(
                "research_agent.services.scraper.WebScraper._build_fingerprint_args",
                return_value=[],
            ):
                with patch("cloakbrowser.launch_async", AsyncMock()) as mock_launch:
                    mock_browser = AsyncMock()
                    mock_page = AsyncMock()
                    mock_page.title = AsyncMock(return_value="Test")
                    mock_page.evaluate = AsyncMock(return_value="content")
                    mock_page.goto = AsyncMock()
                    mock_browser.new_page = AsyncMock(return_value=mock_page)
                    mock_launch.return_value = mock_browser

                    result = await scraper.scrape(req)

                    assert result.title == "Test"
                    call_kwargs = mock_launch.call_args.kwargs
                    assert call_kwargs["proxy"] == {
                        "server": "http://proxy:8080",
                        "username": "u",
                        "password": "p",
                    }

    async def test_scrape_raises_on_missing_cloakbrowser(self):
        scraper = WebScraper(FakeSettings())
        scraper._initialized = True
        req = ScrapeRequest(project_id=uuid.uuid4(), url="https://example.com")

        with patch(
            "research_agent.services.scraper.WebScraper._validate_url",
            return_value="https://example.com",
        ):
            with patch(
                "research_agent.services.scraper.WebScraper._build_fingerprint_args",
                return_value=[],
            ):
                with patch(
                    "research_agent.services.scraper.WebScraper._build_proxy_config",
                    return_value=None,
                ):
                    with patch(
                        "cloakbrowser.launch_async",
                        side_effect=ImportError("no module named cloakbrowser"),
                    ):
                        with pytest.raises(
                            RuntimeError, match="CloakBrowser not available"
                        ):
                            await scraper.scrape(req)
