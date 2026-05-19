import time
from urllib.parse import urlparse

import structlog

from northstar_models import ScrapeRequest

logger = structlog.get_logger(__name__)


class ScrapeResult:
    def __init__(
        self,
        url: str,
        title: str,
        content: str,
        word_count: int,
        fingerprint_seed: int | None,
        took_ms: int,
    ) -> None:
        self.url = url
        self.title = title
        self.content = content
        self.word_count = word_count
        self.fingerprint_seed = fingerprint_seed
        self.took_ms = took_ms


class WebScraper:
    def __init__(self, settings) -> None:
        self._enabled = settings.scraper_enabled
        self._binary = settings.cloakbrowser_binary
        self._default_headless = settings.scraper_default_headless
        self._timeout = settings.scraper_timeout_seconds
        self._max_content_length = settings.scraper_max_content_length
        self._allowlist = settings.scraper_url_allowlist
        self._initialized = False

    async def initialize(self) -> None:
        if not self._enabled:
            logger.info("scraper_disabled_skipping_init")
            return
        try:
            from cloakbrowser.download import ensure_binary

            if self._binary:
                logger.info("cloakbrowser_binary_specified", path=self._binary)
            else:
                path = ensure_binary()
                logger.info("cloakbrowser_binary_ready", path=path)
            self._initialized = True
            logger.info("scraper_initialized")
        except ImportError:
            logger.warning("cloakbrowser_not_installed_install_with_scraper_extra")
        except Exception as exc:
            logger.error("cloakbrowser_download_failed", error=str(exc))

    def _validate_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
        if self._allowlist:
            host = parsed.hostname
            if host and not any(host.endswith(a) for a in self._allowlist):
                raise ValueError(f"URL domain not in allowlist: {host}")
        return url

    def _build_fingerprint_args(self, fingerprint) -> list[str]:
        args = []
        if fingerprint is None:
            return args
        if fingerprint.seed is not None:
            args.append(f"--fingerprint={fingerprint.seed}")
        if fingerprint.platform:
            args.append(f"--fingerprint-platform={fingerprint.platform}")
        if fingerprint.viewport_width:
            args.append(f"--fingerprint-screen-width={fingerprint.viewport_width}")
        if fingerprint.viewport_height:
            args.append(f"--fingerprint-screen-height={fingerprint.viewport_height}")
        if fingerprint.hardware_concurrency:
            args.append(f"--fingerprint-hardware-concurrency={fingerprint.hardware_concurrency}")
        if fingerprint.user_agent:
            args.append(f"--user-agent={fingerprint.user_agent}")
        return args

    def _build_proxy_config(self, proxy) -> dict | None:
        if proxy is None:
            return None
        if proxy.username and proxy.password:
            return {
                "server": proxy.server,
                "username": proxy.username,
                "password": proxy.password,
            }
        return {"server": proxy.server}

    async def scrape(self, req: ScrapeRequest) -> ScrapeResult:
        if not self._enabled:
            raise RuntimeError("Web scraper is not enabled")

        if not self._initialized:
            await self.initialize()

        url = self._validate_url(req.url)
        headless = req.headless if req.headless is not None else self._default_headless
        proxy_config = self._build_proxy_config(req.proxy)
        fingerprint_args = self._build_fingerprint_args(req.fingerprint)

        browser = None
        start = time.monotonic()

        try:
            from cloakbrowser import launch_async

            args = list(fingerprint_args)
            browser = await launch_async(
                headless=headless,
                proxy=proxy_config,
                args=args,
            )

            page = await browser.new_page()

            wait_map = {
                "domcontentloaded": "domcontentloaded",
                "load": "load",
                "networkidle": "networkidle",
            }
            wait_state = wait_map.get(req.wait_until, "networkidle")

            await page.goto(url, wait_until=wait_state, timeout=self._timeout * 1000)

            title = await page.title()
            raw_text: str = await page.evaluate("document.body.innerText")

            await browser.close()
            browser = None

            ellapsed = time.monotonic() - start
            took_ms = int(ellapsed * 1000)
            word_count = len(raw_text.split())

            seed = req.fingerprint.seed if req.fingerprint else None

            logger.info(
                "page_scraped",
                url=url,
                title=title,
                words=word_count,
                took_ms=took_ms,
                seed=seed,
            )

            return ScrapeResult(
                url=url,
                title=title,
                content=raw_text[: self._max_content_length],
                word_count=word_count,
                fingerprint_seed=seed,
                took_ms=took_ms,
            )

        except ImportError as exc:
            logger.error("cloakbrowser_not_available", error=str(exc))
            raise RuntimeError(
                "CloakBrowser not available. Install with: pip install research-agent[scraper]"
            ) from exc
        except Exception as exc:
            logger.error("scrape_failed", url=url, error=str(exc))
            raise
        finally:
            if browser is not None:
                try:
                    await browser.close()
                except Exception:
                    pass
