# crawl_endpoint.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import json
import logging
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
from datetime import datetime
import os
import requests
from urllib.parse import urljoin
import re

# Import from the refactored contact_extractor
from contact_extractor import (
    process_extracted_crawl_results,
    SOCIAL_DOMAINS,
    CAREER_KEYWORDS,
    normalize_url
)

# Keep urllib.parse if used for any direct URL manipulation in the endpoint itself
from urllib.parse import urlparse, urljoin

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class CrawlRequest(BaseModel):
    url: str

class CrawlResponse(BaseModel):
    requested_url: str
    final_url: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    emails: List[str] = []
    social_links: List[str] = []
    career_pages: List[str] = []
    raw_extracted_data: Optional[Dict] = None
    fit_markdown: Optional[str] = None


def extract_with_requests(url: str) -> Dict:
    """Primary method using requests instead of Playwright"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract emails using regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, response.text)
        
        # Extract URLs
        urls = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            if href:
                full_url = urljoin(url, href)
                urls.append(full_url)
        
        return {
            "success": True,
            "status_code": response.status_code,
            "url": response.url,
            "html": response.text,
            "emails": emails,
            "urls": urls
        }
    except Exception as e:
        logger.error(f"❌ Requests failed for {url}: {str(e)}")
        return {
            "success": False,
            "error_message": str(e),
            "status_code": 500
        }


@app.post("/crawl_and_extract_contact_info", response_model=CrawlResponse)
async def crawl_and_extract_contact_info(request: CrawlRequest):
    start_time = datetime.now()
    logger.info(f"🚀 Starting crawl for: {request.url}")
    
    response_data = CrawlResponse(requested_url=request.url, success=False)

    # Use requests as primary method (no Playwright)
    logger.info(f"📡 Crawling with requests: {request.url}")
    result = extract_with_requests(request.url)
    
    response_data.final_url = result.get("url", request.url)
    response_data.success = result.get("success", False)
    response_data.error_message = result.get("error_message")
    response_data.status_code = result.get("status_code", 500)

    if result.get("success"):
        logger.info(f"✅ Requests crawl completed: {request.url} - Status: {result.get('status_code')}")
        
        data_for_extractor = []
        
        # Add emails from result
        for email in result.get("emails", []):
            data_for_extractor.append({"label": "email", "value": email})
        
        # Add URLs from result
        for url in result.get("urls", []):
            data_for_extractor.append({"label": "url", "value": url})
        
        response_data.raw_extracted_data = data_for_extractor
        
        # Process extracted data
        if data_for_extractor:
            classified_contacts = process_extracted_crawl_results(
                raw_extracted_list=data_for_extractor,
                base_url=str(response_data.final_url) if response_data.final_url else request.url
            )
            response_data.emails = classified_contacts.get("emails", [])
            response_data.social_links = classified_contacts.get("social_links", [])
            response_data.career_pages = classified_contacts.get("career_pages", [])

            # Log extraction results
            logger.info(f"📊 Extraction results for {request.url}:")
            logger.info(f"   📧 Emails: {len(response_data.emails)}")
            logger.info(f"   🔗 Social links: {len(response_data.social_links)}")
            logger.info(f"   💼 Career pages: {len(response_data.career_pages)}")
    else:
        logger.error(f"❌ Requests failed for {request.url}")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"⏱️ Total time for {request.url}: {duration:.2f}s")
    
    return response_data

@app.get("/stats")
async def get_crawl_stats():
    """Get crawling statistics"""
    return {
        "message": "Crawl API is running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "crawl": "/crawl_and_extract_contact_info",
            "stats": "/stats"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)