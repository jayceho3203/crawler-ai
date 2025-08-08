# app/services/crawler.py
"""
Optimized crawling service for career pages, contact info, job URLs and job details
"""

import time
import re
import logging
from typing import Dict, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from playwright.async_api import async_playwright

from .cache import get_cached_result, cache_result
from .career_detector import (
    is_job_board_url, extract_career_pages_from_job_board, 
    filter_career_urls
)
from .job_extractor import extract_job_links_detailed
from ..utils.constants import (
    CAREER_SELECTORS, DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, DEFAULT_HEADERS,
    JOB_LINK_SCORE_THRESHOLD
)

logger = logging.getLogger(__name__)

# Tối ưu timeout cho performance
OPTIMIZED_TIMEOUT = 15000  # 15 seconds
PAGE_WAIT_TIMEOUT = 200  # 200ms

async def extract_with_playwright(url: str) -> Dict:
    """Primary method using Playwright for JavaScript rendering and dynamic content"""
    start_time = time.time()
    
    try:
        async with async_playwright() as p:
            # Launch browser with optimized settings for speed
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with optimized settings
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent=DEFAULT_USER_AGENT,
                extra_http_headers=DEFAULT_HEADERS
            )
            
            page = await context.new_page()
            
            # Block unnecessary resources for faster loading
            await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,css,js,ico}", lambda route: route.abort())
            
            # Navigate to URL with optimized timeout
            logger.info(f"🌐 Playwright navigating to: {url}")
            response = await page.goto(url, wait_until='domcontentloaded', timeout=OPTIMIZED_TIMEOUT)
            
            if not response or response.status >= 400:
                raise Exception(f"HTTP {response.status if response else 'Unknown'}")
            
            # Giảm thời gian chờ xuống 200ms
            await page.wait_for_timeout(PAGE_WAIT_TIMEOUT)
            
            # Extract HTML content
            html_content = await page.content()
            
            # Extract emails using regex
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, html_content)
            
            # Extract phone numbers using regex
            phone_patterns = [
                r'\+84\s?\d{1,2}\s?\d{3}\s?\d{3}\s?\d{3}',
                r'0\d{1,2}\s?\d{3}\s?\d{3}\s?\d{3}',
                r'\d{10,11}',
            ]
            phones = []
            for pattern in phone_patterns:
                found_phones = re.findall(pattern, html_content)
                phones.extend(found_phones)
            
            # Extract all URLs (tối ưu - chỉ lấy 100 URLs đầu)
            urls = []
            try:
                links = await page.query_selector_all('a[href]')
                for i, link in enumerate(links[:100]):  # Giới hạn 100 links
                    href = await link.get_attribute('href')
                    if href:
                        full_url = urljoin(url, href)
                        urls.append(full_url)
            except:
                # Fallback to BeautifulSoup if Playwright selector fails
                soup = BeautifulSoup(html_content, 'html.parser')
                for a_tag in soup.find_all('a', href=True)[:100]:  # Giới hạn 100 links
                    href = a_tag.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        urls.append(full_url)
            
            # Enhanced career URL extraction (tối ưu)
            career_urls_raw = []
            try:
                for selector in CAREER_SELECTORS[:5]:  # Chỉ dùng 5 selectors đầu
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements[:10]:  # Giới hạn 10 elements
                            href = await element.get_attribute('href')
                            if href:
                                full_url = urljoin(url, href)
                                career_urls_raw.append(full_url)
                    except:
                        continue
            except:
                pass
            
            # Apply enhanced filtering with detailed analysis
            html_contents = {url: html_content}
            filtered_career_results = filter_career_urls(career_urls_raw, html_contents)
            career_urls = [result['url'] for result in filtered_career_results if result['is_accepted']]
            
            # Enhanced job link detection (tối ưu)
            soup = BeautifulSoup(html_content, 'html.parser')
            job_links_detailed = extract_job_links_detailed(soup, url)
            job_links_filtered = [link for link in job_links_detailed if link['job_score'] >= JOB_LINK_SCORE_THRESHOLD]
            
            # Check if this is a job board and extract company career pages (tối ưu)
            if is_job_board_url(url):
                logger.info(f"🎯 Detected job board: {url}")
                job_board_career_pages = extract_career_pages_from_job_board(html_content, url)
                # Apply filtering to job board career pages too
                job_board_filtered = filter_career_urls(job_board_career_pages, html_contents)
                job_board_accepted = [result['url'] for result in job_board_filtered if result['is_accepted']]
                career_urls.extend(job_board_accepted[:10])  # Giới hạn 10 career pages
                logger.info(f"📋 Found {len(job_board_accepted)} filtered company career pages from job board")
            
            await browser.close()
            
            crawl_time = time.time() - start_time
            logger.info(f"✅ Playwright crawl completed: {url} - {crawl_time:.2f}s")
            logger.info(f"📊 Career URLs: {len(career_urls_raw)} raw -> {len(career_urls)} filtered")
            logger.info(f"📊 Job Links: {len(job_links_detailed)} detected -> {len(job_links_filtered)} filtered")
            
            # Close browser to free memory
            await context.close()
            await browser.close()
            
            return {
                "success": True,
                "status_code": response.status if response else 200,
                "url": response.url if response else url,
                "html": html_content,
                "emails": list(set(emails)),
                "phones": list(set(phones)),
                "urls": list(set(urls)),
                "career_urls": list(set(career_urls)),
                "career_analysis": filtered_career_results,
                "job_links_detected": len(job_links_detailed),
                "job_links_filtered": len(job_links_filtered),
                "top_job_links": job_links_filtered[:10],
                "crawl_time": crawl_time,
                "method": "playwright"
            }
            
    except Exception as e:
        crawl_time = time.time() - start_time
        logger.error(f"❌ Playwright failed for {url}: {str(e)}")
        
        # Ensure browser is closed even on error
        try:
            if 'context' in locals():
                await context.close()
            if 'browser' in locals():
                await browser.close()
        except:
            pass
            
        return {
            "success": False,
            "error_message": str(e),
            "status_code": 500,
            "crawl_time": crawl_time,
            "method": "playwright"
        }

