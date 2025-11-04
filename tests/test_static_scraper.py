"""
Tests for static scraper
"""

from unittest.mock import Mock, patch

import pytest

from scraper.config_loader import ConfigLoader
from scraper.static_scraper import StaticScraper


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
        "pagination": {"next_selector": ".next"},
    }.get(key, default)

    config.get_nested.side_effect = lambda *keys: {
        ("rate_limit", "delay_seconds"): 1.0,
        ("rate_limit", "jitter"): False,
    }.get(keys)

    return config


@patch("scraper.static_scraper.requests.Session")
def test_static_scraper_initialization(mock_session, mock_config):
    """Test static scraper initialization"""
    scraper = StaticScraper(mock_config)

    assert scraper.config == mock_config
    assert scraper.base_url == "https://example.com"
    assert scraper.user_agents == ["Mozilla/5.0"]


@patch("scraper.static_scraper.requests.Session")
def test_fetch_page(mock_session, mock_config):
    """Test fetching a page"""
    mock_response = Mock()
    mock_response.content = b"<html><body><h1>Test</h1></body></html>"
    mock_response.raise_for_status.return_value = None

    mock_session_instance = Mock()
    mock_session_instance.get.return_value = mock_response
    mock_session.return_value = mock_session_instance

    scraper = StaticScraper(mock_config)
    soup = scraper.fetch_page("https://example.com")

    assert soup.find("h1").text == "Test"


@patch("scraper.static_scraper.requests.Session")
def test_extract_data(mock_session, mock_config):
    """Test data extraction"""
    scraper = StaticScraper(mock_config)

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
