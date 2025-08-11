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
from ..utils.constants import (
    DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, DEFAULT_HEADERS
)

logger = logging.getLogger(__name__)

# Tối ưu timeout cho performance (một số site cần lâu hơn để vượt anti-bot)
OPTIMIZED_TIMEOUT = 45000  # 45 seconds
PAGE_WAIT_TIMEOUT = 100  # Reduced to 100ms for memory optimization

async def extract_with_playwright(url: str) -> Dict:
    """Primary method using Playwright for JavaScript rendering and dynamic content"""
    start_time = time.time()
    
    try:
        async with async_playwright() as p:
            # Launch browser with memory-optimized settings for Render free tier
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
                    '--disable-features=VizDisplayCompositor',
                    # Memory optimization flags
                    '--memory-pressure-off',
                    '--max_old_space_size=128',
                    '--single-process',
                    '--disable-background-networking',
                    '--disable-sync',
                    '--disable-translate',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with memory-optimized settings + basic stealth
            context = await browser.new_context(
                viewport={'width': 800, 'height': 600},  # Reduced viewport
                user_agent=DEFAULT_USER_AGENT,
                extra_http_headers=DEFAULT_HEADERS,
                ignore_https_errors=True,  # Ignore SSL certificate errors
                # Memory optimization
                java_script_enabled=True,
                bypass_csp=True,
                # Reduce memory usage
                device_scale_factor=1,
                is_mobile=False,
                has_touch=False,
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Basic stealth to reduce headless detection
            await context.add_init_script(
                """
                // webdriver flag
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                // chrome runtime
                window.chrome = { runtime: {} };
                // languages
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                // plugins length
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                """
            )
            
            page = await context.new_page()
            
            # Block heavy resources to save memory
            await page.route("**/*.{png,jpg,jpeg,gif,svg,webp,ico,woff,woff2,ttf,mp4,webm,avi,mov}", lambda route: route.abort())
            # Block unnecessary JS/CSS to reduce memory
            await page.route("**/*.{css,js}", lambda route: route.abort())
            # Block analytics and tracking
            await page.route("**/*google-analytics*", lambda route: route.abort())
            await page.route("**/*facebook*", lambda route: route.abort())
            await page.route("**/*doubleclick*", lambda route: route.abort())
            
            # Navigate to URL with optimized timeout
            logger.info(f"🌐 Playwright navigating to: {url}")
            try:
                response = await page.goto(url, wait_until='domcontentloaded', timeout=OPTIMIZED_TIMEOUT)
            except Exception:
                # Retry with a different wait strategy
                response = await page.goto(url, wait_until='load', timeout=OPTIMIZED_TIMEOUT)
            
            if not response or response.status >= 400:
                raise Exception(f"HTTP {response.status if response else 'Unknown'}")
            
            # Minimal wait to let essential content load
            await page.wait_for_timeout(PAGE_WAIT_TIMEOUT)
            
            # Extract HTML content
            html_content = await page.content()
            
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
            try:
                links = await page.query_selector_all('a[href]')
                for i, link in enumerate(links[:50]):  # Reduced from 100 to 50
                    href = await link.get_attribute('href')
                    if href:
                        full_url = urljoin(url, href)
                        urls.append(full_url)
            except:
                # Fallback to BeautifulSoup if Playwright selector fails
                soup = BeautifulSoup(html_content, 'html.parser')
                for a_tag in soup.find_all('a', href=True)[:50]:  # Reduced from 100 to 50
                    href = a_tag.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        urls.append(full_url)
            
            crawl_time = time.time() - start_time
            logger.info(f"✅ Playwright crawl completed: {url} - {crawl_time:.2f}s")
            logger.info(f"📊 Emails found: {len(valid_emails)}")
            logger.info(f"📊 URLs found: {len(urls)}")
            
            # Immediately close browser to free memory
            await context.close()
            await browser.close()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            return {
                "success": True,
                "status_code": response.status if response else 200,
                "url": response.url if response else url,
                "html": html_content,
                "emails": list(set(valid_emails)),
                "phones": list(set(phones)),
                "urls": list(set(urls)),
                "crawl_time": crawl_time,
                "crawl_method": "playwright_optimized"
            }
            
    except Exception as e:
        crawl_time = time.time() - start_time
        logger.error(f"❌ Playwright failed for {url}: {str(e)}")
        
        # Ensure browser is closed even on error to prevent memory leaks
        try:
            if 'context' in locals():
                await context.close()
            if 'browser' in locals():
                await browser.close()
        except:
            pass
        
        # Force garbage collection on error
        import gc
        gc.collect()
            
        return {
            "success": False,
            "error_message": str(e),
            "status_code": 500,
            "crawl_time": crawl_time,
            "method": "playwright"
        }

async def extract_with_requests(url: str) -> Dict:
    """Fallback method using aiohttp with enhanced filtering and anti-bot headers"""
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
                
                # Extract all URLs (tối ưu - chỉ lấy 100 URLs đầu)
                urls = []
                soup = BeautifulSoup(html_content, 'html.parser')
                for a_tag in soup.find_all('a', href=True)[:100]:  # Giới hạn 100 links
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
    """Crawl single URL with Playwright primary, requests fallback"""
    # Check cache first
    cached = get_cached_result(url)
    if cached:
        return cached
    
    # Try Playwright first (if available)
    try:
        logger.info(f"🚀 Starting Playwright crawl for: {url}")
        result = await extract_with_playwright(url)
        
        # If Playwright fails, try requests
        if not result.get("success"):
            logger.info(f"🔄 Playwright failed, trying requests fallback for: {url}")
            result = await extract_with_requests(url)
    except Exception as e:
        logger.warning(f"⚠️ Playwright not available, using requests fallback: {e}")
        # If Playwright fails to start (no browser), use requests directly
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