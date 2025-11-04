"""
Metrics module for HEX Web Scraper
"""

import threading
from typing import Any, Dict

from flask import Flask, jsonify

from .logger import get_logger

logger = get_logger(__name__)

# Global metrics storage
metrics_data = {"items_scraped": 0, "errors": 0, "last_run": None, "runtime": 0}

# Flask app for metrics endpoint
app = Flask(__name__)


@app.route("/metrics")
def metrics():
    """Expose metrics endpoint"""
    return jsonify(metrics_data)


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


class MetricsManager:
    """Manage metrics collection and reporting"""

    def __init__(self, port: int = 8000):
        self.port = port
        self.server_thread = None

    def start_metrics_server(self):
        """Start the metrics server in a separate thread"""
        self.server_thread = threading.Thread(
            target=app.run,
            kwargs={
                "host": "0.0.0.0",
                "port": self.port,
                "debug": False,
                "use_reloader": False,
            },
            daemon=True,
        )
        self.server_thread.start()
        logger.info(f"Metrics server started on port {self.port}")

    def increment_items_scraped(self, count: int = 1):
        """Increment the items scraped counter"""
        metrics_data["items_scraped"] += count

    def increment_errors(self, count: int = 1):
        """Increment the errors counter"""
        metrics_data["errors"] += count

    def set_last_run(self, timestamp: str):
        """Set the last run timestamp"""
        metrics_data["last_run"] = timestamp

    def set_runtime(self, runtime: float):
        """Set the runtime in seconds"""
        metrics_data["runtime"] = runtime
