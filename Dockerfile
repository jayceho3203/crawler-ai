FROM python:3.10

# Cài các thư viện hệ thống cần thiết cho Playwright
RUN apt-get update && \
    apt-get install -y wget gnupg2 \
    libgtk-3-0 libgtk-4-1 libgraphene-1.0-0 \
    libgstreamer-gl1.0-0 libgstreamer-plugins-base1.0-0 \
    libenchant-2-2 libsecret-1-0 libmanette-0.2-0 libgles2 libavif15 \
    libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxi6 libxtst6 \
    libnss3 libxrandr2 libasound2 libpangocairo-1.0-0 libatk1.0-0 \
    libcups2 libxss1 libxshmfence1 libgbm1 libpango-1.0-0 fonts-liberation \
    libappindicator3-1 libxinerama1 libxext6 libxfixes3

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN playwright install chromium

CMD ["uvicorn", "crawl_endpoint:app", "--host", "0.0.0.0", "--port", "10000"] 