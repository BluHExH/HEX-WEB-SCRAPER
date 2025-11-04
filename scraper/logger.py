"""
Logging module for HEX Web Scraper
"""

import logging
import os
from typing import Any, Dict

import structlog

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.render_to_log_kwargs,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configure standard logging to write to file
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("logs/scraper.log"), logging.StreamHandler()],
)


def get_logger(name: str):
    """Get a logger instance"""
    return structlog.get_logger(name)
