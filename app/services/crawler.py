# app/services/crawler.py
"""
Main crawling service using Playwright and requests
Enhanced with strict career page filtering, detailed job link detection, and hidden job extraction
"""

import time
import re
import logging
from typing import Dict, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
from playwright.async_api import async_playwright

from .cache import get_cached_result, cache_result
from .career_detector import (
    is_job_board_url, extract_career_pages_from_job_board, 
    filter_career_urls, analyze_url_structure, check_early_rejection,
    calculate_career_score, validate_career_page_content
)
from .job_extractor import extract_job_links_detailed, calculate_job_link_score
from .hidden_job_extractor import HiddenJobExtractor
from .simple_job_formatter import SimpleJobFormatter
from ..utils.constants import (
    CAREER_SELECTORS, DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, DEFAULT_HEADERS,
    JOB_LINK_SELECTORS, CAREER_SCORE_THRESHOLD, JOB_LINK_SCORE_THRESHOLD
)

logger = logging.getLogger(__name__)

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
                user_agent=DEFAULT_USER_AGENT,
                extra_http_headers=DEFAULT_HEADERS
            )
            
            page = await context.new_page()
            
            # Block unnecessary resources for faster loading
            await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf}", lambda route: route.abort())
            
            # Navigate to URL
            logger.info(f"🌐 Playwright navigating to: {url}")
            response = await page.goto(url, wait_until='domcontentloaded', timeout=DEFAULT_TIMEOUT)
            
            if not response or response.status >= 400:
                raise Exception(f"HTTP {response.status if response else 'Unknown'}")
            
            # Wait for page to be ready
            await page.wait_for_timeout(2000)
            
            # Try to find and interact with navigation elements
            try:
                nav_selectors = ['nav', '.menu', '.navigation', '.navbar', 'header']
                for selector in nav_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=3000)
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
            
            # Enhanced career URL extraction with detailed analysis
            career_urls_raw = []
            try:
                for selector in CAREER_SELECTORS:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements:
                            href = await element.get_attribute('href')
                            if href:
                                full_url = urljoin(url, href)
                                career_urls_raw.append(full_url)
                    except:
                        continue
            except:
                pass
            
            # Apply enhanced filtering with detailed analysis
            html_contents = {url: html_content}  # For content validation
            filtered_career_results = filter_career_urls(career_urls_raw, html_contents)
            career_urls = [result['url'] for result in filtered_career_results if result['is_accepted']]
            
            # Enhanced job link detection
            soup = BeautifulSoup(html_content, 'html.parser')
            job_links_detailed = extract_job_links_detailed(soup, url)
            job_links_filtered = [link for link in job_links_detailed if link['job_score'] >= JOB_LINK_SCORE_THRESHOLD]
            
            # HIDDEN JOB EXTRACTION - NEW FEATURE
            hidden_job_extractor = HiddenJobExtractor()
            hidden_jobs = await hidden_job_extractor.extract_hidden_jobs_from_page(url, page)
            
            # Extract visible jobs from the main page
            visible_jobs = await extract_visible_jobs_from_page(page)
            
            # Combine all jobs
            all_jobs = visible_jobs + hidden_jobs
            
            # Remove duplicates based on title
            unique_jobs = []
            seen_titles = set()
            for job in all_jobs:
                if job.get('title') and job['title'] not in seen_titles:
                    unique_jobs.append(job)
                    seen_titles.add(job['title'])
            
            # Check if this is a job board and extract company career pages
            if is_job_board_url(url):
                logger.info(f"🎯 Detected job board: {url}")
                job_board_career_pages = extract_career_pages_from_job_board(html_content, url)
                # Apply filtering to job board career pages too
                job_board_filtered = filter_career_urls(job_board_career_pages, html_contents)
                job_board_accepted = [result['url'] for result in job_board_filtered if result['is_accepted']]
                career_urls.extend(job_board_accepted)
                logger.info(f"📋 Found {len(job_board_accepted)} filtered company career pages from job board")
            
            await browser.close()
            
            crawl_time = time.time() - start_time
            logger.info(f"✅ Playwright crawl completed: {url} - {crawl_time:.2f}s")
            logger.info(f"📊 Career URLs: {len(career_urls_raw)} raw -> {len(career_urls)} filtered")
            logger.info(f"📊 Job Links: {len(job_links_detailed)} detected -> {len(job_links_filtered)} filtered")
            logger.info(f"🎯 Hidden Jobs: {len(hidden_jobs)} extracted")
            logger.info(f"👁️ Visible Jobs: {len(visible_jobs)} extracted")
            logger.info(f"📋 Total Unique Jobs: {len(unique_jobs)}")
            
            # Format jobs using simple formatter
            try:
                formatter = SimpleJobFormatter()
                logger.info(f"🔧 Formatting {len(unique_jobs)} jobs...")
                formatted_jobs = formatter.format_jobs_list(unique_jobs)
                job_summary = formatter.get_job_summary(unique_jobs)
                logger.info(f"✅ Jobs formatted successfully: {formatted_jobs.get('total_count', 0)} jobs")
            except Exception as e:
                logger.error(f"❌ Error formatting jobs: {str(e)}")
                formatted_jobs = {"jobs": [], "total_count": 0}
                job_summary = {"total_jobs": 0, "job_types": {}, "locations": {}}
            
            return {
                "success": True,
                "status_code": response.status if response else 200,
                "url": response.url if response else url,
                "html": html_content,
                "emails": list(set(emails)),
                "urls": list(set(urls)),
                "career_urls": list(set(career_urls)),
                "career_analysis": filtered_career_results,
                "job_links_detected": len(job_links_detailed),
                "job_links_filtered": len(job_links_filtered),
                "top_job_links": job_links_filtered[:10],
                "hidden_jobs": hidden_jobs,
                "visible_jobs": visible_jobs,
                "total_jobs": unique_jobs,
                "formatted_jobs": formatted_jobs,
                "job_summary": job_summary,
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

async def extract_visible_jobs_from_page(page) -> List[Dict]:
    """Extract visible jobs from the current page"""
    jobs = []
    
    try:
        # Common job element selectors for visible jobs
        job_selectors = [
            '.job-item', '.career-item', '.position-item',
            '.job-card', '.career-card', '.position-card',
            '.job-listing', '.career-listing', '.position-listing',
            '[data-job]', '[data-position]', '[data-career]',
            'article', '.card', '.item', '.listing'
        ]
        
        for selector in job_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    job = await extract_job_from_element_playwright(element)
                    if job:
                        jobs.append(job)
            except:
                continue
                
    except Exception as e:
        logger.error(f"Error extracting visible jobs: {str(e)}")
    
    return jobs

async def extract_job_from_element_playwright(element) -> Dict:
    """Extract job information from a Playwright element"""
    try:
        # Extract text content
        text_content = await element.text_content()
        if not text_content or len(text_content.strip()) < 10:
            return None
        
        # Extract job title
        title = await extract_job_title_playwright(element)
        if not title:
            return None
        
        # Extract other job details
        job = {
            'title': title,
            'description': text_content[:500] + '...' if len(text_content) > 500 else text_content,
            'location': await extract_job_location_playwright(element),
            'company': await extract_job_company_playwright(element),
            'job_type': await extract_job_type_playwright(element),
            'salary': await extract_job_salary_playwright(element),
            'requirements': await extract_job_requirements_playwright(element),
            'url': await extract_job_url_playwright(element),
            'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'visible'
        }
        
        return job
        
    except Exception as e:
        logger.error(f"Error extracting job from element: {str(e)}")
        return None

async def extract_job_title_playwright(element) -> str:
    """Extract job title from Playwright element"""
    try:
        # Look for title in headings
        title_selectors = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', '.title', '.job-title', '.position-title']
        
        for selector in title_selectors:
            title_elem = await element.query_selector(selector)
            if title_elem:
                title = await title_elem.text_content()
                if title and len(title.strip()) > 3:
                    return title.strip()
        
        # Look for title in data attributes
        title_attr = await element.get_attribute('data-title') or await element.get_attribute('title')
        if title_attr:
            return title_attr.strip()
        
        return None
        
    except Exception as e:
        return None

async def extract_job_location_playwright(element) -> str:
    """Extract job location from Playwright element"""
    try:
        location_selectors = ['.location', '.job-location', '.position-location', '[data-location]']
        
        for selector in location_selectors:
            location_elem = await element.query_selector(selector)
            if location_elem:
                location = await location_elem.text_content()
                if location and len(location.strip()) > 2:
                    return location.strip()
        
        return None
        
    except Exception as e:
        return None

async def extract_job_company_playwright(element) -> str:
    """Extract company name from Playwright element"""
    try:
        company_selectors = ['.company', '.job-company', '.position-company', '[data-company]']
        
        for selector in company_selectors:
            company_elem = await element.query_selector(selector)
            if company_elem:
                company = await company_elem.text_content()
                if company and len(company.strip()) > 2:
                    return company.strip()
        
        return None
        
    except Exception as e:
        return None

async def extract_job_type_playwright(element) -> str:
    """Extract job type from Playwright element"""
    try:
        type_selectors = ['.job-type', '.position-type', '.employment-type', '[data-type]']
        
        for selector in type_selectors:
            type_elem = await element.query_selector(selector)
            if type_elem:
                job_type = await type_elem.text_content()
                if job_type and len(job_type.strip()) > 2:
                    return job_type.strip()
        
        return None
        
    except Exception as e:
        return None

async def extract_job_salary_playwright(element) -> str:
    """Extract salary information from Playwright element"""
    try:
        salary_selectors = ['.salary', '.job-salary', '.position-salary', '[data-salary]']
        
        for selector in salary_selectors:
            salary_elem = await element.query_selector(selector)
            if salary_elem:
                salary = await salary_elem.text_content()
                if salary and len(salary.strip()) > 2:
                    return salary.strip()
        
        return None
        
    except Exception as e:
        return None

async def extract_job_requirements_playwright(element) -> List[str]:
    """Extract job requirements from Playwright element"""
    try:
        requirements = []
        req_selectors = ['.requirements', '.job-requirements', '.position-requirements', '.qualifications']
        
        for selector in req_selectors:
            req_elem = await element.query_selector(selector)
            if req_elem:
                req_text = await req_elem.text_content()
                if req_text:
                    # Split requirements into list
                    req_list = [req.strip() for req in req_text.split('\n') if req.strip()]
                    requirements.extend(req_list)
        
        return requirements
        
    except Exception as e:
        return []

async def extract_job_url_playwright(element) -> str:
    """Extract job URL from Playwright element"""
    try:
        # Look for link within the element
        link = await element.query_selector('a[href]')
        if link:
            href = await link.get_attribute('href')
            if href:
                return href
        
        # Look for data-url attribute
        data_url = await element.get_attribute('data-url')
        if data_url:
            return data_url
        
        return None
        
    except Exception as e:
        return None

def extract_with_requests(url: str) -> Dict:
    """Fallback method using requests with enhanced filtering"""
    start_time = time.time()
    
    try:
        headers = {
            'User-Agent': DEFAULT_USER_AGENT,
            **DEFAULT_HEADERS
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
        html_contents = {url: response.text}  # For content validation
        filtered_career_results = filter_career_urls(career_urls_raw, html_contents)
        career_urls = [result['url'] for result in filtered_career_results if result['is_accepted']]
        
        # Enhanced job link detection
        job_links_detailed = extract_job_links_detailed(soup, url)
        job_links_filtered = [link for link in job_links_detailed if link['job_score'] >= JOB_LINK_SCORE_THRESHOLD]
        
        # Extract visible jobs (limited for requests method)
        visible_jobs = extract_visible_jobs_from_soup(soup, url)
        
        crawl_time = time.time() - start_time
        logger.info(f"✅ Requests fallback completed: {url} - {crawl_time:.2f}s")
        logger.info(f"📊 Career URLs: {len(career_urls_raw)} raw -> {len(career_urls)} filtered")
        logger.info(f"📊 Job Links: {len(job_links_detailed)} detected -> {len(job_links_filtered)} filtered")
        logger.info(f"👁️ Visible Jobs: {len(visible_jobs)} extracted")
        
        # Format jobs using simple formatter
        try:
            formatter = SimpleJobFormatter()
            logger.info(f"🔧 Formatting {len(visible_jobs)} jobs...")
            formatted_jobs = formatter.format_jobs_list(visible_jobs)
            job_summary = formatter.get_job_summary(visible_jobs)
            logger.info(f"✅ Jobs formatted successfully: {formatted_jobs.get('total_count', 0)} jobs")
        except Exception as e:
            logger.error(f"❌ Error formatting jobs: {str(e)}")
            formatted_jobs = {"jobs": [], "total_count": 0}
            job_summary = {"total_jobs": 0, "job_types": {}, "locations": {}}
        
        return {
            "success": True,
            "status_code": response.status_code,
            "url": response.url,
            "html": response.text,
            "emails": list(set(emails)),
            "urls": list(set(urls)),
            "career_urls": list(set(career_urls)),
            "career_analysis": filtered_career_results,
            "job_links_detected": len(job_links_detailed),
            "job_links_filtered": len(job_links_filtered),
            "top_job_links": job_links_filtered[:10],
            "hidden_jobs": [],  # No hidden jobs with requests method
            "visible_jobs": visible_jobs,
            "total_jobs": visible_jobs,
            "formatted_jobs": formatted_jobs,
            "job_summary": job_summary,
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

def extract_visible_jobs_from_soup(soup: BeautifulSoup, base_url: str) -> List[Dict]:
    """Extract visible jobs from BeautifulSoup object"""
    jobs = []
    
    try:
        # Common job element selectors
        job_selectors = [
            '.job-item', '.career-item', '.position-item',
            '.job-card', '.career-card', '.position-card',
            '.job-listing', '.career-listing', '.position-listing',
            '[data-job]', '[data-position]', '[data-career]',
            'article', '.card', '.item', '.listing'
        ]
        
        for selector in job_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    job = extract_job_from_soup_element(element, base_url)
                    if job:
                        jobs.append(job)
            except:
                continue
                
    except Exception as e:
        logger.error(f"Error extracting visible jobs from soup: {str(e)}")
    
    return jobs

def extract_job_from_soup_element(element, base_url: str) -> Dict:
    """Extract job information from BeautifulSoup element"""
    try:
        # Extract text content
        text_content = element.get_text(strip=True)
        if not text_content or len(text_content) < 10:
            return None
        
        # Extract job title
        title = extract_job_title_soup(element)
        if not title:
            return None
        
        # Extract other job details
        job = {
            'title': title,
            'description': text_content[:500] + '...' if len(text_content) > 500 else text_content,
            'location': extract_job_location_soup(element),
            'company': extract_job_company_soup(element),
            'job_type': extract_job_type_soup(element),
            'salary': extract_job_salary_soup(element),
            'requirements': extract_job_requirements_soup(element),
            'url': extract_job_url_soup(element, base_url),
            'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'visible'
        }
        
        return job
        
    except Exception as e:
        logger.error(f"Error extracting job from soup element: {str(e)}")
        return None

def extract_job_title_soup(element) -> str:
    """Extract job title from BeautifulSoup element"""
    try:
        # Look for title in headings
        title_selectors = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', '.title', '.job-title', '.position-title']
        
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 3:
                    return title
        
        # Look for title in data attributes
        title_attr = element.get('data-title') or element.get('title')
        if title_attr:
            return title_attr.strip()
        
        return None
        
    except Exception as e:
        return None

def extract_job_location_soup(element) -> str:
    """Extract job location from BeautifulSoup element"""
    try:
        location_selectors = ['.location', '.job-location', '.position-location', '[data-location]']
        
        for selector in location_selectors:
            location_elem = element.select_one(selector)
            if location_elem:
                location = location_elem.get_text(strip=True)
                if location and len(location) > 2:
                    return location
        
        return None
        
    except Exception as e:
        return None

def extract_job_company_soup(element) -> str:
    """Extract company name from BeautifulSoup element"""
    try:
        company_selectors = ['.company', '.job-company', '.position-company', '[data-company]']
        
        for selector in company_selectors:
            company_elem = element.select_one(selector)
            if company_elem:
                company = company_elem.get_text(strip=True)
                if company and len(company) > 2:
                    return company
        
        return None
        
    except Exception as e:
        return None

def extract_job_type_soup(element) -> str:
    """Extract job type from BeautifulSoup element"""
    try:
        type_selectors = ['.job-type', '.position-type', '.employment-type', '[data-type]']
        
        for selector in type_selectors:
            type_elem = element.select_one(selector)
            if type_elem:
                job_type = type_elem.get_text(strip=True)
                if job_type and len(job_type) > 2:
                    return job_type
        
        return None
        
    except Exception as e:
        return None

def extract_job_salary_soup(element) -> str:
    """Extract salary information from BeautifulSoup element"""
    try:
        salary_selectors = ['.salary', '.job-salary', '.position-salary', '[data-salary]']
        
        for selector in salary_selectors:
            salary_elem = element.select_one(selector)
            if salary_elem:
                salary = salary_elem.get_text(strip=True)
                if salary and len(salary) > 2:
                    return salary
        
        return None
        
    except Exception as e:
        return None

def extract_job_requirements_soup(element) -> List[str]:
    """Extract job requirements from BeautifulSoup element"""
    try:
        requirements = []
        req_selectors = ['.requirements', '.job-requirements', '.position-requirements', '.qualifications']
        
        for selector in req_selectors:
            req_elem = element.select_one(selector)
            if req_elem:
                req_text = req_elem.get_text(strip=True)
                if req_text:
                    # Split requirements into list
                    req_list = [req.strip() for req in req_text.split('\n') if req.strip()]
                    requirements.extend(req_list)
        
        return requirements
        
    except Exception as e:
        return []

def extract_job_url_soup(element, base_url: str) -> str:
    """Extract job URL from BeautifulSoup element"""
    try:
        # Look for link within the element
        link = element.select_one('a[href]')
        if link:
            href = link.get('href')
            if href:
                return urljoin(base_url, href)
        
        # Look for data-url attribute
        data_url = element.get('data-url')
        if data_url:
            return urljoin(base_url, data_url)
        
        return None
        
    except Exception as e:
        return None

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