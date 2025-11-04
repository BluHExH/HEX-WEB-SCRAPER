"""
Resilience module for HEX Web Scraper
"""

import os
import signal
import sqlite3
import sys
from typing import Any, Dict, List

from .logger import get_logger

logger = get_logger(__name__)


class ResilienceManager:
    """Handle resilience features like graceful shutdown and job state persistence"""

    def __init__(self, db_path: str = "logs/job_state.db"):
        self.db_path = db_path
        self.shutdown_requested = False
        self.job_state = {}
        self._init_db()
        self._setup_signal_handlers()

    def _init_db(self):
        """Initialize the job state database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS job_state (
                id INTEGER PRIMARY KEY,
                job_name TEXT UNIQUE,
                last_url TEXT,
                last_page INTEGER,
                items_scraped INTEGER,
                status TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, requesting shutdown...")
        self.shutdown_requested = True

    def save_job_state(self, job_name: str, state: Dict[str, Any]):
        """Save the current state of a job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO job_state 
            (job_name, last_url, last_page, items_scraped, status)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                job_name,
                state.get("last_url", ""),
                state.get("last_page", 0),
                state.get("items_scraped", 0),
                state.get("status", "running"),
            ),
        )

        conn.commit()
        conn.close()

    def load_job_state(self, job_name: str) -> Dict[str, Any]:
        """Load the last saved state of a job"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT last_url, last_page, items_scraped, status
            FROM job_state
            WHERE job_name = ?
        """,
            (job_name,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "last_url": row[0],
                "last_page": row[1],
                "items_scraped": row[2],
                "status": row[3],
            }

        return {}

    def mark_job_completed(self, job_name: str):
        """Mark a job as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE job_state
            SET status = 'completed'
            WHERE job_name = ?
        """,
            (job_name,),
        )

        conn.commit()
        conn.close()

    def check_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested"""
        return self.shutdown_requested

    def circuit_breaker(self, domain: str, failure_threshold: int = 5) -> bool:
        """Implement circuit breaker pattern for domains"""
        # This is a simplified implementation
        # In a production system, you would track failures per domain
        # and temporarily stop making requests to failing domains
        return False  # For now, we'll just return False (circuit closed)
