# crawl_endpoint.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import json
import logging
from bs4 import BeautifulSoup
from typing import Optional, List, Dict, Set
from datetime import datetime
import os
import requests
from urllib.parse import urljoin, urlparse
import re
import asyncio
import time
import hashlib
from playwright.async_api import async_playwright, Browser, Page
import random

# Import from the refactored contact_extractor
from contact_extractor import (
    process_extracted_crawl_results,
    SOCIAL_DOMAINS,
    CAREER_KEYWORDS,
    normalize_url
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Vietnamese software company career keywords
CAREER_KEYWORDS_VI = [
    # Vietnamese keywords
    'tuyen-dung', 'tuyển-dụng', 'tuyen-dung', 'tuyển-dụng',
    'viec-lam', 'việc-làm', 'viec-lam', 'việc-làm',
    'co-hoi', 'cơ-hội', 'co-hoi', 'cơ-hội',
    'nhan-vien', 'nhân-viên', 'nhan-vien', 'nhân-viên',
    'tuyen', 'tuyển', 'tuyen', 'tuyển',
    'ung-vien', 'ứng-viên', 'ung-vien', 'ứng-viên',
    'cong-viec', 'công-việc', 'cong-viec', 'công-việc',
    'lam-viec', 'làm-việc', 'lam-viec', 'làm-việc',
    'moi', 'mời', 'moi', 'mời',
    'thu-viec', 'thử-việc', 'thu-viec', 'thử-việc',
    'chinh-thuc', 'chính-thức', 'chinh-thuc', 'chính-thức',
    
    # English keywords
    'developer', 'dev', 'programmer', 'engineer',
    'software', 'tech', 'technology', 'it',
    'career', 'job', 'recruitment', 'employment',
    'work', 'position', 'opportunity', 'vacancy',
    'apply', 'application', 'hiring', 'join-us',
    'team', 'talent', 'careers', 'jobs',
    'open-role', 'open-roles', 'we-are-hiring',
    'work-with-us', 'join-our-team', 'grow-with-us',
    'build-with-us', 'create-with-us', 'innovate-with-us',
    'full-time', 'part-time', 'remote', 'hybrid',
    'onsite', 'on-site', 'freelance', 'contract',
    'internship', 'intern', 'graduate', 'entry-level',
    'senior', 'junior', 'lead', 'principal',
    'frontend', 'front-end', 'backend', 'back-end',
    'fullstack', 'full-stack', 'mobile', 'web',
    'data', 'ai', 'ml', 'machine-learning',
    'devops', 'qa', 'test', 'testing',
    'ui', 'ux', 'design', 'product'
]

# Common job board platforms
JOB_BOARD_DOMAINS = {
    'topcv.vn', 'careerbuilder.vn', 'jobstreet.vn', 'vietnamworks.com',
    'mywork.com.vn', '123job.vn', 'timviec365.vn', 'careerlink.vn',
    'indeed.com', 'linkedin.com/jobs', 'glassdoor.com', 'monster.com',
    'ziprecruiter.com', 'simplyhired.com', 'dice.com', 'angel.co',
    'stackoverflow.com/jobs', 'github.com/jobs', 'remote.co', 'weworkremotely.com'
}

def is_job_board_url(url: str) -> bool:
    """Check if URL is from a known job board platform"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Remove www. prefix for comparison
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain in JOB_BOARD_DOMAINS

def extract_career_pages_from_job_board(html_content: str, base_url: str) -> List[str]:
    """Extract company career pages from job board listings"""
    career_pages = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Common patterns for company links on job boards
    company_selectors = [
        'a[href*="/company/"]', 'a[href*="/employer/"]', 'a[href*="/recruiter/"]',
        'a[href*="/business/"]', 'a[href*="/client/"]', 'a[href*="/partner/"]',
        '.company-name a', '.employer-name a', '.business-name a',
        '[data-company] a', '[data-employer] a', '.job-company a'
    ]
    
    for selector in company_selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    # Only add if it's not the same job board
                    if not is_job_board_url(full_url):
                        career_pages.append(full_url)
        except:
            continue
    
    return list(set(career_pages))

# Software company career selectors
CAREER_SELECTORS = [
    'a[href*="tuyen-dung"]', 'a[href*="viec-lam"]',
    'a[href*="career"]', 'a[href*="job"]',
    'a[href*="recruitment"]', 'a[href*="employment"]',
    'a[href*="developer"]', 'a[href*="dev"]',
    'a[href*="software"]', 'a[href*="tech"]',
    'a[href*="hiring"]', 'a[href*="join-us"]',
    'a[href*="talent"]', 'a[href*="team"]',
    'a[href*="apply"]', 'a[href*="position"]',
    'a[href*="vacancy"]', 'a[href*="opportunity"]',
    'a[href*="open-role"]', 'a[href*="open-roles"]',
    'a[href*="we-are-hiring"]', 'a[href*="work-with-us"]',
    '.menu a', '.nav a', 'header a', 'footer a',
    'nav a', '.navigation a', '.navbar a',
    '.careers a', '.jobs a', '.team a',
    '.career a', '.job a', '.hiring a',
    '.recruitment a', '.talent a', '.apply a'
]

# Cache for crawl results
crawl_cache = {}
CACHE_DURATION = 3600  # 1 hour

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
    url: Optional[str] = None

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
    crawl_method: Optional[str] = None
    crawl_time: Optional[float] = None
    # Job extraction fields
    total_jobs_found: Optional[int] = None
    jobs: Optional[List[Dict]] = None

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
    total_crawl_time: Optional[float] = None

def get_cached_result(url: str) -> Optional[Dict]:
    """Get cached crawl result if available and not expired"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    if url_hash in crawl_cache:
        cached = crawl_cache[url_hash]
        if time.time() - cached['timestamp'] < CACHE_DURATION:
            logger.info(f"📋 Using cached result for {url}")
            return cached['data']
    return None

def cache_result(url: str, data: Dict):
    """Cache crawl result"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    crawl_cache[url_hash] = {
        'data': data,
        'timestamp': time.time()
    }

async def extract_with_playwright(url: str) -> Dict:
    """Primary method using Playwright for JavaScript rendering and dynamic content"""
    start_time = time.time()
    
    try:
        async with async_playwright() as p:
            # Launch browser with stealth mode
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            # Create context with stealth settings
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                extra_http_headers={
                    'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            )
            
            page = await context.new_page()
            
            # Block unnecessary resources for faster loading
            await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf}", lambda route: route.abort())
            
            # Navigate to URL
            logger.info(f"🌐 Playwright navigating to: {url}")
            response = await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            
            if not response or response.status >= 400:
                raise Exception(f"HTTP {response.status if response else 'Unknown'}")
            
            # Wait for page to be ready
            await page.wait_for_timeout(2000)
            
            # Try to find and interact with navigation elements
            try:
                # Look for navigation elements
                nav_selectors = ['nav', '.menu', '.navigation', '.navbar', 'header']
                for selector in nav_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=3000)
                        # Hover over navigation to trigger dropdowns
                        await page.hover(selector)
                        await page.wait_for_timeout(1000)
                        break
                    except:
                        continue
            except:
                pass
            
            # Scroll to trigger lazy loading
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(500)
            except:
                pass
            
            # Extract HTML content
            html_content = await page.content()
            
            # Extract emails using regex
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, html_content)
            
            # Extract all URLs
            urls = []
            try:
                links = await page.query_selector_all('a[href]')
                for link in links:
                    href = await link.get_attribute('href')
                    if href:
                        full_url = urljoin(url, href)
                        urls.append(full_url)
            except:
                # Fallback to BeautifulSoup if Playwright selector fails
                soup = BeautifulSoup(html_content, 'html.parser')
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        urls.append(full_url)
            
            # Look specifically for career-related links
            career_urls = []
            try:
                for selector in CAREER_SELECTORS:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements:
                            href = await element.get_attribute('href')
                            if href:
                                full_url = urljoin(url, href)
                                career_urls.append(full_url)
                    except:
                        continue
            except:
                pass
            
            # Also check URLs for career keywords
            for url_found in urls:
                url_lower = url_found.lower()
                for keyword in CAREER_KEYWORDS_VI:
                    if keyword in url_lower:
                        career_urls.append(url_found)
                        break
            
            # Check if this is a job board and extract company career pages
            if is_job_board_url(url):
                logger.info(f"🎯 Detected job board: {url}")
                job_board_career_pages = extract_career_pages_from_job_board(html_content, url)
                career_urls.extend(job_board_career_pages)
                logger.info(f"📋 Found {len(job_board_career_pages)} company career pages from job board")
            
            await browser.close()
            
            crawl_time = time.time() - start_time
            logger.info(f"✅ Playwright crawl completed: {url} - {crawl_time:.2f}s")
            
            return {
                "success": True,
                "status_code": response.status if response else 200,
                "url": response.url if response else url,
                "html": html_content,
                "emails": list(set(emails)),
                "urls": list(set(urls)),
                "career_urls": list(set(career_urls)),
                "crawl_time": crawl_time,
                "method": "playwright"
            }
            
    except Exception as e:
        crawl_time = time.time() - start_time
        logger.error(f"❌ Playwright failed for {url}: {str(e)}")
        return {
            "success": False,
            "error_message": str(e),
            "status_code": 500,
            "crawl_time": crawl_time,
            "method": "playwright"
        }

def extract_with_requests(url: str) -> Dict:
    """Fallback method using requests"""
    start_time = time.time()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
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
        for url_found in urls:
            url_lower = url_found.lower()
            for keyword in CAREER_KEYWORDS_VI:
                if keyword in url_lower:
                    career_urls.append(url_found)
                    break
        
        crawl_time = time.time() - start_time
        logger.info(f"✅ Requests fallback completed: {url} - {crawl_time:.2f}s")
        
        return {
            "success": True,
            "status_code": response.status_code,
            "url": response.url,
            "html": response.text,
            "emails": list(set(emails)),
            "urls": list(set(urls)),
            "career_urls": list(set(career_urls)),
            "crawl_time": crawl_time,
            "method": "requests"
        }
    except Exception as e:
        crawl_time = time.time() - start_time
        logger.error(f"❌ Requests failed for {url}: {str(e)}")
        return {
            "success": False,
            "error_message": str(e),
            "status_code": 500,
            "crawl_time": crawl_time,
            "method": "requests"
        }

async def crawl_single_url(url: str) -> Dict:
    """Crawl single URL with Playwright primary, requests fallback"""
    # Check cache first
    cached = get_cached_result(url)
    if cached:
        return cached
    
    # Try Playwright first
    logger.info(f"🚀 Starting Playwright crawl for: {url}")
    result = await extract_with_playwright(url)
    
    # If Playwright fails, try requests
    if not result.get("success"):
        logger.info(f"🔄 Playwright failed, trying requests fallback for: {url}")
        result = extract_with_requests(url)
    
    # Cache the result
    cache_result(url, result)
    
    return result

@app.post("/crawl_and_extract_contact_info", response_model=CrawlResponse)
async def crawl_and_extract_contact_info(request: CrawlRequest):
    start_time = datetime.now()
    logger.info(f"🚀 Starting crawl for: {request.url}")
    
    response_data = CrawlResponse(requested_url=request.url, success=False)

    # Crawl with improved method
    result = await crawl_single_url(request.url)
    
    response_data.final_url = result.get("url", request.url)
    response_data.success = result.get("success", False)
    response_data.error_message = result.get("error_message")
    response_data.status_code = result.get("status_code", 500)
    response_data.crawl_method = result.get("method", "unknown")
    response_data.crawl_time = result.get("crawl_time", 0)

    if result.get("success"):
        logger.info(f"✅ Crawl completed: {request.url} - Method: {result.get('method')} - Time: {result.get('crawl_time', 0):.2f}s")
        
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
            
            # Add career URLs found by our improved method
            career_urls = result.get("career_urls", [])
            for career_url in career_urls:
                if career_url not in response_data.career_pages:
                    response_data.career_pages.append(career_url)

            # NEW: Extract jobs from career pages
            if response_data.career_pages:
                logger.info(f"💼 Found {len(response_data.career_pages)} career pages, extracting jobs...")
                
                try:
                    from job_extractor import extract_jobs_from_multiple_pages
                    
                    # Extract jobs from career pages (limit to 10 jobs per page to avoid timeout)
                    job_result = extract_jobs_from_multiple_pages(response_data.career_pages, max_jobs_per_page=10)
                    
                    if job_result.get("success"):
                        jobs_found = job_result.get("jobs", [])
                        logger.info(f"✅ Job extraction completed: {len(jobs_found)} jobs found")
                        
                        # Add jobs to response
                        response_data.total_jobs_found = len(jobs_found)
                        response_data.jobs = jobs_found
                        
                        # Also add to fit_markdown for backward compatibility
                        import json
                        response_data.fit_markdown = json.dumps({
                            "jobs": jobs_found,
                            "total_jobs_found": len(jobs_found),
                            "career_pages_processed": len(response_data.career_pages),
                            "job_extraction_time": time.strftime('%Y-%m-%d %H:%M:%S')
                        })
                    else:
                        logger.warning(f"⚠️ Job extraction failed: {job_result.get('error', 'Unknown error')}")
                        
                except ImportError:
                    logger.warning("⚠️ Job extractor module not available, skipping job extraction")
                except Exception as e:
                    logger.error(f"❌ Error during job extraction: {str(e)}")

            # Log extraction results
            logger.info(f"📊 Extraction results for {request.url}:")
            logger.info(f"   📧 Emails: {len(response_data.emails)}")
            logger.info(f"   🔗 Social links: {len(response_data.social_links)}")
            logger.info(f"   💼 Career pages: {len(response_data.career_pages)}")
            
            # Log job extraction results if available
            if response_data.total_jobs_found:
                logger.info(f"   💼 Jobs found: {response_data.total_jobs_found}")
    else:
        logger.error(f"❌ Crawl failed for {request.url}")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"⏱️ Total time for {request.url}: {duration:.2f}s")
    
    return response_data

@app.post("/batch_crawl_and_extract", response_model=BatchCrawlResponse)
async def batch_crawl_and_extract(request: BatchCrawlRequest):
    """
    Batch crawl multiple URLs with parallel processing
    """
    start_time = datetime.now()
    
    # Debug logging
    logger.info(f"🔍 Received request data:")
    logger.info(f"   name: {request.name}")
    logger.info(f"   domain: {request.domain}")
    logger.info(f"   phone: {request.phone}")
    logger.info(f"   description: {request.description}")
    logger.info(f"   social: {request.social}")
    logger.info(f"   career_page: {request.career_page}")
    logger.info(f"   crawl_data: {request.crawl_data}")
    
    logger.info(f"🚀 Starting batch crawl for company: {request.name}")
    
    response = BatchCrawlResponse(
        company_name=request.name,
        domain=request.domain,
        phone=request.phone,
        description=request.description
    )
    
    # Collect all URLs to crawl
    urls_to_crawl = []
    
    # Handle case where only url is provided (backward compatibility)
    if request.url and not request.domain:
        logger.info(f"🔗 Using single URL mode: {request.url}")
        urls_to_crawl.append(request.url)
        response.domain = request.url
    else:
        # Add social links
        if request.social:
            if isinstance(request.social, str):
                social_urls = [url.strip() for url in request.social.split(',') if url.strip()]
            else:
                social_urls = request.social
            urls_to_crawl.extend(social_urls)
            response.social_links = social_urls
        
        # Add career pages
        if request.career_page:
            if isinstance(request.career_page, str):
                career_urls = [url.strip() for url in request.career_page.split(',') if url.strip()]
            else:
                career_urls = request.career_page
            urls_to_crawl.extend(career_urls)
            response.career_pages = career_urls
        
        # Add main domain if available
        if request.domain and not request.domain.startswith(('http://', 'https://')):
            main_url = f"https://{request.domain}"
            urls_to_crawl.insert(0, main_url)
        elif request.domain:
            urls_to_crawl.insert(0, request.domain)
    
    response.total_urls_processed = len(urls_to_crawl)
    logger.info(f"📋 URLs to crawl: {response.total_urls_processed}")
    
    # Crawl URLs in parallel (with concurrency limit)
    semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent crawls
    
    async def crawl_with_semaphore(url: str):
        async with semaphore:
            return await crawl_single_url(url)
    
    # Create tasks for parallel execution
    tasks = [crawl_with_semaphore(url) for url in urls_to_crawl]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    all_emails = set()
    all_social_links = set()
    all_career_pages = set()
    
    for i, result in enumerate(results):
        url = urls_to_crawl[i]
        
        if isinstance(result, Exception):
            logger.error(f"❌ Error crawling {url}: {str(result)}")
            response.crawl_results.append({
                "url": url,
                "success": False,
                "error_message": str(result)
            })
            continue
        
        crawl_result = {
            "url": url,
            "success": result.get("success", False),
            "status_code": result.get("status_code"),
            "error_message": result.get("error_message"),
            "crawl_method": result.get("method", "unknown"),
            "crawl_time": result.get("crawl_time", 0),
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
        
        # Add career URLs found by improved method
        career_urls = result.get("career_urls", [])
        for career_url in career_urls:
            if career_url not in crawl_result["career_pages"]:
                crawl_result["career_pages"].append(career_url)
            if career_url not in all_career_pages:
                all_career_pages.add(career_url)
        
        response.crawl_results.append(crawl_result)
    
    # Set final results
    response.emails = sorted(list(all_emails))
    response.social_links = sorted(list(all_social_links))
    response.career_pages = sorted(list(all_career_pages))
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    response.total_crawl_time = duration
    
    logger.info(f"⏱️ Batch crawl completed in {duration:.2f}s")
    logger.info(f"📊 Results: {len(response.emails)} emails, {len(response.social_links)} social, {len(response.career_pages)} career")
    
    return response

@app.get("/stats")
async def get_crawl_stats():
    """Get crawling statistics"""
    return {
        "message": "Improved Crawl API is running",
        "timestamp": datetime.now().isoformat(),
        "cache_size": len(crawl_cache),
        "endpoints": {
            "single_crawl": "/crawl_and_extract_contact_info",
            "batch_crawl": "/batch_crawl_and_extract",
            "test_career": "/test_career_extraction",
            "extract_jobs_from_career": "/extract_jobs_from_career_pages",
            "extract_jobs_from_urls": "/extract_jobs_from_urls",
            "stats": "/stats",
            "clear_cache": "/clear_cache"
        },
        "features": {
            "playwright_primary": True,
            "requests_fallback": True,
            "parallel_processing": True,
            "caching": True,
            "vietnamese_optimized": True,
            "job_board_detection": True,
            "career_page_extraction": True,
            "enhanced_keywords": len(CAREER_KEYWORDS_VI),
            "career_selectors": len(CAREER_SELECTORS),
            "job_board_platforms": len(JOB_BOARD_DOMAINS)
        }
    }

@app.get("/clear_cache")
async def clear_cache():
    """Clear crawl cache"""
    global crawl_cache
    cache_size = len(crawl_cache)
    crawl_cache.clear()
    return {
        "message": "Cache cleared",
        "cleared_items": cache_size,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/test_career_extraction")
async def test_career_extraction(request: CrawlRequest):
    """Test endpoint specifically for career page extraction"""
    logger.info(f"🧪 Testing career extraction for: {request.url}")
    
    result = await crawl_single_url(request.url)
    
    if result.get("success"):
        career_urls = result.get("career_urls", [])
        is_job_board = is_job_board_url(request.url)
        
        return {
            "url": request.url,
            "success": True,
            "is_job_board": is_job_board,
            "career_urls_found": len(career_urls),
            "career_urls": career_urls,
            "total_urls_found": len(result.get("urls", [])),
            "crawl_method": result.get("method"),
            "crawl_time": result.get("crawl_time")
        }
    else:
        return {
            "url": request.url,
            "success": False,
            "error_message": result.get("error_message")
        }

@app.post("/extract_jobs_from_career_pages")
async def extract_jobs_from_career_pages(request: CrawlRequest):
    """
    Extract job listings from career pages
    This endpoint will:
    1. Crawl the given URL to find career pages
    2. Extract job listings from those career pages
    """
    logger.info(f"💼 Extracting jobs from career pages: {request.url}")
    
    # First, crawl the URL to find career pages
    crawl_result = await crawl_single_url(request.url)
    
    if not crawl_result.get("success"):
        return {
            "success": False,
            "source_url": request.url,
            "error": f"Crawl failed: {crawl_result.get('error_message')}",
            "jobs": []
        }
    
    # Get career pages found
    career_urls = crawl_result.get("career_urls", [])
    
    if not career_urls:
        return {
            "success": False,
            "source_url": request.url,
            "error": "No career pages found",
            "jobs": []
        }
    
    logger.info(f"📋 Found {len(career_urls)} career pages, extracting jobs...")
    
    # Import job extractor
    try:
        from job_extractor import extract_jobs_from_multiple_pages
    except ImportError:
        return {
            "success": False,
            "source_url": request.url,
            "error": "Job extractor module not available",
            "jobs": []
        }
    
    # Extract jobs from career pages
    job_result = extract_jobs_from_multiple_pages(career_urls, max_jobs_per_page=20)
    
    # Add crawl info to result
    job_result.update({
        "source_url": request.url,
        "career_pages_found": len(career_urls),
        "career_pages": career_urls,
        "crawl_method": crawl_result.get("method"),
        "crawl_time": crawl_result.get("crawl_time")
    })
    
    logger.info(f"✅ Job extraction completed: {job_result.get('total_jobs_found', 0)} jobs found")
    
    return job_result

@app.post("/extract_jobs_from_urls")
async def extract_jobs_from_urls(request: BatchCrawlRequest):
    """
    Extract job listings from a list of URLs
    Useful when you already have career page URLs
    """
    logger.info(f"💼 Extracting jobs from URLs")
    
    # Get URLs from request
    urls_to_process = []
    
    if request.career_page:
        if isinstance(request.career_page, str):
            urls_to_process = [url.strip() for url in request.career_page.split(',') if url.strip()]
        else:
            urls_to_process = request.career_page
    
    if request.url and not urls_to_process:
        urls_to_process = [request.url]
    
    if not urls_to_process:
        return {
            "success": False,
            "error": "No URLs provided",
            "jobs": []
        }
    
    logger.info(f"📋 Processing {len(urls_to_process)} URLs for job extraction...")
    
    # Import job extractor
    try:
        from job_extractor import extract_jobs_from_multiple_pages
    except ImportError:
        return {
            "success": False,
            "error": "Job extractor module not available",
            "jobs": []
        }
    
    # Extract jobs from URLs
    job_result = extract_jobs_from_multiple_pages(urls_to_process, max_jobs_per_page=20)
    
    # Add request info to result
    job_result.update({
        "company_name": request.name,
        "domain": request.domain,
        "urls_processed": urls_to_process
    })
    
    logger.info(f"✅ Job extraction completed: {job_result.get('total_jobs_found', 0)} jobs found")
    
    return job_result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)