# Makefile for HEX Web Scraper

# Variables
PYTHON := python3
PIP := pip3
TEST_FLAGS := -v

# Default target
.PHONY: help
help:
	@echo "HEX Web Scraper Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make build     - Install dependencies"
	@echo "  make test      - Run tests"
	@echo "  make run       - Run the scraper"
	@echo "  make clean     - Clean up temporary files"
	@echo "  make lint      - Run code linting"
	@echo "  make format    - Format code with black and isort"

# Install dependencies
.PHONY: build
build:
	$(PIP) install -r requirements.txt

# Run tests
.PHONY: test
test:
	$(PYTHON) -m pytest $(TEST_FLAGS) tests/

# Run the scraper
.PHONY: run
run:
	$(PYTHON) cli.py run

# Clean up temporary files
.PHONY: clean
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf logs/*.log
	rm -rf logs/screenshots/*.png
	rm -rf logs/job_state.db

# Run code linting
.PHONY: lint
lint:
	$(PYTHON) -m flake8 scraper/ cli.py
	$(PYTHON) -m mypy scraper/ cli.py

# Format code with black and isort
.PHONY: format
format:
	$(PYTHON) -m black scraper/ cli.py
	$(PYTHON) -m isort scraper/ cli.py

# Set up pre-commit hooks
.PHONY: setup-hooks
setup-hooks:
	$(PYTHON) -m pip install pre-commit
	pre-commit install

# Run pre-commit hooks
.PHONY: pre-commit
pre-commit:
	pre-commit run --all-files