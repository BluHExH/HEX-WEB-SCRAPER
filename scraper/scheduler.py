"""
Scheduler module for HEX Web Scraper
"""

import threading
import time
from typing import Callable

import schedule

from .logger import get_logger

logger = get_logger(__name__)


class Scheduler:
    """Handle scheduling of scraping tasks"""

    def __init__(self):
        self.running = False
        self.thread = None

    def schedule_task(self, interval: int, unit: str, task: Callable):
        """Schedule a task to run at specified intervals"""
        if unit == "minutes":
            schedule.every(interval).minutes.do(task)
        elif unit == "hours":
            schedule.every(interval).hours.do(task)
        elif unit == "days":
            schedule.every(interval).days.do(task)
        else:
            raise ValueError(f"Unsupported time unit: {unit}")

    def run_scheduler(self):
        """Run the scheduler in a separate thread"""
        self.running = True
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def start_scheduler(self):
        """Start the scheduler in a background thread"""
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.thread.start()
            logger.info("Scheduler started")

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Scheduler stopped")

    def run_once(self, task: Callable):
        """Run a task once"""
        task()
        logger.info("Task executed once")
