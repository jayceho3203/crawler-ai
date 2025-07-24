#!/usr/bin/env python3
"""
Optimized Job extraction module - Core functionality only
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
from typing import Dict, List, Optional

def get_domain(url: str) -> str:
    """Extract domain from URL"""
    return urlparse(url).netloc.lower()

def extract_company_name(base_url: str, soup: BeautifulSoup) -> str:
    """Extract company name dynamically"""
    try:
        # Method 1: From page title
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True)
            patterns = [
                r'^([^-|]+)\s*[-|]\s*(?:Careers|Jobs|Tuyển dụng)',
                r'(?:Careers|Jobs|Tuyển dụng)\s*[-|]\s*([^-|]+)$'
            ]
            for pattern in patterns:
                match = re.search(pattern, title_text, re.IGNORECASE)
                if match:
                    company = match.group(1).strip()
                    if 2 < len(company) < 50:
                        return company
        
        # Method 2: From domain
        domain = get_domain(base_url)
        if domain:
            domain = re.sub(r'^www\.', '', domain)
            domain = re.sub(r'\.(com|vn|org|net|co|io|ai|tech|app)$', '', domain)
            company = domain.replace('-', ' ').replace('_', ' ').title()
            company = re.sub(r'\s+(Inc|Ltd|LLC|Corp|Corporation|Company|Co)\s*$', '', company, flags=re.IGNORECASE)
            if len(company) > 2:
                return company
        
        return domain if domain else "Unknown Company"
        
    except Exception as e:
        return "Unknown Company"

def extract_location_from_text(text: str) -> Optional[str]:
    """Extract location from text"""
    try:
        # Common location patterns
        patterns = [
            r'(Remote|Hybrid|On-site|Work from home|WFH)',
            r'(Hà Nội|Hanoi|HN)',
            r'(TP\.?HCM|Ho Chi Minh|HCM|Saigon)',
            r'(New York|NYC|NY)',
            r'(San Francisco|SF|Silicon Valley)',
            r'(London|UK|United Kingdom)',
            r'(Berlin|Germany)',
            r'(Singapore|SG)',
            r'(Tokyo|Japan)',
            r'(Seoul|Korea)',
            r'(Sydney|Australia)',
            r'(Toronto|Canada)',
            r'(Paris|France)',
            r'(Amsterdam|Netherlands)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
        
    except Exception as e:
        return None

def extract_job_from_element(element, base_url: str, soup: BeautifulSoup) -> Optional[Dict]:
    """Extract job from HTML element"""
    try:
        text = element.get_text(strip=True)
        if not text or len(text) < 5:
            return None
        
        # Find title
        title = None
        title_elements = element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b'])
        for title_elem in title_elements:
            title_text = title_elem.get_text(strip=True)
            if title_text and 3 < len(title_text) < 100:
                title = title_text
                break
        
        if not title:
            parts = re.split(r'[|\-–—•·]', text)
            for part in parts:
                part = part.strip()
                if part and 3 < len(part) < 100 and not part.isdigit():
                    title = part
                    break
        
        if not title:
            title = text[:100] if len(text) > 100 else text
        
        # Skip navigation elements
        if any(nav_word in title.lower() for nav_word in ['home', 'about', 'services', 'contact']):
            return None
        
        # Find job URL
        job_url = None
        link = element.find('a', href=True)
        if link:
            job_url = urljoin(base_url, link.get('href'))
        
        # Extract info
        company = extract_company_name(base_url, soup)
        location = extract_location_from_text(text)
        
        # Extract salary
        salary = None
        salary_patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:triệu|million|tr|USD|VND)',
            r'(\$\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
            r'(Phụ cấp)', r'(Thỏa thuận)', r'(Competitive)', r'(Negotiable)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                salary = match.group(0)
                break
        
        # Determine job type
        text_lower = text.lower()
        if any(word in text_lower for word in ['intern', 'internship', 'thực tập']):
            job_type = 'Internship'
        elif any(word in text_lower for word in ['part-time', 'parttime', 'bán thời gian']):
            job_type = 'Part-time'
        elif any(word in text_lower for word in ['contract', 'hợp đồng']):
            job_type = 'Contract'
        else:
            job_type = 'Full-time'
        
        return {
            'title': title,
            'company': company,
            'location': location,
            'url': job_url,
            'salary': salary,
            'job_type': job_type,
            'description': text[:200] + '...' if len(text) > 200 else text,
            'source_url': base_url,
            'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        return None

def extract_jobs_flexible(soup: BeautifulSoup, base_url: str, max_jobs: int) -> List[Dict]:
    """Flexible job extraction using multiple approaches"""
    jobs = []
    
    # Approach 1: CSS Selectors
    selectors = [
        '.job-item', '.job-listing', '.career-item', '.position-item',
        '.job-card', '.career-card', '.position-card',
        'li.job', 'li.career', 'li.position',
        'div[class*="job"]', 'div[class*="career"]', 'div[class*="position"]',
        'article', 'section', 'div[class*="item"]',
        '.wixui-repeater__item', 'div[role="listitem"]'
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            for element in elements[:max_jobs]:
                job = extract_job_from_element(element, base_url, soup)
                if job:
                    jobs.append(job)
                    if len(jobs) >= max_jobs:
                        return jobs
            if jobs:
                break
    
    # Approach 2: Text-based extraction
    if not jobs:
        page_text = soup.get_text()
        job_patterns = [
            r'tuyển dụng\s+([^,\n]+)',
            r'việc làm\s+([^,\n]+)',
            r'career\s+([^,\n]+)',
            r'job\s+([^,\n]+)',
            r'position\s+([^,\n]+)'
        ]
        
        found_titles = set()
        for pattern in job_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                title = match.strip()
                if len(title) > 3 and len(title) < 100 and title not in found_titles:
                    found_titles.add(title)
                    job = {
                        'title': title,
                        'company': extract_company_name(base_url, soup),
                        'location': extract_location_from_text(page_text),
                        'url': None,
                        'salary': None,
                        'job_type': 'Full-time',
                        'description': f"Job: {title}",
                        'source_url': base_url,
                        'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    jobs.append(job)
                    if len(jobs) >= max_jobs:
                        break
    
    return jobs

def extract_jobs_from_page(url: str, max_jobs: int = 50) -> Dict:
    """Main function to extract jobs from a career page"""
    print(f"🔍 Extracting jobs from: {url}")
    
    try:
        # Get page content
        try:
            from playwright.async_api import async_playwright
            import asyncio
            
            async def get_page_content():
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    content = await page.content()
                    await browser.close()
                    return content
            
            html_content = asyncio.run(get_page_content())
            soup = BeautifulSoup(html_content, 'html.parser')
            print(f"   ✅ Successfully crawled with Playwright")
            
        except Exception as e:
            print(f"   ⚠️ Playwright failed, trying requests: {e}")
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract jobs
        jobs = extract_jobs_flexible(soup, url, max_jobs)
        
        if not jobs:
            return {
                'success': False,
                'total_jobs_found': 0,
                'jobs': [],
                'source_url': url,
                'error': 'No jobs found'
            }
        
        print(f"   ✅ Found {len(jobs)} jobs")
        
        return {
            'success': True,
            'total_jobs_found': len(jobs),
            'jobs': jobs,
            'source_url': url
        }
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {
            'success': False,
            'total_jobs_found': 0,
            'jobs': [],
            'source_url': url,
            'error': str(e)
        } 