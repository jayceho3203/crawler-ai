# app/services/crawler.py
"""
Optimized crawling service for career pages, contact info, job URLs and job details
Requests-only mode for Render free tier compatibility
"""

import time
import re
import logging
import random
from typing import Dict, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import aiohttp
import asyncio

# Add Brotli support for content-encoding
try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False
    logger.warning("Brotli not available - some websites may fail to load")

# Default headers without brotli to avoid decode errors
DEFAULT_HEADERS_NO_BROTLI = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
    "Accept-Encoding": "gzip, deflate",  # Explicitly exclude brotli
    "Cache-Control": "no-cache",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}

from .cache import get_cached_result, cache_result
from ..utils.constants import (
    DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, DEFAULT_HEADERS
)

logger = logging.getLogger(__name__)

# Tối ưu timeout cho performance
OPTIMIZED_TIMEOUT = 15000  # Giảm từ 30s xuống 15s
PAGE_WAIT_TIMEOUT = 50  # Giảm từ 100ms xuống 50ms

# Enhanced anti-bot protection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
]

# Proxy list (free proxies - can be enhanced with paid proxies)
PROXY_LIST = [
    None,  # Direct connection
    # Add proxy URLs here if available
    # "http://proxy1:port",
    # "http://proxy2:port",
]

def get_random_delay():
    """Get random delay between requests to avoid rate limiting"""
    return random.uniform(0.5, 1.5)  # Giảm delay từ 1-3s xuống 0.5-1.5s

def get_enhanced_headers(url: str):
    """Get enhanced headers with anti-bot protection"""
    user_agent = random.choice(USER_AGENTS)
    
    # Randomize Accept-Language
    languages = [
        'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        'en-US,en;q=0.9,vi;q=0.8',
        'vi,en-US;q=0.9,en;q=0.8',
        'en-GB,en;q=0.9,vi;q=0.8'
    ]
    
    return {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': random.choice(languages),
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Charset': 'utf-8, iso-8859-1;q=0.5',
        'Referer': url,
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Connection': 'keep-alive',
        'X-Requested-With': 'XMLHttpRequest',
        **DEFAULT_HEADERS
    }

