"""
JavaScript-heavy scraper implementation using Selenium or Playwright
"""

import logging
import random
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config_loader import ConfigLoader
from .logger import get_logger

logger = get_logger(__name__)


class JSScraper:
    """JavaScript-heavy web scraper using Selenium"""

    def __init__(self, config: ConfigLoader):
        self.config = config
        self.base_url = config.get("base_url")
        self.selenium_config = config.get("selenium", {})
        self.user_agents = config.get("user_agents", [])
        self.delay_seconds = config.get_nested("rate_limit", "delay_seconds") or 1.0
        self.jitter = config.get_nested("rate_limit", "jitter") or False
        self.driver = None
        self.wait = None

    def setup_driver(self):
        """Set up Selenium WebDriver"""
        remote_url = self.selenium_config.get("remote_url")

        if remote_url:
            # Use remote WebDriver (for Termux compatibility)
            try:
                self.driver = webdriver.Remote(
                    command_executor=remote_url, options=self._get_chrome_options()
                )
            except Exception as e:
                logger.error(f"Failed to connect to remote WebDriver: {e}")
                raise
        else:
            # Use local WebDriver
            try:
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager

                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(
                    service=service, options=self._get_chrome_options()
                )
            except Exception as e:
                logger.error(f"Failed to set up local WebDriver: {e}")
                raise

        self.wait = WebDriverWait(self.driver, 10)

    def _get_chrome_options(self):
        """Get Chrome options for WebDriver"""
        chrome_options = Options()

        if self.selenium_config.get("headless", True):
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        if self.user_agents:
            user_agent = random.choice(self.user_agents)
            chrome_options.add_argument(f"user-agent={user_agent}")

        return chrome_options

    def extract_data(self, selectors: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract data from page using CSS selectors"""
        items = []
        item_selector = selectors.get("item", "")
        field_selectors = selectors.get("fields", {})

        try:
            # Wait for item elements to be present
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, item_selector))
            )
        except TimeoutException:
            logger.warning(f"Item selector '{item_selector}' not found on page")
            return items

        # Find all item containers
        item_elements = self.driver.find_elements(By.CSS_SELECTOR, item_selector)

        for element in item_elements:
            item_data = {}
            for field_name, selector in field_selectors.items():
                try:
                    if isinstance(selector, str):
                        # Simple CSS selector
                        elements = element.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            # If multiple elements, get all text
                            if len(elements) > 1:
                                item_data[field_name] = [
                                    elem.text.strip() for elem in elements
                                ]
                            else:
                                item_data[field_name] = elements[0].text.strip()
                        else:
                            item_data[field_name] = ""
                    elif isinstance(selector, dict):
                        # Complex selector with attributes
                        attr = selector.get("attr", "text")
                        css_selector = selector.get("selector", "")
                        elements = element.find_elements(By.CSS_SELECTOR, css_selector)
                        if elements:
                            if attr == "text":
                                item_data[field_name] = elements[0].text.strip()
                            else:
                                item_data[field_name] = elements[0].get_attribute(attr)
                        else:
                            item_data[field_name] = ""
                except Exception as e:
                    logger.warning(f"Error extracting field '{field_name}': {e}")
                    item_data[field_name] = ""

            items.append(item_data)

        return items

    def get_next_page_url(self, current_url: str) -> Optional[str]:
        """Determine next page URL"""
        pagination = self.config.get("pagination", {})
        next_selector = pagination.get("next_selector")

        if next_selector:
            try:
                # Wait for next button to be clickable
                next_element = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, next_selector))
                )
                return next_element.get_attribute("href")
            except TimeoutException:
                logger.info("Next page button not found or not clickable")

        return None

    def take_screenshot(self, filename: str):
        """Take screenshot of current page"""
        if self.driver and self.selenium_config.get("screenshot_on_error", True):
            try:
                import os

                screenshot_dir = "logs/screenshots"
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = os.path.join(screenshot_dir, filename)
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Screenshot saved to {screenshot_path}")
            except Exception as e:
                logger.error(f"Failed to take screenshot: {e}")

    def scrape(self) -> List[Dict[str, Any]]:
        """Main scraping method"""
        all_data = []
        start_paths = self.config.get("start_paths", ["/"])
        selectors = self.config.get("selectors", {})

        try:
            self.setup_driver()

            for path in start_paths:
                current_url = urljoin(self.base_url, path)

                while current_url:
                    logger.info(f"Scraping: {current_url}")

                    try:
                        # Add delay between requests
                        delay = self.delay_seconds
                        if self.jitter:
                            delay += random.uniform(0, 1)
                        time.sleep(delay)

                        self.driver.get(current_url)

                        # Extract data from page
                        data = self.extract_data(selectors)
                        all_data.extend(data)

                        # Check for next page
                        current_url = self.get_next_page_url(current_url)

                    except Exception as e:
                        logger.error(f"Error scraping {current_url}: {e}")
                        self.take_screenshot(f"error_{int(time.time())}.png")
                        break

        except Exception as e:
            logger.error(f"Error setting up WebDriver: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()

        return all_data
