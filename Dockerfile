FROM python:3.10

# Cài các thư viện hệ thống cần thiết cho Playwright
RUN apt-get update && \
    apt-get install -y wget gnupg2 \
    libgtk-3-0 libgtk-4-1 libgraphene-1.0-0 \
    libgstreamer-gl1.0-0 libgstreamer-plugins-base1.0-0 \
    libenchant-2-2 libsecret-1-0 libmanette-0.2-0 libgles2 libavif15

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN playwright install chromium

CMD ["uvicorn", "crawl_endpoint:app", "--host", "0.0.0.0", "--port", "10000"] 