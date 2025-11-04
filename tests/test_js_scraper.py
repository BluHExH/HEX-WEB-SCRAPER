"""
Tests for JavaScript scraper
"""

from unittest.mock import Mock, patch

import pytest

from scraper.config_loader import ConfigLoader
from scraper.js_scraper import JSScraper


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
        "selenium": {"remote_url": "", "headless": True, "screenshot_on_error": True},
    }.get(key, default)

    config.get_nested.side_effect = lambda *keys: {
        ("rate_limit", "delay_seconds"): 1.0,
        ("rate_limit", "jitter"): False,
    }.get(keys)

    return config


@patch("scraper.js_scraper.webdriver.Chrome")
def test_js_scraper_initialization(mock_webdriver, mock_config):
    """Test JavaScript scraper initialization"""
    scraper = JSScraper(mock_config)

    assert scraper.config == mock_config
    assert scraper.base_url == "https://example.com"
    assert scraper.user_agents == ["Mozilla/5.0"]


@patch("scraper.js_scraper.webdriver.Remote")
@patch("scraper.js_scraper.webdriver.Chrome")
def test_setup_driver_remote(mock_chrome, mock_remote, mock_config):
    """Test setting up remote WebDriver"""
    # Configure mock config to use remote URL
    mock_config.get.side_effect = lambda key, default=None: {
        "base_url": "https://example.com",
        "start_paths": ["/"],
        "user_agents": ["Mozilla/5.0"],
        "selectors": {"item": ".item", "fields": {"title": ".title"}},
        "selenium": {
            "remote_url": "http://localhost:4444/wd/hub",
            "headless": True,
            "screenshot_on_error": True,
        },
    }.get(key, default)

    scraper = JSScraper(mock_config)
    scraper.setup_driver()

    mock_remote.assert_called_once()
    mock_chrome.assert_not_called()


@patch("scraper.js_scraper.webdriver.Chrome")
def test_extract_data(mock_webdriver, mock_config):
    """Test data extraction with Selenium"""
    # Create mock elements
    mock_element = Mock()
    mock_element.text = "Test Title"

    mock_driver = Mock()
    mock_driver.find_elements.return_value = [mock_element]
    mock_webdriver.return_value = mock_driver

    scraper = JSScraper(mock_config)
    scraper.driver = mock_driver
    scraper.wait = Mock()

    selectors = {"item": ".item", "fields": {"title": ".title"}}

    data = scraper.extract_data(selectors)

    assert len(data) == 1
    assert data[0]["title"] == "Test Title"
