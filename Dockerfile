FROM python:3.10

WORKDIR /app
COPY . /app

# Cài playwright và các dependencies hệ thống
RUN pip install --upgrade pip
RUN pip install playwright
RUN playwright install-deps
RUN pip install -r requirements.txt
RUN playwright install chromium

CMD ["uvicorn", "crawl_endpoint:app", "--host", "0.0.0.0", "--port", "10000"] 