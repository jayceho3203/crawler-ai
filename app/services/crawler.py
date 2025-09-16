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
    # Note: logger will be defined later in the file

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

async def check_url_availability(url: str, session: aiohttp.ClientSession, timeout: aiohttp.ClientTimeout) -> Dict:
    """Check if URL is available using HEAD request first"""
    try:
        # Try HEAD request first (faster)
        async with session.head(url, timeout=timeout, allow_redirects=True, ssl=False) as response:
            if response.status in [200, 301, 302, 303, 307, 308]:
                return {
                    'available': True,
                    'status': response.status,
                    'method': 'HEAD'
                }
            elif response.status in [404, 410]:
                return {
                    'available': False,
                    'status': response.status,
                    'method': 'HEAD',
                    'error': f'Permanent error: HTTP {response.status}'
                }
            else:
                return {
                    'available': False,
                    'status': response.status,
                    'method': 'HEAD',
                    'error': f'HTTP {response.status} - {response.reason}'
                }
    except Exception as e:
        # If HEAD fails, we'll try GET anyway
        return {
            'available': None,  # Unknown, try GET
            'error': str(e),
            'method': 'HEAD'
        }

async def extract_with_requests(url: str) -> Dict:
    """Primary method using aiohttp with enhanced filtering and anti-bot headers"""
    start_time = time.time()
    
    try:
        # Skip non-HTTP URLs early (mailto:, tel:, javascript:, data:, anchors)
        if not url.startswith(("http://", "https://")) or url.startswith(("mailto:", "tel:", "javascript:", "data:", "#")):
            logger.info(f"⚠️ Skip non-HTTP URL: {url}")
            return {
                "success": False,
                "error_message": "Non-HTTP URL skipped",
                "error_type": "non_http",
                "url": url,
                "crawl_time": 0,
                "crawl_method": "requests_optimized"
            }
        # Add random delay to avoid rate limiting
        delay = get_random_delay()
        await asyncio.sleep(delay)
        
        # Enhanced retry mechanism với exponential backoff
        max_retries = 3
        html_content = None
        response = None
        last_error = None
        
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
                
                # Improved timeout configuration
                timeout = aiohttp.ClientTimeout(
                    total=20,  # Total timeout
                    connect=10,  # Connection timeout
                    sock_read=10  # Socket read timeout
                )
                
                async with aiohttp.ClientSession(connector=connector) as session:
                    # Check availability with HEAD request first (optional optimization)
                    if attempt == 0:  # Only on first attempt
                        availability = await check_url_availability(url, session, timeout)
                        if availability['available'] is False:
                            raise Exception(availability['error'])
                        elif availability['available'] is True:
                            logger.info(f"✅ URL available via HEAD: {url} (status: {availability['status']})")
                    
                    async with session.get(url, headers=headers, timeout=timeout, allow_redirects=True, ssl=False) as response:
                        
                        # Handle different error status codes with better classification
                        if response.status == 403:
                            last_error = f"403 Forbidden - likely blocked by server"
                            if attempt < max_retries - 1:
                                logger.warning(f"⚠️ {last_error} for {url}, retrying... (attempt {attempt + 1}/{max_retries})")
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                                continue
                            else:
                                raise Exception(last_error)
                        
                        elif response.status == 429:  # Rate limited
                            last_error = f"429 Rate Limited - too many requests"
                            if attempt < max_retries - 1:
                                logger.warning(f"⚠️ {last_error} for {url}, waiting longer... (attempt {attempt + 1}/{max_retries})")
                                await asyncio.sleep(3 + (attempt * 2))  # Longer wait: 3s, 5s, 7s
                                continue
                            else:
                                raise Exception(last_error)
                        
                        elif response.status == 503:  # Service unavailable
                            last_error = f"503 Service Unavailable - server overloaded"
                            if attempt < max_retries - 1:
                                logger.warning(f"⚠️ {last_error} for {url}, retrying... (attempt {attempt + 1}/{max_retries})")
                                await asyncio.sleep(2 + attempt)  # 2s, 3s, 4s
                                continue
                            else:
                                raise Exception(last_error)
                        
                        elif response.status >= 400:
                            last_error = f"HTTP {response.status} - {response.reason}"
                            if response.status in [404, 410]:  # Permanent errors
                                raise Exception(f"Permanent error: {last_error}")
                            elif attempt < max_retries - 1:
                                logger.warning(f"⚠️ {last_error} for {url}, retrying... (attempt {attempt + 1}/{max_retries})")
                                await asyncio.sleep(1 + attempt)
                                continue
                            else:
                                raise Exception(last_error)
                        
                        response.raise_for_status()
                        html_content = await response.text()
                        break  # Thành công, thoát loop
                        
            except aiohttp.ClientResponseError as e:
                last_error = f"HTTP {e.status} - {e.message}"
                if e.status in [403, 429, 503] and attempt < max_retries - 1:
                    logger.warning(f"⚠️ {last_error} for {url}, retrying... (attempt {attempt + 1}/{max_retries})")
                    # Add jitter for 403 errors
                    if e.status == 403:
                        jitter = random.uniform(0.5, 1.5)
                        await asyncio.sleep(jitter + (2 ** attempt))
                    else:
                        await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise e
            except aiohttp.http_exceptions.ContentEncodingError as e:
                last_error = f"Content encoding error: {str(e)}"
                logger.warning(f"⚠️ {last_error} for {url}")
                if attempt < max_retries - 1:
                    # Retry with explicit no-brotli headers
                    logger.info(f"🔄 Retrying {url} with gzip/deflate only...")
                    headers = DEFAULT_HEADERS_NO_BROTLI.copy()
                    headers['Referer'] = url
                    continue
                else:
                    raise e
            except asyncio.TimeoutError:
                last_error = "Connection timeout"
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ {last_error} for {url}, retrying... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise Exception(f"{last_error} after {max_retries} attempts")
            except aiohttp.ClientConnectorError as e:
                last_error = f"Connection error: {str(e)}"
                if "Name or service not known" in str(e):
                    last_error = "DNS resolution failed - domain may not exist"
                elif "Connection refused" in str(e):
                    last_error = "Connection refused - server may be down"
                elif "Network is unreachable" in str(e):
                    last_error = "Network unreachable"
                
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ {last_error} for {url}, retrying... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise Exception(last_error)
        
        if html_content is None:
            raise Exception(f"Failed to get HTML content after {max_retries} attempts. Last error: {last_error}")
        
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
        
        # Extract title and description
        title = ""
        description = ""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        try:
            # Get title
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Get description - ưu tiên meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '').strip()
            
            # Nếu không có meta description, tìm trong content
            if not description or len(description) < 50:
                # Tìm trong các thẻ có class chứa từ khóa mô tả
                desc_selectors = [
                    'p[class*="description"]', 'p[class*="about"]', 'p[class*="intro"]',
                    'div[class*="description"]', 'div[class*="about"]', 'div[class*="intro"]',
                    '.hero p', '.banner p', '.intro p', '.about p'
                ]
                
                for selector in desc_selectors:
                    desc_elem = soup.select_one(selector)
                    if desc_elem:
                        text = desc_elem.get_text().strip()
                        if len(text) > len(description):
                            description = text
                
                # Nếu vẫn chưa có, lấy đoạn văn đầu tiên dài nhất
                if not description or len(description) < 50:
                    paragraphs = soup.find_all('p')
                    for p in paragraphs:
                        text = p.get_text().strip()
                        if len(text) > 100 and len(text) > len(description):
                            description = text
                    
                    # Nếu vẫn chưa đủ dài, ghép nhiều đoạn văn lại
                    if len(description) < 200:
                        all_paragraphs = soup.find_all('p')
                        combined_text = ""
                        for p in all_paragraphs[:5]:  # Lấy 5 đoạn đầu
                            text = p.get_text().strip()
                            if len(text) > 50:  # Chỉ lấy đoạn có ý nghĩa
                                if combined_text:
                                    combined_text += " " + text
                                else:
                                    combined_text = text
                                if len(combined_text) > 300:  # Đủ dài rồi thì dừng
                                    break
                        
                        if len(combined_text) > len(description):
                            description = combined_text
        except Exception as e:
            logger.warning(f"⚠️ Error extracting title/description: {e}")

        # Extract all URLs (tối ưu - chỉ lấy 50 URLs đầu để giảm memory)
        urls = []
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
            "title": title,
            "description": description,
            "emails": valid_emails,
            "phones": list(set(phones)),
            "urls": list(set(urls)),
            "crawl_time": crawl_time,
            "crawl_method": "requests_optimized"
        }
                
    except Exception as e:
        import traceback
        error_msg = str(e)
        
        # Classify error types for better logging
        error_type = "unknown"
        if any(err in error_msg.lower() for err in ['timeout', 'connection timeout']):
            error_type = "timeout"
            logger.warning(f"⏱️ Timeout error for {url}: {error_msg}")
        elif any(err in error_msg.lower() for err in ['dns', 'name or service not known']):
            error_type = "dns"
            logger.warning(f"🌐 DNS error for {url}: {error_msg}")
        elif any(err in error_msg.lower() for err in ['connection refused', 'unreachable']):
            error_type = "connection"
            logger.warning(f"🔌 Connection error for {url}: {error_msg}")
        elif any(err in error_msg.lower() for err in ['403', 'forbidden', 'blocked']):
            error_type = "blocked"
            logger.warning(f"🚫 Blocked/Forbidden for {url}: {error_msg}")
        elif any(err in error_msg.lower() for err in ['429', 'rate limited']):
            error_type = "rate_limited"
            logger.warning(f"⏳ Rate limited for {url}: {error_msg}")
        elif any(err in error_msg.lower() for err in ['404', 'not found', '410', 'gone']):
            error_type = "not_found"
            logger.warning(f"❓ Not found for {url}: {error_msg}")
        else:
            error_type = "other"
            logger.exception(f"❌ Unexpected error for {url}: {error_msg}")
            
        return {
            "success": False,
            "error_message": error_msg,
            "error_type": error_type,
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