import asyncio
import json
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict
from urllib.parse import urlparse
import time

try:
    from playwright.async_api import async_playwright
except ImportError:  # pragma: no cover
    async_playwright = None  # type: ignore

try:
    from newspaper import Article
except ImportError:  # pragma: no cover
    Article = None  # type: ignore

import aiohttp
import urllib.robotparser

logger = logging.getLogger(__name__)

@dataclass
class ArticleData:
    url: str
    title: Optional[str] = None
    text: Optional[str] = None
    authors: Optional[List[str]] = None
    published: Optional[str] = None


class RobotsCache:
    """Cache robots.txt parsing results and crawl delays."""

    def __init__(self) -> None:
        self.parsers: Dict[str, urllib.robotparser.RobotFileParser] = {}
        self.delays: Dict[str, int] = {}

    async def fetch(self, session: aiohttp.ClientSession, domain: str) -> None:
        robots_url = domain + "/robots.txt"
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)
        try:
            async with session.get(robots_url) as resp:
                text = await resp.text()
                parser.parse(text.splitlines())
        except Exception:
            parser.parse([])
        self.parsers[domain] = parser
        self.delays[domain] = parser.crawl_delay('*') or 0

    async def allowed(self, session: aiohttp.ClientSession, url: str) -> (bool, int):
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        parser = self.parsers.get(domain)
        if parser is None:
            await self.fetch(session, domain)
            parser = self.parsers[domain]
        return parser.can_fetch('*', url), self.delays.get(domain, 0)


class NewsCrawler:
    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries
        self.robots = RobotsCache()
        self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        await self.session.close()

    async def _download_playwright(self, url: str) -> str:
        if async_playwright is None:
            raise RuntimeError('playwright is not installed')
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            html = await page.content()
            await browser.close()
            return html

    async def _download_static(self, url: str) -> str:
        async with self.session.get(url) as resp:
            return await resp.text()

    async def _parse_article(self, url: str, html: str) -> ArticleData:
        if Article is None:
            raise RuntimeError('newspaper3k is not installed')
        article = Article(url)
        article.set_html(html)
        article.parse()
        return ArticleData(
            url=url,
            title=article.title,
            text=article.text,
            authors=article.authors,
            published=article.publish_date.isoformat() if article.publish_date else None,
        )

    async def fetch_article(self, url: str) -> Optional[ArticleData]:
        allowed, delay = await self.robots.allowed(self.session, url)
        if not allowed:
            logger.warning("Blocked by robots.txt: %s", url)
            return None
        await asyncio.sleep(delay)

        # Try static fetch first
        for attempt in range(1, self.max_retries + 1):
            try:
                html = await self._download_static(url)
                article = await self._parse_article(url, html)
                if article.text.strip():
                    return article
            except Exception as exc:
                logger.error("Static fetch failed (%s): %s", url, exc)
                if attempt == self.max_retries:
                    break
                await asyncio.sleep(attempt)

        # Fallback to playwright
        if async_playwright is None:
            logger.error("Playwright not available for %s", url)
            return None

        for attempt in range(1, self.max_retries + 1):
            try:
                html = await self._download_playwright(url)
                article = await self._parse_article(url, html)
                if article.text.strip():
                    return article
            except Exception as exc:
                logger.error("Playwright fetch failed (%s): %s", url, exc)
                if attempt == self.max_retries:
                    return None
                await asyncio.sleep(attempt)
        return None


async def scrape_urls(urls: List[str]) -> List[ArticleData]:
    crawler = NewsCrawler()
    results: List[ArticleData] = []
    for url in urls:
        data = await crawler.fetch_article(url)
        if data:
            results.append(data)
    await crawler.close()
    return results


def scrape_urls_sync(urls: List[str]) -> List[Dict[str, Optional[str]]]:
    return [data.__dict__ for data in asyncio.run(scrape_urls(urls))]


def main(urls: List[str]) -> None:
    logging.basicConfig(level=logging.INFO)
    articles = scrape_urls_sync(urls)
    print(json.dumps(articles, indent=2))


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
