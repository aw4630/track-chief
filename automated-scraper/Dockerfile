# Use official Python runtime as base image
FROM python:3.9

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app

# Install dependencies and Chromium
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    default-libmysqlclient-dev \
    build-essential \
    postgresql-client \
    chromium \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome environment variables
ENV CHROME_BIN=/usr/bin/chromium \
    CHROME_PATH=/usr/lib/chromium/chrome \
    CHROMIUM_FLAGS="--no-sandbox --headless --disable-gpu --disable-software-rasterizer --disable-dev-shm-usage"

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for credentials
RUN mkdir -p /app/secrets

# Copy the entire app directory
COPY app/ /app/

# Create non-root user
RUN useradd -m scraper && \
    chown -R scraper:scraper /app

# Set proper permissions
RUN chmod -R 755 /app

USER scraper

# Run the scraper
CMD ["python", "-m", "scraper.run_scraper"]