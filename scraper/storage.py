"""
Data storage module for HEX Web Scraper
"""

import csv
import json
import os
import sqlite3
from typing import Any, Dict, List

from .logger import get_logger

logger = get_logger(__name__)


class DataStorage:
    """Handle storage of scraped data in various formats"""

    def __init__(self, storage_config: Dict[str, Any]):
        self.storage_type = storage_config.get("type", "csv")
        self.storage_path = storage_config.get("path", "data/output.csv")
        self.unique_key = storage_config.get("unique_key")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

        # Initialize storage based on type
        if self.storage_type == "sqlite":
            self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite database"""
        self.db_path = self.storage_path
        # Database initialization will happen when we store data

    def save(self, data: List[Dict[str, Any]]):
        """Save data based on storage type"""
        if self.storage_type == "csv":
            self._save_csv(data)
        elif self.storage_type == "jsonl":
            self._save_jsonl(data)
        elif self.storage_type == "sqlite":
            self._save_sqlite(data)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")

    def _save_csv(self, data: List[Dict[str, Any]]):
        """Save data to CSV file"""
        if not data:
            logger.warning("No data to save to CSV")
            return

        # Use the keys from the first item as fieldnames
        fieldnames = list(data[0].keys())

        # Check if file exists to determine if we need to write headers
        file_exists = os.path.isfile(self.storage_path)

        with open(self.storage_path, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header only if file doesn't exist
            if not file_exists:
                writer.writeheader()

            # Write data rows
            for item in data:
                writer.writerow(item)

        logger.info(f"Saved {len(data)} items to CSV: {self.storage_path}")

    def _save_jsonl(self, data: List[Dict[str, Any]]):
        """Save data to JSON Lines file"""
        with open(self.storage_path, "a", encoding="utf-8") as jsonl_file:
            for item in data:
                jsonl_file.write(json.dumps(item, ensure_ascii=False) + "\n")

        logger.info(f"Saved {len(data)} items to JSON Lines: {self.storage_path}")

    def _save_sqlite(self, data: List[Dict[str, Any]]):
        """Save data to SQLite database"""
        if not data:
            logger.warning("No data to save to SQLite")
            return

        # Connect to database (this will create the file if it doesn't exist)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Create table if it doesn't exist
            if data:
                # Use the keys from the first item as column names
                columns = list(data[0].keys())
                # Create column definitions
                column_defs = ", ".join([f"{col} TEXT" for col in columns])

                # If we have a unique key, add it to the table definition
                if self.unique_key and self.unique_key in columns:
                    create_table_sql = f"""
                    CREATE TABLE IF NOT EXISTS scraped_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        {column_defs},
                        UNIQUE({self.unique_key})
                    )
                    """
                else:
                    create_table_sql = f"""
                    CREATE TABLE IF NOT EXISTS scraped_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        {column_defs}
                    )
                    """

                cursor.execute(create_table_sql)

                # Insert data
                for item in data:
                    # Create INSERT statement with ON CONFLICT clause for upsert
                    placeholders = ", ".join(["?" for _ in columns])
                    column_names = ", ".join(columns)

                    if self.unique_key and self.unique_key in columns:
                        # Update existing records on conflict
                        update_clause = ", ".join(
                            [
                                f"{col} = excluded.{col}"
                                for col in columns
                                if col != self.unique_key
                            ]
                        )
                        insert_sql = f"""
                        INSERT INTO scraped_data ({column_names})
                        VALUES ({placeholders})
                        ON CONFLICT({self.unique_key}) DO UPDATE SET
                        {update_clause}
                        """
                    else:
                        # Simple insert
                        insert_sql = f"INSERT INTO scraped_data ({column_names}) VALUES ({placeholders})"

                    values = [item.get(col, "") for col in columns]
                    cursor.execute(insert_sql, values)

                conn.commit()
                logger.info(f"Saved {len(data)} items to SQLite: {self.db_path}")

        except Exception as e:
            logger.error(f"Error saving to SQLite: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
