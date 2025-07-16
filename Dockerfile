FROM python:3.10-slim

# Install system dependencies for requests and BeautifulSoup
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and dependencies as root
RUN playwright install --with-deps

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Copy application code
COPY crawl_endpoint.py .
COPY contact_extractor.py .

# Create postinstall script
RUN echo '#!/bin/bash\n\
echo "Running postinstall script..."\n\
if [ ! -f "/home/appuser/.cache/ms-playwright/chromium-1155/chrome-linux/chrome" ]; then\n\
    echo "Playwright browser not found, installing..."\n\
    playwright install chromium\n\
    echo "Playwright browser installed successfully"\n\
else\n\
    echo "Playwright browser already exists"\n\
fi\n\
echo "Starting application..."\n\
exec uvicorn crawl_endpoint:app --host 0.0.0.0 --port 8000' > /app/start.sh

RUN chmod +x /app/start.sh

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to appuser
USER appuser

# Install Playwright browser as appuser (without deps since they're already installed)
RUN playwright install

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/stats || exit 1

# Run the application
CMD ["/app/start.sh"] 