async def extract_with_requests(url: str) -> Dict:
    """Primary method using aiohttp with enhanced filtering and anti-bot headers"""
    start_time = time.time()
    
    try:
        # Add random delay to avoid rate limiting
        delay = get_random_delay()
        await asyncio.sleep(delay)
        
        # Enhanced retry mechanism với exponential backoff
        max_retries = 3  # Giảm từ 5 xuống 3
        html_content = None
        response = None
        
        for attempt in range(max_retries):
            try:
                # Get fresh headers for each attempt
                headers = get_enhanced_headers(url)
                
                # Always disable brotli to avoid decode errors
                headers['Accept-Encoding'] = 'gzip, deflate'
                
                # Create SSL context that ignores certificate verification
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                
                # Add timeout with exponential backoff (giảm timeout)
                timeout = aiohttp.ClientTimeout(total=15 + (attempt * 5))  # Giảm từ 30+10 xuống 15+5
                
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(url, headers=headers, timeout=timeout, allow_redirects=True) as response:
                        
                        # Handle different error status codes
                        if response.status == 403:
                            if attempt < max_retries - 1:
                                logger.warning(f"⚠️ 403 Forbidden for {url}, retrying... (attempt {attempt + 1}/{max_retries})")
                                await asyncio.sleep(1 + attempt)  # Giảm từ 2^attempt xuống 1+attempt
                                continue
                            else:
                                raise Exception(f"403 Forbidden after {max_retries} attempts")
                        
                        elif response.status == 429:  # Rate limited
                            if attempt < max_retries - 1:
                                logger.warning(f"⚠️ 429 Rate Limited for {url}, waiting longer... (attempt {attempt + 1}/{max_retries})")
                                await asyncio.sleep(2 + (attempt * 2))  # Giảm từ 5+5 xuống 2+2
                                continue
                            else:
                                raise Exception(f"429 Rate Limited after {max_retries} attempts")
                        
                        elif response.status == 503:  # Service unavailable
                            if attempt < max_retries - 1:
                                logger.warning(f"⚠️ 503 Service Unavailable for {url}, retrying... (attempt {attempt + 1}/{max_retries})")
                                await asyncio.sleep(1 + attempt)  # Giảm từ 3+2 xuống 1+attempt
                                continue
                            else:
                                raise Exception(f"503 Service Unavailable after {max_retries} attempts")
                        
                        response.raise_for_status()
                        html_content = await response.text()
                        break  # Thành công, thoát loop
                        
            except aiohttp.ClientResponseError as e:
                if e.status in [403, 429, 503] and attempt < max_retries - 1:
                    logger.warning(f"⚠️ HTTP {e.status} for {url}, retrying... (attempt {attempt + 1}/{max_retries})")
                    # Add jitter for 403 errors
                    if e.status == 403:
                        jitter = random.uniform(0.5, 1.5)
                        await asyncio.sleep(jitter + attempt)
                    else:
                        await asyncio.sleep(1 + attempt)  # Giảm từ 2^attempt xuống 1+attempt
                    continue
                else:
                    raise e
            except aiohttp.http_exceptions.ContentEncodingError as e:
                logger.warning(f"⚠️ Content encoding error for {url}: {e}")
                if attempt < max_retries - 1:
                    # Retry with explicit no-brotli headers
                    logger.info(f"🔄 Retrying {url} with gzip/deflate only...")
                    headers = DEFAULT_HEADERS_NO_BROTLI.copy()
                    headers['Referer'] = url
                    continue
                else:
                    raise e
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Timeout for {url}, retrying... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(1 + attempt)  # Giảm từ 2^attempt xuống 1+attempt
                    continue
                else:
                    raise Exception(f"Timeout after {max_retries} attempts")
        
        if html_content is None:
            raise Exception("Failed to get HTML content after all retries")
        
        # Extract emails using enhanced patterns
        logger.info(f"🔍 Processing HTML content (length: {len(html_content)})")
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
                # Filter non-HTTP URLs
                if href.startswith(('mailto:', 'tel:', 'skype:', 'javascript:', 'data:')):
                    logger.debug(f"⚠️ Skip non-HTTP URL: {href}")
                    continue
                
                full_url = urljoin(url, href)
                urls.append(full_url)
        
        crawl_time = time.time() - start_time
        logger.info(f"✅ Requests crawl completed: {url} - {crawl_time:.2f}s")
        logger.info(f"📊 Emails found: {len(valid_emails)}")
        logger.info(f"📊 URLs found: {len(urls)}")
        
        return {
            "success": True,
            "status_code": response.status if response else 200,
            "url": str(response.url) if response else url,
            "html": html_content,
            "emails": valid_emails,
            "phones": list(set(phones)),
            "urls": list(set(urls)),
            "crawl_time": crawl_time,
            "crawl_method": "requests_optimized"
        }
                
    except Exception as e:
        import traceback
        logger.exception(f"❌ Requests failed for {url}")  # tự động in traceback
        return {
            "success": False,
            "error_message": str(e),
            "url": url,
            "crawl_time": time.time() - start_time,
            "crawl_method": "requests_optimized"
        }

async def crawl_single_url(url: str) -> Dict:
    """Crawl single URL using requests method (Playwright disabled for Render)"""
    
    # Check cache first (chỉ trả về nếu có HTML đầy đủ)
    cached = get_cached_result(url)
    if cached and cached.get("html") and len(cached["html"]) > 500:  # tuỳ ngưỡng
        logger.info(f"📋 Using cached result for {url} (HTML length: {len(cached['html'])})")
        return cached
    
    # Always use requests method (Playwright disabled)
    logger.info(f"🚀 Starting requests crawl for: {url}")
    result = await extract_with_requests(url)
    
    # Debug logging
    logger.info(f"🔍 extract_with_requests result: success={result.get('success')} status={result.get('status_code')} url={result.get('url')} html_len={len(result.get('html', ''))}")
    
    # Only cache successful results with HTML content
    if result.get('success') and result.get('html') and len(result.get('html', '')) > 500:
        cache_result(url, result)
        logger.info(f"💾 Cached successful result for {url}")
    else:
        logger.warning(f"⚠️ Skip caching failed/empty result for {url}")
    
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