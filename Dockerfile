FROM python:3.10

# Cài các dependencies chuẩn cho Playwright
RUN apt-get update && \
    apt-get install -y wget gnupg2 && \
    pip install playwright && \
    playwright install-deps && \
    pip install -r requirements.txt && \
    playwright install chromium

WORKDIR /app
COPY . /app

CMD ["uvicorn", "crawl_endpoint:app", "--host", "0.0.0.0", "--port", "10000"] 