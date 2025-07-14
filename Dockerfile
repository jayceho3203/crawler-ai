FROM python:3.10

WORKDIR /app
COPY . /app

RUN apt-get update && \
    apt-get install -y wget gnupg2 libnss3 libnspr4 libasound2 && \
    pip install playwright && \
    playwright install-deps

# Cài playwright và các dependencies hệ thống
RUN pip install --upgrade pip
RUN pip install playwright
RUN pip install -r requirements.txt
RUN playwright install chromium

CMD ["uvicorn", "crawl_endpoint:app", "--host", "0.0.0.0", "--port", "10000"] 