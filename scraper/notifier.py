"""
Notification module for HEX Web Scraper
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List

import requests

from .logger import get_logger

logger = get_logger(__name__)


class Notifier:
    """Handle notifications via various channels"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.telegram_config = config.get("telegram", {})
        self.email_config = config.get("email", {})

    def send_telegram_message(
        self, message: str, data_sample: List[Dict[str, Any]] = None
    ):
        """Send message via Telegram"""
        if not self.telegram_config.get("enabled", False):
            return

        bot_token = self.telegram_config.get("bot_token")
        chat_id = self.telegram_config.get("chat_id")

        if not bot_token or not chat_id:
            logger.warning("Telegram not configured properly")
            return

        # Add data sample to message if provided
        if data_sample:
            sample_text = "\n".join(
                [str(item) for item in data_sample[:3]]
            )  # First 3 items
            message += f"\n\nSample data:\n{sample_text}"

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info("Telegram notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

    def send_email(
        self, subject: str, message: str, data_sample: List[Dict[str, Any]] = None
    ):
        """Send email notification"""
        if not self.email_config.get("enabled", False):
            return

        smtp_server = self.email_config.get("smtp_server")
        smtp_port = self.email_config.get("smtp_port", 587)
        username = self.email_config.get("username")
        password = self.email_config.get("password")
        from_addr = self.email_config.get("from_addr")
        to_addr = self.email_config.get("to_addr")

        if not all([smtp_server, username, password, from_addr, to_addr]):
            logger.warning("Email not configured properly")
            return

        # Add data sample to message if provided
        if data_sample:
            sample_text = "\n".join(
                [str(item) for item in data_sample[:3]]
            )  # First 3 items
            message += f"\n\nSample data:\n{sample_text}"

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_addr
            msg["To"] = to_addr
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain"))

            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()

            logger.info("Email notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    def send_webhook(self, message: str, data_sample: List[Dict[str, Any]] = None):
        """Send notification via webhook"""
        webhook_config = self.config.get("webhook", {})
        if not webhook_config.get("enabled", False):
            return

        url = webhook_config.get("url")
        if not url:
            logger.warning("Webhook URL not configured")
            return

        payload = {"text": message}

        # Add data sample if provided
        if data_sample:
            payload["data_sample"] = data_sample[:3]  # First 3 items

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info("Webhook notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")

    def notify_start(self, scraper_name: str):
        """Send notification when scraping starts"""
        message = f"🔄 Scraping started for *{scraper_name}*"

        self.send_telegram_message(message)
        self.send_email(f"Scraping Started: {scraper_name}", message)
        self.send_webhook(message)

    def notify_completion(
        self,
        scraper_name: str,
        items_count: int,
        data_sample: List[Dict[str, Any]] = None,
    ):
        """Send notification when scraping completes"""
        message = (
            f"✅ Scraping completed for *{scraper_name}*\nItems scraped: {items_count}"
        )

        self.send_telegram_message(message, data_sample)
        self.send_email(f"Scraping Completed: {scraper_name}", message, data_sample)
        self.send_webhook(message, data_sample)

    def notify_error(self, scraper_name: str, error: str):
        """Send notification when scraping encounters an error"""
        message = f"❌ Error in *{scraper_name}*:\n```{error}```"

        self.send_telegram_message(message)
        self.send_email(f"Scraping Error: {scraper_name}", message)
        self.send_webhook(message)
