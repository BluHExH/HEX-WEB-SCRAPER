"""
Configuration loader for HEX Web Scraper
"""

import json
import os
from typing import Any, Dict


class ConfigLoader:
    """Load and validate configuration files"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            config = json.load(f)

        # Validate required fields
        required_fields = [
            "name",
            "mode",
            "base_url",
            "start_paths",
            "selectors",
            "storage",
        ]

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required configuration field: {field}")

        # Set defaults for optional fields
        config.setdefault("user_agents", [])
        config.setdefault("rate_limit", {"delay_seconds": 1.0, "jitter": False})
        config.setdefault("concurrency", {"global": 5, "per_domain": 2})
        config.setdefault("proxies", {"enabled": False, "list": [], "validate": True})
        config.setdefault(
            "telegram", {"enabled": False, "bot_token": "", "chat_id": ""}
        )
        config.setdefault(
            "selenium",
            {"remote_url": "", "headless": True, "screenshot_on_error": True},
        )

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self.config.get(key, default)

    def get_nested(self, *keys: str) -> Any:
        """Get nested configuration value"""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
