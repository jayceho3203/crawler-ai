FROM python:3.10-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    procps \
    libxss1 \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and dependencies as root
RUN playwright install-deps && playwright install chromium

# Create non-root user and set permissions for browser cache
RUN useradd -m -u 1000 appuser
RUN mkdir -p /home/appuser/.cache && chown -R appuser:appuser /home/appuser/.cache

# Copy application code
COPY crawl_endpoint.py .
COPY contact_extractor.py .

# Change ownership of Playwright cache to appuser
RUN chown -R appuser:appuser /app
RUN chown -R appuser:appuser /home/appuser/.cache

# Switch to appuser
USER appuser

# Install Playwright browser as appuser (manual)
RUN playwright install chromium

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/stats || exit 1

# Run the application
CMD ["uvicorn", "crawl_endpoint:app", "--host", "0.0.0.0", "--port", "8000"] 