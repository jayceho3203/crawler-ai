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

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.extraction_strategy import RegexExtractionStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import MarkdownGenerationResult

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
    """Fallback method using requests when Playwright fails"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract emails using regex
        import re
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
        logger.error(f"❌ Requests fallback failed for {url}: {str(e)}")
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

    contact_regex_strategy = RegexExtractionStrategy(
        pattern=(
            RegexExtractionStrategy.Email |
            RegexExtractionStrategy.Url
        )
    )

    config_params = {
        "extraction_strategy": contact_regex_strategy,
        "markdown_generator": DefaultMarkdownGenerator()
    }
    run_config = CrawlerRunConfig(**config_params)

    # Configure browser for Docker environment
    browser_config = {
        "headless": True,
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote",
            "--disable-gpu"
        ]
    }

    # Try Playwright first, fallback to requests if it fails
    try:
        async with AsyncWebCrawler(browser_config=browser_config) as crawler:
            logger.info(f"📡 Crawling with Playwright: {request.url}")
            result = await crawler.arun(url=request.url, config=run_config)

            response_data.final_url = result.url
            response_data.success = result.success
            response_data.error_message = result.error_message
            response_data.status_code = result.status_code

            if result.markdown and isinstance(result.markdown, MarkdownGenerationResult):
                 response_data.fit_markdown = result.markdown.fit_markdown
            elif isinstance(result.markdown, str):
                 response_data.fit_markdown = result.markdown

            logger.info(f"✅ Playwright crawl completed: {request.url} - Status: {result.status_code}")

            data_for_extractor = []
            processed_html_for_urls = False

            # Extract Emails
            if result.extracted_content:
                try:
                    parsed_extracted_content = json.loads(result.extracted_content)
                    response_data.raw_extracted_data = parsed_extracted_content

                    if isinstance(parsed_extracted_content, list):
                        for item in parsed_extracted_content:
                            if isinstance(item, dict) and item.get("label") == "email" and item.get("value"):
                                data_for_extractor.append({"label": "email", "value": str(item["value"])})
                except json.JSONDecodeError:
                    logger.error(f"❌ Error decoding JSON from extracted_content: {result.extracted_content}")

            # Extract URLs
            if result.html:
                try:
                    soup = BeautifulSoup(result.html, "html.parser")
                    for a_tag in soup.find_all('a', href=True):
                        href = a_tag.get('href')
                        if href and str(href).strip():
                            data_for_extractor.append({"label": "url", "value": str(href)})
                    processed_html_for_urls = True
                except Exception as e:
                    logger.error(f"❌ Error during BeautifulSoup parsing: {e}")

            # Fallback for URLs
            if not processed_html_for_urls and response_data.raw_extracted_data and isinstance(response_data.raw_extracted_data, list):
                for item in response_data.raw_extracted_data:
                    if isinstance(item, dict) and item.get("label") == "url" and item.get("value"):
                        is_duplicate = False
                        for existing_item in data_for_extractor:
                            if existing_item.get("label") == "url" and existing_item.get("value") == item.get("value"):
                                is_duplicate = True
                                break
                        if not is_duplicate:
                             data_for_extractor.append({"label": "url", "value": str(item["value"])})

    except Exception as e:
        logger.warning(f"⚠️ Playwright failed, trying requests fallback: {str(e)}")
        
        # Fallback to requests
        fallback_result = extract_with_requests(request.url)
        
        response_data.final_url = fallback_result.get("url", request.url)
        response_data.success = fallback_result.get("success", False)
        response_data.error_message = fallback_result.get("error_message")
        response_data.status_code = fallback_result.get("status_code", 500)
        
        if fallback_result.get("success"):
            logger.info(f"✅ Requests fallback successful: {request.url}")
            
            data_for_extractor = []
            
            # Add emails from fallback
            for email in fallback_result.get("emails", []):
                data_for_extractor.append({"label": "email", "value": email})
            
            # Add URLs from fallback
            for url in fallback_result.get("urls", []):
                data_for_extractor.append({"label": "url", "value": url})
            
            response_data.raw_extracted_data = data_for_extractor
        else:
            response_data.error_message = f"Both Playwright and requests failed: {str(e)}"
            logger.error(f"❌ Both methods failed for {request.url}")

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