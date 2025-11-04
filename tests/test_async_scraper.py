"""
Tests for async scraper
"""

from unittest.mock import Mock, patch

import pytest

from scraper.async_scraper import AsyncScraper
from scraper.config_loader import ConfigLoader


@pytest.fixture
def mock_config():
    """Create a mock configuration"""
    config = Mock(spec=ConfigLoader)
    config.get.return_value = None
    config.get_nested.return_value = None

    # Set up specific return values
    config.get.side_effect = lambda key, default=None: {
        "base_url": "https://example.com",
        "start_paths": ["/"],
        "user_agents": ["Mozilla/5.0"],
        "selectors": {"item": ".item", "fields": {"title": ".title"}},
        "concurrency": {"global": 5, "per_domain": 2},
    }.get(key, default)

    config.get_nested.side_effect = lambda *keys: {
        ("rate_limit", "delay_seconds"): 1.0,
        ("rate_limit", "jitter"): False,
    }.get(keys)

    return config


@pytest.mark.asyncio
async def test_async_scraper_initialization(mock_config):
    """Test async scraper initialization"""
    async with AsyncScraper(mock_config) as scraper:
        assert scraper.config == mock_config
        assert scraper.base_url == "https://example.com"
        assert scraper.user_agents == ["Mozilla/5.0"]


@pytest.mark.asyncio
@patch("scraper.async_scraper.aiohttp.ClientSession")
async def test_fetch_page(mock_session, mock_config):
    """Test fetching a page"""
    mock_response = Mock()
    mock_response.read.return_value = b"<html><body><h1>Test</h1></body></html>"
    mock_response.raise_for_status.return_value = None

    mock_session_instance = Mock()
    mock_session_instance.get.return_value.__aenter__.return_value = mock_response
    mock_session.return_value = mock_session_instance

    async with AsyncScraper(mock_config) as scraper:
        soup = await scraper.fetch_page("https://example.com")

        assert soup.find("h1").text == "Test"


@pytest.mark.asyncio
async def test_extract_data(mock_config):
    """Test data extraction"""
    async with AsyncScraper(mock_config) as scraper:
        # Create a mock BeautifulSoup object
        from bs4 import BeautifulSoup

        html = """
        <div class="item">
            <div class="title">Test Title</div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")

        selectors = {"item": ".item", "fields": {"title": ".title"}}

        data = scraper.extract_data(soup, selectors)

        assert len(data) == 1
        assert data[0]["title"] == "Test Title"
