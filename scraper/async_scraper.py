"""
Async scraper implementation using aiohttp
"""

import asyncio
import random
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from .config_loader import ConfigLoader
from .logger import get_logger

logger = get_logger(__name__)


class AsyncScraper:
    """Async web scraper using aiohttp"""

    def __init__(self, config: ConfigLoader):
        self.config = config
        self.base_url = config.get("base_url")
        self.user_agents = config.get("user_agents", [])
        self.delay_seconds = config.get_nested("rate_limit", "delay_seconds") or 1.0
        self.jitter = config.get_nested("rate_limit", "jitter") or False
        self.concurrency = config.get("concurrency", {})
        self.proxies = config.get("proxies", {})
        self.semaphore = None
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        # Set up concurrency limits
        global_concurrency = self.concurrency.get("global", 5)
        self.semaphore = asyncio.Semaphore(global_concurrency)

        # Set up aiohttp session
        connector = aiohttp.TCPConnector(limit=global_concurrency)
        timeout = aiohttp.ClientTimeout(total=30)

        headers = {}
        if self.user_agents:
            headers["User-Agent"] = self.user_agents[0]

        self.session = aiohttp.ClientSession(
            connector=connector, timeout=timeout, headers=headers
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch a single page with retry logic"""
        async with self.semaphore:
            # Rotate user agent if multiple are provided
            headers = {}
            if self.user_agents:
                user_agent = random.choice(self.user_agents)
                headers["User-Agent"] = user_agent

            # Add delay between requests
            delay = self.delay_seconds
            if self.jitter:
                delay += random.uniform(0, 1)
            await asyncio.sleep(delay)

            try:
                async with self.session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    content = await response.read()
                    return BeautifulSoup(content, "html.parser")
            except aiohttp.ClientError as e:
                logger.error(f"Error fetching {url}: {e}")
                raise

    def extract_data(
        self, soup: BeautifulSoup, selectors: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract data from page using CSS selectors"""
        items = []
        item_selector = selectors.get("item", "")
        field_selectors = selectors.get("fields", {})

        # Find all item containers
        item_elements = soup.select(item_selector)

        for element in item_elements:
            item_data = {}
            for field_name, selector in field_selectors.items():
                # Handle different selector types
                if isinstance(selector, str):
                    # Simple CSS selector
                    elements = element.select(selector)
                    if elements:
                        # If multiple elements, get all text
                        if len(elements) > 1:
                            item_data[field_name] = [
                                elem.get_text(strip=True) for elem in elements
                            ]
                        else:
                            item_data[field_name] = elements[0].get_text(strip=True)
                    else:
                        item_data[field_name] = ""
                elif isinstance(selector, dict):
                    # Complex selector with attributes
                    attr = selector.get("attr", "text")
                    css_selector = selector.get("selector", "")
                    elements = element.select(css_selector)
                    if elements:
                        if attr == "text":
                            item_data[field_name] = elements[0].get_text(strip=True)
                        else:
                            item_data[field_name] = elements[0].get(attr, "")
                    else:
                        item_data[field_name] = ""

            items.append(item_data)

        return items

    async def scrape_single_page(
        self, url: str, selectors: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Scrape a single page"""
        try:
            soup = await self.fetch_page(url)
            return self.extract_data(soup, selectors)
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return []

    async def scrape(self) -> List[Dict[str, Any]]:
        """Main scraping method"""
        all_data = []
        start_paths = self.config.get("start_paths", ["/"])
        selectors = self.config.get("selectors", {})

        # Generate all URLs to scrape
        urls = [urljoin(self.base_url, path) for path in start_paths]

        # Scrape all pages concurrently
        async with self:
            tasks = [self.scrape_single_page(url, selectors) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Scraping task failed: {result}")
                else:
                    all_data.extend(result)

        return all_data
