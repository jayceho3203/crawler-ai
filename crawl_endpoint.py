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

class BatchCrawlRequest(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    data_raw: Optional[str] = None
    social: Optional[List[str]] = []
    career_page: Optional[List[str]] = []
    crawl_data: Optional[str] = None

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

class BatchCrawlResponse(BaseModel):
    company_name: Optional[str] = None
    domain: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    social_links: List[str] = []
    career_pages: List[str] = []
    emails: List[str] = []
    crawl_results: List[Dict] = []
    total_urls_processed: int = 0
    successful_crawls: int = 0


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

@app.post("/batch_crawl_and_extract", response_model=BatchCrawlResponse)
async def batch_crawl_and_extract(request: BatchCrawlRequest):
    """
    Batch crawl multiple URLs (social links, career pages) and extract contact information.
    This endpoint is designed to work with n8n workflow data.
    """
    start_time = datetime.now()
    logger.info(f"🚀 Starting batch crawl for company: {request.name}")
    
    response = BatchCrawlResponse(
        company_name=request.name,
        domain=request.domain,
        phone=request.phone,
        description=request.description
    )
    
    # Collect all URLs to crawl
    urls_to_crawl = []
    
    # Add social links
    if request.social:
        if isinstance(request.social, str):
            # Handle case where social is passed as string
            social_urls = [url.strip() for url in request.social.split(',') if url.strip()]
        else:
            social_urls = request.social
        urls_to_crawl.extend(social_urls)
        response.social_links = social_urls
    
    # Add career pages
    if request.career_page:
        if isinstance(request.career_page, str):
            # Handle case where career_page is passed as string
            career_urls = [url.strip() for url in request.career_page.split(',') if url.strip()]
        else:
            career_urls = request.career_page
        urls_to_crawl.extend(career_urls)
        response.career_pages = career_urls
    
    # Add main domain if available
    if request.domain and not request.domain.startswith(('http://', 'https://')):
        main_url = f"https://{request.domain}"
        urls_to_crawl.insert(0, main_url)  # Add main domain first
    
    response.total_urls_processed = len(urls_to_crawl)
    logger.info(f"📋 URLs to crawl: {response.total_urls_processed}")
    
    # Crawl each URL
    all_emails = set()
    all_social_links = set()
    all_career_pages = set()
    
    for url in urls_to_crawl:
        try:
            logger.info(f"📡 Crawling: {url}")
            result = extract_with_requests(url)
            
            crawl_result = {
                "url": url,
                "success": result.get("success", False),
                "status_code": result.get("status_code"),
                "error_message": result.get("error_message"),
                "emails": [],
                "social_links": [],
                "career_pages": []
            }
            
            if result.get("success"):
                response.successful_crawls += 1
                
                # Process extracted data
                data_for_extractor = []
                
                # Add emails
                for email in result.get("emails", []):
                    data_for_extractor.append({"label": "email", "value": email})
                    all_emails.add(email)
                
                # Add URLs
                for url_found in result.get("urls", []):
                    data_for_extractor.append({"label": "url", "value": url_found})
                
                # Process with contact extractor
                if data_for_extractor:
                    classified_contacts = process_extracted_crawl_results(
                        raw_extracted_list=data_for_extractor,
                        base_url=result.get("url", url)
                    )
                    
                    crawl_result["emails"] = classified_contacts.get("emails", [])
                    crawl_result["social_links"] = classified_contacts.get("social_links", [])
                    crawl_result["career_pages"] = classified_contacts.get("career_pages", [])
                    
                    # Add to global sets
                    all_emails.update(classified_contacts.get("emails", []))
                    all_social_links.update(classified_contacts.get("social_links", []))
                    all_career_pages.update(classified_contacts.get("career_pages", []))
            
            response.crawl_results.append(crawl_result)
            
        except Exception as e:
            logger.error(f"❌ Error crawling {url}: {str(e)}")
            response.crawl_results.append({
                "url": url,
                "success": False,
                "error_message": str(e)
            })
    
    # Set final results
    response.emails = sorted(list(all_emails))
    response.social_links = sorted(list(all_social_links))
    response.career_pages = sorted(list(all_career_pages))
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"⏱️ Batch crawl completed in {duration:.2f}s")
    logger.info(f"📊 Results: {len(response.emails)} emails, {len(response.social_links)} social, {len(response.career_pages)} career")
    
    return response

@app.get("/stats")
async def get_crawl_stats():
    """Get crawling statistics"""
    return {
        "message": "Crawl API is running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "single_crawl": "/crawl_and_extract_contact_info",
            "batch_crawl": "/batch_crawl_and_extract",
            "stats": "/stats"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)