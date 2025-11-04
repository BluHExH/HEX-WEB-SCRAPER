# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        wget \
        unzip \
        xvfb \
        libxi6 \
        libgconf-2-4 \
        libnss3 \
        libxss1 \
        libappindicator1 \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install-deps
RUN playwright install chromium

# Create non-root user
RUN useradd --create-home --shell /bin/bash scraper
USER scraper

# Copy application code
COPY --chown=scraper:scraper . .

# Expose port for metrics
EXPOSE 8000

# Create volume for output data
VOLUME ["/app/data"]

# Default command
CMD ["python", "cli.py", "run"]