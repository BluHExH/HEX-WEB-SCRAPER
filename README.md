# HEX Web Scraper

![My image](https://github.com/BluHExH/BluHExH/blob/main/IMG_20251104_123036.png)

<!-- Animated HEX Banner -->
<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=30&pause=1000&color=39FF14&center=true&vCenter=true&width=600&lines=Hacker+Hex;Full+Stack+Developer;Cybersecurity+Enthusiast;Open+Source+Contributor" alt="Typing SVG" />

  <!-- Gradient HEX Name -->
<h1 align="center">
  <img src="https://svg-banners.vercel.app/api?type=glitch&text1=H%20E%20X&width=800&height=200" alt="HEX Banner" />
A production-ready, fully featured, secure, and configurable web scraping automation tool.

## Features

- **Multiple Scraping Modes**: Static (requests/BeautifulSoup), JavaScript-heavy (Selenium/Playwright), and Async (aiohttp)
- **Configurable Selectors**: CSS/XPath selectors per target with pagination support
- **Data Storage Options**: CSV, JSON Lines, SQLite with upsert support
- **Politeness & Anti-blocking**: User-Agent rotation, configurable delays, proxy support
- **Scheduler Support**: Cron, Termux-friendly loop runner, Docker + systemd examples
- **Notifications**: Telegram, Email, Webhook/Slack notifiers
- **Logging & Monitoring**: Structured logs, metrics endpoint, health-check
- **Error Handling & Resilience**: Graceful shutdown, persistent job state, circuit breaker
- **Security & Legal**: robots.txt compliance, secrets management, responsible scraping guidelines
- **Extensibility**: Plugin architecture for custom transformations
- **Deployment**: Docker, docker-compose, VPS deployment script

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy and edit config: `cp config_example.json config.json`
4. Run the scraper: `python cli.py run --config config.json`

## Installation

### Python >= 3.11

```bash
pip install -r requirements.txt
```

### Docker

```bash
docker-compose up
```

### Termux (Android)

For JS scraping on Termux, we recommend using a remote Selenium WebDriver:
1. Set up a remote VM with Selenium WebDriver
2. Configure the `remote_url` in your target configuration
3. Run the scraper in Termux which will connect to the remote WebDriver

See the Termux section in the full documentation for detailed instructions.

## Configuration

Create a `config.json` file based on `config_example.json`:

```json
{
  "name": "quotes_static",
  "mode": "static",
  "base_url": "https://quotes.toscrape.com",
  "start_paths": ["/"],
  "selectors": {
    "item": ".quote",
    "fields": {
      "text": ".text",
      "author": ".author",
      "tags": ".tags .tag"
    }
  },
  "pagination": {
    "next_selector": ".next a",
    "next_url_template": null
  },
  "storage": {
    "type": "csv",
    "path": "data/output.csv",
    "unique_key": "text"
  },
  "user_agents": ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"],
  "rate_limit": {"delay_seconds": 1.5, "jitter": true},
  "concurrency": {"global": 5, "per_domain": 2},
  "proxies": {"enabled": false, "list": [], "validate": true},
  "telegram": {"enabled": false, "bot_token": "", "chat_id": ""},
  "selenium": {"remote_url": "", "headless": true, "screenshot_on_error": true}
}
```

## CLI Usage

```bash
# Run a specific target
python cli.py run --target quotes_static

# Run with a config file
python cli.py run --config config.json

# Test a target configuration
python cli.py test-target quotes_static

# Export data
python cli.py export --format csv

# Dry run (validate selectors without saving)
python cli.py run --target quotes_static --dry-run

# Run once
python cli.py run --target quotes_static --once

# Run as daemon
python cli.py run --target quotes_static --daemon
```

## Examples

Check the `examples/` directory for sample configurations:
- `quotes_static.json`: Scrapes quotes.toscrape.com using static mode
- `quotes_js.json`: Scrapes quotes.toscrape.com/js/ using JavaScript mode

## Legal and Ethical Usage

Please see `LEGAL.md` for guidelines on responsible and lawful web scraping.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
