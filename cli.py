"""
Command-line interface for HEX Web Scraper
"""

import json
import os
import sys
from typing import Any, Dict, List

import click

from scraper.async_scraper import AsyncScraper
from scraper.config_loader import ConfigLoader
from scraper.js_scraper import JSScraper
from scraper.logger import get_logger
from scraper.metrics import MetricsManager
from scraper.notifier import Notifier
from scraper.resilience import ResilienceManager
from scraper.scheduler import Scheduler
from scraper.static_scraper import StaticScraper
from scraper.storage import DataStorage

logger = get_logger(__name__)


@click.group()
def cli():
    """HEX Web Scraper CLI"""
    pass


@cli.command()
@click.option("--target", "-t", help="Target name to scrape")
@click.option("--config", "-c", help="Path to config file")
@click.option("--dry-run", is_flag=True, help="Validate selectors without saving")
@click.option("--once", is_flag=True, help="Run once and exit")
@click.option("--daemon", is_flag=True, help="Run as daemon")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--debug", is_flag=True, help="Debug output")
def run(
    target: str,
    config: str,
    dry_run: bool,
    once: bool,
    daemon: bool,
    verbose: bool,
    debug: bool,
):
    """Run the scraper"""
    # Set log level based on flags
    if debug:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        import logging

        logging.getLogger().setLevel(logging.INFO)

    # Load configuration
    if config:
        config_loader = ConfigLoader(config)
    elif target:
        # Try to find target config file
        config_file = f"targets/{target}.json"
        if not os.path.exists(config_file):
            click.echo(f"Target config not found: {config_file}")
            sys.exit(1)
        config_loader = ConfigLoader(config_file)
    else:
        # Try to load default config.json
        if not os.path.exists("config.json"):
            click.echo("No config file specified and config.json not found")
            sys.exit(1)
        config_loader = ConfigLoader("config.json")

    # Initialize components
    notifier = Notifier(config_loader.config)
    resilience = ResilienceManager()
    metrics = MetricsManager()

    # Start metrics server
    metrics.start_metrics_server()

    # Notify start
    notifier.notify_start(config_loader.get("name"))

    try:
        # Determine scraping mode
        mode = config_loader.get("mode", "static")

        # Initialize scraper based on mode
        if mode == "static":
            scraper = StaticScraper(config_loader)
        elif mode == "js":
            scraper = JSScraper(config_loader)
        elif mode == "async":
            # For async mode, we need to run in an async context
            import asyncio

            # We'll handle this separately
            scraper = None
        else:
            click.echo(f"Unsupported mode: {mode}")
            sys.exit(1)

        # Scrape data
        if mode == "async":
            import asyncio

            data = asyncio.run(run_async_scraper(config_loader))
        else:
            data = scraper.scrape()

        # Apply transformations if any
        transformations = config_loader.get("transformations", {})
        if transformations:
            from scraper.plugins import PluginManager

            plugin_manager = PluginManager()
            data = [
                plugin_manager.apply_transformations(item, transformations)
                for item in data
            ]

        # Handle dry run
        if dry_run:
            click.echo(f"Dry run completed. Would have scraped {len(data)} items:")
            for item in data[:5]:  # Show first 5 items
                click.echo(json.dumps(item, indent=2))
            return

        # Save data
        storage_config = config_loader.get("storage", {})
        storage = DataStorage(storage_config)
        storage.save(data)

        # Update metrics
        metrics.increment_items_scraped(len(data))

        # Notify completion
        notifier.notify_completion(config_loader.get("name"), len(data), data[:3])

        click.echo(
            f"Scraping completed. {len(data)} items saved to {storage_config.get('path')}"
        )

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        notifier.notify_error(config_loader.get("name"), str(e))
        sys.exit(1)


async def run_async_scraper(config_loader):
    """Run async scraper"""
    async with AsyncScraper(config_loader) as scraper:
        return await scraper.scrape()


@cli.command()
@click.argument("target")
def test_target(target: str):
    """Test a target configuration"""
    config_file = f"targets/{target}.json"
    if not os.path.exists(config_file):
        click.echo(f"Target config not found: {config_file}")
        sys.exit(1)

    try:
        config_loader = ConfigLoader(config_file)
        click.echo(f"Target '{target}' configuration is valid")
        click.echo(json.dumps(config_loader.config, indent=2))
    except Exception as e:
        click.echo(f"Error in target configuration: {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--format", "-f", type=click.Choice(["csv", "json", "sqlite"]), default="csv"
)
@click.option("--output", "-o", help="Output file path")
def export(format: str, output: str):
    """Export scraped data"""
    # This is a simplified implementation
    # In a real implementation, you would read from the storage and convert to the requested format
    click.echo(f"Exporting data in {format} format to {output or 'default location'}")


if __name__ == "__main__":
    cli()
