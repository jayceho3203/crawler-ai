#!/usr/bin/env python3
"""
Simple server for testing job extraction without playwright
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
import json
from typing import List, Dict, Optional

# Import job extractor
from job_extractor import extract_jobs_from_page

app = FastAPI()

class CrawlRequest(BaseModel):
    url: str

class CrawlResponse(BaseModel):
    requested_url: str
    success: bool
    error_message: Optional[str] = None
    emails: List[str] = []
    social_links: List[str] = []
    career_pages: List[str] = []
    total_jobs_found: Optional[int] = None
    jobs: Optional[List[Dict]] = None
    crawl_time: Optional[float] = None

def extract_with_requests_simple(url: str) -> Dict:
    """Simple extraction using requests only"""
    start_time = time.time()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8'
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
        
        # Look for career-related URLs
        career_urls = []
        career_keywords = [
            'tuyen-dung', 'tuyển-dụng', 'viec-lam', 'việc-làm',
            'co-hoi', 'cơ-hội', 'nhan-vien', 'nhân-viên',
            'career', 'job', 'hiring', 'recruitment'
        ]
        
        for url_found in urls:
            url_lower = url_found.lower()
            for keyword in career_keywords:
                if keyword in url_lower:
                    career_urls.append(url_found)
                    break
        
        crawl_time = time.time() - start_time
        
        return {
            "success": True,
            "status_code": response.status_code,
            "url": response.url,
            "emails": list(set(emails)),
            "urls": list(set(urls)),
            "career_urls": list(set(career_urls)),
            "crawl_time": crawl_time
        }
    except Exception as e:
        crawl_time = time.time() - start_time
        return {
            "success": False,
            "error_message": str(e),
            "status_code": 500,
            "crawl_time": crawl_time
        }

@app.post("/crawl_and_extract_contact_info", response_model=CrawlResponse)
async def crawl_and_extract_contact_info(request: CrawlRequest):
    start_time = time.time()
    print(f"🚀 Starting crawl for: {request.url}")
    
    response_data = CrawlResponse(requested_url=request.url, success=False)

    # Simple crawl without playwright
    result = extract_with_requests_simple(request.url)
    
    response_data.success = result.get("success", False)
    response_data.error_message = result.get("error_message")
    response_data.crawl_time = result.get("crawl_time", 0)

    if result.get("success"):
        print(f"✅ Crawl completed: {request.url} - Time: {result.get('crawl_time', 0):.2f}s")
        
        # Add emails
        response_data.emails = result.get("emails", [])
        
        # Add career pages
        career_urls = result.get("career_urls", [])
        response_data.career_pages = career_urls

        # Extract jobs from career pages
        if career_urls:
            print(f"💼 Found {len(career_urls)} career pages, extracting jobs...")
            
            all_jobs = []
            for career_url in career_urls[:3]:  # Limit to 3 career pages
                try:
                    job_result = extract_jobs_from_page(career_url, max_jobs=20)  # Increased limit
                    if job_result.get("success"):
                        jobs = job_result.get("jobs", [])
                        all_jobs.extend(jobs)
                        print(f"   Found {len(jobs)} jobs from {career_url}")
                except Exception as e:
                    print(f"   Error extracting from {career_url}: {e}")
            
            # Also try to extract jobs directly from the main URL if it's a career page
            if any(keyword in request.url.lower() for keyword in ['tuyendung', 'career', 'job', 'tuyen-dung']):
                try:
                    print(f"   Also extracting jobs directly from main URL: {request.url}")
                    job_result = extract_jobs_from_page(request.url, max_jobs=20)
                    if job_result.get("success"):
                        jobs = job_result.get("jobs", [])
                        all_jobs.extend(jobs)
                        print(f"   Found {len(jobs)} jobs from main URL")
                except Exception as e:
                    print(f"   Error extracting from main URL: {e}")
            
            # Remove duplicates based on title and URL
            unique_jobs = []
            seen_titles = set()
            seen_urls = set()
            for job in all_jobs:
                title = job.get('title', '').lower()
                url = job.get('url', '')
                
                if title not in seen_titles and url not in seen_urls:
                    unique_jobs.append(job)
                    seen_titles.add(title)
                    if url:
                        seen_urls.add(url)
            
            response_data.total_jobs_found = len(unique_jobs)
            response_data.jobs = unique_jobs
            
            print(f"✅ Job extraction completed: {len(unique_jobs)} total jobs found")

        # Log results
        print(f"📊 Results: {len(response_data.emails)} emails, {len(response_data.career_pages)} career pages, {response_data.total_jobs_found or 0} jobs")
    else:
        print(f"❌ Crawl failed for {request.url}")

    total_time = time.time() - start_time
    print(f"⏱️ Total time: {total_time:.2f}s")
    
    return response_data

@app.get("/")
async def root():
    return {"message": "Simple Job Extraction Server is running"}

@app.get("/stats")
async def stats():
    return {
        "message": "Simple Job Extraction Server",
        "endpoints": ["/crawl_and_extract_contact_info", "/stats"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 