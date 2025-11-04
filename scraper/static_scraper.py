"""
Static scraper implementation using requests and BeautifulSoup
"""

import logging
import random
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from .config_loader import ConfigLoader
from .logger import get_logger

logger = get_logger(__name__)


class StaticScraper:
    """Static web scraper using requests and BeautifulSoup"""

    def __init__(self, config: ConfigLoader):
        self.config = config
        self.session = requests.Session()
        self.user_agents = config.get("user_agents", [])
        self.delay_seconds = config.get_nested("rate_limit", "delay_seconds") or 1.0
        self.jitter = config.get_nested("rate_limit", "jitter") or False
        self.proxies = config.get("proxies", {})
        self.base_url = config.get("base_url")

        # Set up session headers
        if self.user_agents:
            self.session.headers.update({"User-Agent": self.user_agents[0]})

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch a single page with retry logic"""
        # Rotate user agent if multiple are provided
        if self.user_agents:
            user_agent = random.choice(self.user_agents)
            self.session.headers.update({"User-Agent": user_agent})

        # Add delay between requests
        delay = self.delay_seconds
        if self.jitter:
            delay += random.uniform(0, 1)
        time.sleep(delay)

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except requests.RequestException as e:
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

    def get_next_page_url(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """Determine next page URL"""
        pagination = self.config.get("pagination", {})
        next_selector = pagination.get("next_selector")
        next_url_template = pagination.get("next_url_template")

        if next_selector:
            next_element = soup.select_one(next_selector)
            if next_element and next_element.get("href"):
                return urljoin(current_url, next_element["href"])

        # Fallback to URL pattern if specified
        if next_url_template:
            # This would require implementing URL pattern matching
            # For now, we'll just log that this feature is not fully implemented
            logger.warning("URL template pagination not fully implemented")

        return None

    def scrape(self) -> List[Dict[str, Any]]:
        """Main scraping method"""
        all_data = []
        start_paths = self.config.get("start_paths", ["/"])
        selectors = self.config.get("selectors", {})

        for path in start_paths:
            current_url = urljoin(self.base_url, path)

            while current_url:
                logger.info(f"Scraping: {current_url}")

                try:
                    soup = self.fetch_page(current_url)
                    data = self.extract_data(soup, selectors)
                    all_data.extend(data)

                    # Check for next page
                    current_url = self.get_next_page_url(soup, current_url)

                except Exception as e:
                    logger.error(f"Error scraping {current_url}: {e}")
                    break

        return all_data
