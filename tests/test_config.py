"""
Tests for configuration loader
"""

import json
import os

import pytest

from scraper.config_loader import ConfigLoader


@pytest.fixture
def sample_config(tmp_path):
    """Create a sample config file for testing"""
    config_data = {
        "name": "test_scraper",
        "mode": "static",
        "base_url": "https://example.com",
        "start_paths": ["/"],
        "selectors": {
            "item": ".item",
            "fields": {"title": ".title", "description": ".description"},
        },
        "storage": {"type": "csv", "path": "data/output.csv"},
    }

    config_file = tmp_path / "test_config.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    return str(config_file)


def test_config_loader(sample_config):
    """Test configuration loading"""
    loader = ConfigLoader(sample_config)

    # Test basic fields
    assert loader.get("name") == "test_scraper"
    assert loader.get("mode") == "static"
    assert loader.get("base_url") == "https://example.com"

    # Test nested fields
    assert loader.get_nested("selectors", "item") == ".item"
    assert loader.get_nested("storage", "type") == "csv"

    # Test default values
    assert loader.get("user_agents") == []
    assert loader.get_nested("rate_limit", "delay_seconds") == 1.0


def test_config_loader_missing_file():
    """Test config loader with missing file"""
    with pytest.raises(FileNotFoundError):
        ConfigLoader("nonexistent_config.json")


def test_config_loader_missing_required_field(tmp_path):
    """Test config loader with missing required field"""
    config_data = {
        "name": "test_scraper",
        # Missing "mode" field
        "base_url": "https://example.com",
        "start_paths": ["/"],
        "selectors": {"item": ".item", "fields": {"title": ".title"}},
        "storage": {"type": "csv", "path": "data/output.csv"},
    }

    config_file = tmp_path / "incomplete_config.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    with pytest.raises(ValueError, match="Missing required configuration field: mode"):
        ConfigLoader(str(config_file))