async def extract_with_requests(url: str) -> Dict:
    """Fallback method using aiohttp with enhanced filtering"""
    start_time = time.time()
    
    try:
        headers = {
            'User-Agent': DEFAULT_USER_AGENT,
            **DEFAULT_HEADERS
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=30) as response:
                response.raise_for_status()
                
                html_content = await response.text()
                
                # Extract emails using regex
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, html_content)
                
                # Extract URLs
                urls = []
                soup = BeautifulSoup(html_content, 'html.parser')
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        urls.append(full_url)
                
                # Enhanced career URL extraction
                career_urls_raw = []
                for url_found in urls:
                    url_lower = url_found.lower()
                    from ..utils.constants import CAREER_KEYWORDS_VI
                    for keyword in CAREER_KEYWORDS_VI:
                        if keyword in url_lower:
                            career_urls_raw.append(url_found)
                            break
                
                # Apply enhanced filtering with detailed analysis
                html_contents = {url: html_content}
                filtered_career_results = filter_career_urls(career_urls_raw, html_contents)
                career_urls = [result['url'] for result in filtered_career_results if result['is_accepted']]
                
                # Enhanced job link detection
                job_links_detailed = extract_job_links_detailed(soup, url)
                job_links_filtered = [link for link in job_links_detailed if link['job_score'] >= JOB_LINK_SCORE_THRESHOLD]
                
                crawl_time = time.time() - start_time
                logger.info(f"✅ Requests fallback completed: {url} - {crawl_time:.2f}s")
                logger.info(f"📊 Career URLs: {len(career_urls_raw)} raw -> {len(career_urls)} filtered")
                logger.info(f"📊 Job Links: {len(job_links_detailed)} detected -> {len(job_links_filtered)} filtered")
                
                return {
                    "success": True,
                    "status_code": response.status,
                    "url": response.url,
                    "html": html_content,
                    "emails": list(set(emails)),
                    "urls": list(set(urls)),
                    "career_urls": list(set(career_urls)),
                    "career_analysis": filtered_career_results,
                    "job_links_detected": len(job_links_detailed),
                    "job_links_filtered": len(job_links_filtered),
                    "top_job_links": job_links_filtered[:10],
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
        result = await extract_with_requests(url)
    
    # Cache the result
    cache_result(url, result)
    
    return result

async def crawl_website(url: str) -> List[Dict[str, str]]:
    """
    Crawl website and extract contact information (emails, social links, career pages)
    Returns list of dictionaries with 'label' and 'value' keys
    """
    try:
        # Use the existing extract_with_playwright function
        result = await extract_with_playwright(url)
        
        # Extract emails from the result
        emails = result.get('emails', [])
        phones = result.get('phones', [])
        extracted_data = []
        
        # Add emails
        for email in emails:
            extracted_data.append({
                'label': 'email',
                'value': email
            })
        
        # Add phones
        for phone in phones:
            extracted_data.append({
                'label': 'phone',
                'value': phone
            })
        
        # Add URLs (social links, career pages, etc.)
        urls = result.get('urls', [])
        for url_item in urls:
            extracted_data.append({
                'label': 'url',
                'value': url_item
            })
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error crawling website {url}: {e}")
        return [] 