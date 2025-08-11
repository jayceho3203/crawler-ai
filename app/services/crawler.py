# app/services/crawler.py
"""
Optimized crawling service for career pages, contact info, job URLs and job details
Requests-only mode for Render free tier compatibility
"""

import time
import re
import logging
from typing import Dict, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import aiohttp
import asyncio

from .cache import get_cached_result, cache_result
from ..utils.constants import (
    DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, DEFAULT_HEADERS
)

logger = logging.getLogger(__name__)

# Tối ưu timeout cho performance
OPTIMIZED_TIMEOUT = 30000  # 30 seconds for requests
PAGE_WAIT_TIMEOUT = 100  # 100ms for memory optimization

async def extract_with_requests(url: str) -> Dict:
    """Primary method using aiohttp with enhanced filtering and anti-bot headers"""
    start_time = time.time()
    
    try:
        headers = {
            'User-Agent': DEFAULT_USER_AGENT,
            'Referer': url,
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1',
            **DEFAULT_HEADERS
        }
        
        # Create SSL context that ignores certificate verification
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, headers=headers, timeout=40, allow_redirects=True) as response:
                response.raise_for_status()
                html_content = await response.text()
                
                # Extract emails using enhanced patterns
                email_patterns = [
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    r'[a-zA-Z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
                ]
                
                all_emails = []
                for pattern in email_patterns:
                    emails = re.findall(pattern, html_content, re.IGNORECASE)
                    all_emails.extend(emails)
                
                # Clean and validate emails
                valid_emails = []
                for email in all_emails:
                    email = email.strip().lower()
                    # Basic validation
                    if '@' in email and '.' in email.split('@')[1]:
                        # Skip common invalid patterns
                        if not any(invalid in email for invalid in [
                            'cropped-favicon', 'favicon', '.png', '.jpg', '.jpeg', '.gif',
                            'data:', 'javascript:', 'mailto:', 'tel:', 'http', 'https'
                        ]):
                            valid_emails.append(email)
                
                # Remove duplicates
                valid_emails = list(set(valid_emails))
                
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
                
                # Extract all URLs (tối ưu - chỉ lấy 50 URLs đầu để giảm memory)
                urls = []
                soup = BeautifulSoup(html_content, 'html.parser')
                for a_tag in soup.find_all('a', href=True)[:50]:  # Reduced to 50 for memory
                    href = a_tag.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        urls.append(full_url)
                
                crawl_time = time.time() - start_time
                logger.info(f"✅ Requests crawl completed: {url} - {crawl_time:.2f}s")
                logger.info(f"📊 Emails found: {len(valid_emails)}")
                logger.info(f"📊 URLs found: {len(urls)}")
                
                return {
                    "success": True,
                    "status_code": response.status if response else 200,
                    "url": response.url if response else url,
                    "html": html_content,
                    "emails": valid_emails,
                    "phones": list(set(phones)),
                    "urls": list(set(urls)),
                    "crawl_time": crawl_time,
                    "crawl_method": "requests_optimized"
                }
                
    except Exception as e:
        logger.error(f"❌ Requests failed for {url}: {e}")
        return {
            "success": False,
            "error_message": str(e),
            "url": url,
            "crawl_time": time.time() - start_time,
            "crawl_method": "requests_optimized"
        }

async def crawl_single_url(url: str) -> Dict:
    """Crawl single URL using requests method (Playwright disabled for Render)"""
    # Check cache first
    cached = get_cached_result(url)
    if cached:
        return cached
    
    # Always use requests method (Playwright disabled)
    logger.info(f"🚀 Starting requests crawl for: {url}")
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
        # Use the existing extract_with_requests function
        result = await extract_with_requests(url)
        
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