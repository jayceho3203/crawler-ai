# app/services/job_extractor.py
"""
Optimized job extraction service for job URLs and job details
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

async def extract_job_details_from_url(job_url: str) -> Optional[Dict]:
    """Extract job details from a single job URL using Playwright for JavaScript rendering"""
    try:
        logger.info(f"   🔍 Extracting job details from: {job_url}")
        
        # Try Playwright first for JavaScript rendering
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set user agent to avoid detection
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                # Navigate to the page and wait for content to load
                await page.goto(job_url, wait_until='networkidle', timeout=30000)
                
                # Wait a bit more for dynamic content
                await page.wait_for_timeout(3000)
                
                # Extract job details using JavaScript
                job_details = await page.evaluate("""
                    () => {
                        const details = {};
                        
                        // Extract job title
                        const titleSelectors = [
                            'h1', 'h2', '.job-title', '.position-title', '.career-title',
                            '.entry-title', '.post-title', '.page-title',
                            '[data-job-title]', '[data-position-title]'
                        ];
                        
                        for (const selector of titleSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.textContent.trim()) {
                                details.job_name = element.textContent.trim();
                                break;
                            }
                        }
                        
                        // Extract job description
                        const descSelectors = [
                            '.job-description', '.description', '.content', '.job-content',
                            '.position-description', '.career-description',
                            'article', '.main-content', '.job-details',
                            '.entry-content', '.post-content', '.page-content',
                            '.job-body', '.position-body', '.career-body'
                        ];
                        
                        for (const selector of descSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.textContent.trim()) {
                                details.job_description = element.textContent.trim();
                                break;
                            }
                        }
                        
                        // Extract job type
                        const typeSelectors = [
                            '.job-type', '.position-type', '.career-type',
                            '[data-job-type]', '[data-position-type]'
                        ];
                        
                        for (const selector of typeSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.textContent.trim()) {
                                details.job_type = element.textContent.trim();
                                break;
                            }
                        }
                        
                        // Extract location
                        const locationSelectors = [
                            '.job-location', '.position-location', '.career-location',
                            '.location', '[data-location]'
                        ];
                        
                        for (const selector of locationSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.textContent.trim()) {
                                details.location = element.textContent.trim();
                                break;
                            }
                        }
                        
                        // Extract salary
                        const salarySelectors = [
                            '.job-salary', '.position-salary', '.career-salary',
                            '.salary', '[data-salary]'
                        ];
                        
                        for (const selector of salarySelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.textContent.trim()) {
                                details.salary = element.textContent.trim();
                                break;
                            }
                        }
                        
                        return details;
                    }
                """)
                
                await browser.close()
                
                # Add default values
                job_details['job_url'] = job_url
                job_details['job_name'] = job_details.get('job_name', '')
                job_details['job_description'] = job_details.get('job_description', '')
                job_details['job_type'] = job_details.get('job_type', 'Full-time')
                job_details['job_role'] = job_details.get('job_name', '')  # Use job name as role
                job_details['location'] = job_details.get('location', '')
                job_details['salary'] = job_details.get('salary', '')
                job_details['job_link'] = job_url
                
                logger.info(f"   ✅ Extracted job details: {job_details.get('job_name', 'No title')}")
                return job_details
                
        except ImportError:
            logger.warning("   ⚠️ Playwright not available, falling back to requests")
            return await extract_job_details_from_url_requests(job_url)
            
    except Exception as e:
        logger.error(f"   ❌ Error extracting job details from {job_url}: {e}")
        return None

async def extract_job_details_from_url_requests(job_url: str) -> Optional[Dict]:
    """Fallback method using requests for job details extraction"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(job_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    
                    # Parse HTML with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    job_details = {
                        'job_url': job_url,
                        'job_name': '',
                        'job_description': '',
                        'job_type': 'Full-time',
                        'job_role': '',
                        'location': '',
                        'salary': '',
                        'job_link': job_url
                    }
                    
                    # Extract job title
                    title_selectors = [
                        'h1', 'h2', '.job-title', '.position-title', '.career-title',
                        '.entry-title', '.post-title', '.page-title'
                    ]
                    
                    for selector in title_selectors:
                        element = soup.select_one(selector)
                        if element and element.get_text().strip():
                            job_details['job_name'] = element.get_text().strip()
                            job_details['job_role'] = element.get_text().strip()
                            break
                    
                    # Extract job description
                    desc_selectors = [
                        '.job-description', '.description', '.content', '.job-content',
                        '.position-description', '.career-description',
                        'article', '.main-content', '.job-details'
                    ]
                    
                    for selector in desc_selectors:
                        element = soup.select_one(selector)
                        if element and element.get_text().strip():
                            job_details['job_description'] = element.get_text().strip()
                            break
                    
                    return job_details
                    
    except Exception as e:
        logger.error(f"Error in requests fallback: {e}")
        return None

def get_domain(url: str) -> str:
    """Extract domain from URL"""
    return urlparse(url).netloc.lower()

def analyze_job_link_structure(url: str, link_text: str = "") -> Dict[str, any]:
    """Analyze job link structure for validation"""
    parsed = urlparse(url)
    path_lower = parsed.path.lower() if parsed.path else ""
    query_lower = parsed.query.lower()
    
    # Path analysis
    path_segments = [seg for seg in path_lower.strip('/').split('/') if seg]
    path_depth = len(path_segments)
    
    # Query parameters analysis
    query_params = {}
    if parsed.query:
        for param in parsed.query.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                query_params[key.lower()] = value.lower()
    
    # Link text analysis
    text_lower = link_text.lower() if link_text else ""
    
    return {
        'path': path_lower,
        'path_segments': path_segments,
        'path_depth': path_depth,
        'query': query_lower,
        'query_params': query_params,
        'link_text': text_lower,
        'full_path': f"{path_lower}?{query_lower}"
    }

def calculate_job_link_score(url: str, link_text: str = "", element_attrs: Dict = None) -> Tuple[int, Dict[str, int]]:
    """Calculate comprehensive job link score with detailed breakdown"""
    link_analysis = analyze_job_link_structure(url, link_text)
    path_lower = link_analysis['path']
    query_lower = link_analysis['query']
    text_lower = link_analysis['link_text']
    query_params = link_analysis['query_params']
    
    score = 0
    score_breakdown = {}
    
    # HIGH PRIORITY job indicators (+5 points each)
    high_priority_patterns = [
        '/job/', '/jobs/', '/position/', '/positions/',
        '/career/', '/careers/', '/opportunity/', '/opportunities/',
        '/vacancy/', '/vacancies/', '/opening/', '/openings/',
        '/apply/', '/application/', '/applications/',
        '/tuyen-dung/', '/tuyển-dụng/', '/tuyendung/',
        '/viec-lam/', '/việc-làm/', '/vieclam/',
        '/co-hoi/', '/cơ-hội/', '/cohoi/'
    ]
    
    for pattern in high_priority_patterns:
        if pattern in path_lower:
            score += 5
            score_breakdown[f'high_priority_path_{pattern}'] = 5
            break
    
    # MEDIUM PRIORITY job indicators (+3 points each)
    medium_priority_patterns = [
        '/hiring/', '/recruitment/', '/employment/',
        '/join-us/', '/joinus/', '/work-with-us/', '/workwithus/',
        '/team/', '/talent/', '/people/', '/staff/',
        '/nhan-vien/', '/nhân-viên/', '/nhanvien/',
        '/ung-vien/', '/ứng-viên/', '/ungvien/',
        '/cong-viec/', '/công-việc/', '/congviec/',
        '/lam-viec/', '/làm-việc/', '/lamviec/'
    ]
    
    for pattern in medium_priority_patterns:
        if pattern in path_lower:
            score += 3
            score_breakdown[f'medium_priority_path_{pattern}'] = 3
            break
    
    # JOB KEYWORDS IN PATH (+2 points each, max 3)
    job_keywords = [
        'developer', 'dev', 'engineer', 'programmer', 'analyst',
        'designer', 'manager', 'lead', 'architect', 'consultant',
        'specialist', 'coordinator', 'assistant', 'director',
        'frontend', 'backend', 'fullstack', 'mobile', 'web',
        'data', 'ai', 'ml', 'devops', 'qa', 'test',
        'ui', 'ux', 'product', 'business', 'marketing',
        'sales', 'customer', 'support', 'admin', 'hr'
    ]
    
    keyword_count = 0
    for keyword in job_keywords:
        if keyword in path_lower and keyword_count < 3:
            score += 2
            score_breakdown[f'job_keyword_{keyword}'] = 2
            keyword_count += 1
    
    # LINK TEXT ANALYSIS (+1 point each, max 3)
    text_keywords = [
        'job', 'career', 'position', 'opportunity', 'vacancy',
        'hiring', 'recruitment', 'employment', 'work',
        'tuyển dụng', 'việc làm', 'cơ hội', 'vị trí',
        'nghề nghiệp', 'công việc', 'làm việc'
    ]
    
    text_count = 0
    for keyword in text_keywords:
        if keyword in text_lower and text_count < 3:
            score += 1
            score_breakdown[f'text_keyword_{keyword}'] = 1
            text_count += 1
    
    # QUERY PARAMETERS (+1 point each, max 2)
    query_keywords = ['job', 'career', 'position', 'opportunity', 'vacancy']
    query_count = 0
    for keyword in query_keywords:
        if keyword in query_lower and query_count < 2:
            score += 1
            score_breakdown[f'query_keyword_{keyword}'] = 1
            query_count += 1
    
    # ELEMENT ATTRIBUTES (+1 point each, max 2)
    if element_attrs:
        attr_keywords = ['job', 'career', 'position', 'opportunity']
        attr_count = 0
        for attr_name, attr_value in element_attrs.items():
            attr_value_lower = str(attr_value).lower()
            for keyword in attr_keywords:
                if keyword in attr_value_lower and attr_count < 2:
                    score += 1
                    score_breakdown[f'attr_keyword_{keyword}'] = 1
                    attr_count += 1
                    break
    
    # PATH DEPTH BONUS (+1 point for reasonable depth)
    if 2 <= link_analysis['path_depth'] <= 4:
        score += 1
        score_breakdown['path_depth_bonus'] = 1
    
    return score, score_breakdown

def extract_job_cards_from_html(soup: BeautifulSoup, base_url: str) -> List[Dict]:
    """Extract job cards directly from HTML structure"""
    job_cards = []
    
    try:
        # Common job card selectors
        job_card_selectors = [
            'article',  # Common for job cards
            '.job-card', '.jobcard', '.job-item', '.jobitem',
            '.career-item', '.career-card', '.position-item',
            '.vacancy-item', '.opportunity-item',
            '[class*="job"]', '[class*="career"]', '[class*="position"]',
            '[class*="vacancy"]', '[class*="opportunity"]'
        ]
        
        for selector in job_card_selectors:
            cards = soup.select(selector)
            
            for card in cards:
                # Extract job title
                title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.job-title', '.position-title']
                title = ""
                for title_sel in title_selectors:
                    title_elem = card.select_one(title_sel)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        break
                
                # Extract job link
                link_elem = card.find('a', href=True)
                job_url = ""
                if link_elem:
                    job_url = urljoin(base_url, link_elem.get('href'))
                
                # Extract job description
                desc_selectors = ['.description', '.job-description', '.content', 'p']
                description = ""
                for desc_sel in desc_selectors:
                    desc_elem = card.select_one(desc_sel)
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                        break
                
                # Only add if we have a title
                if title:
                    job_cards.append({
                        'url': job_url,
                        'text': title,
                        'job_score': 10,  # High score for direct job cards
                        'score_breakdown': {'direct_job_card': 10},
                        'element_attrs': {},
                        'description': description,
                        'is_direct_card': True
                    })
        
        logger.info(f"🔍 Found {len(job_cards)} job cards directly from HTML")
        return job_cards
        
    except Exception as e:
        logger.error(f"Error extracting job cards: {e}")
        return []

def extract_job_links_detailed(soup: BeautifulSoup, base_url: str) -> List[Dict]:
    """Extract job links with detailed analysis and scoring"""
    job_links = []
    
    try:
        # Step 1: Extract job cards directly from HTML
        job_cards = extract_job_cards_from_html(soup, base_url)
        job_links.extend(job_cards)
        
        # Step 2: Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            if not href:
                continue
            
            # Normalize URL
            full_url = urljoin(base_url, href)
            
            # Skip external links and non-HTTP links
            if not full_url.startswith(('http://', 'https://')):
                continue
            
            # Get link text
            link_text = link.get_text(strip=True)
            
            # Get element attributes
            element_attrs = {}
            for attr_name, attr_value in link.attrs.items():
                if attr_name not in ['href']:
                    element_attrs[attr_name] = attr_value
            
            # Calculate job link score
            score, score_breakdown = calculate_job_link_score(full_url, link_text, element_attrs)
            
            # Only include links with reasonable scores
            if score >= 3:
                job_links.append({
                    'url': full_url,
                    'text': link_text,
                    'job_score': score,
                    'score_breakdown': score_breakdown,
                    'element_attrs': element_attrs
                })
        
        # Sort by score (highest first)
        job_links.sort(key=lambda x: x['job_score'], reverse=True)
        
    except Exception as e:
        logger.error(f"Error extracting job links: {str(e)}")
    
    return job_links

async def extract_jobs_from_page(url: str, max_jobs: int = 50) -> Dict:
    """Extract jobs from a single page with enhanced job link detection"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }) as response:
                response.raise_for_status()
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract job links for detailed analysis
                job_links = extract_job_links_detailed(soup, url)
                
                # Filter job links based on score
                filtered_job_links = []
                for link in job_links:
                    if link['job_score'] >= 5:  # High score threshold
                        filtered_job_links.append(link)
                
                # Convert job_links to jobs format
                jobs = []
                for link in filtered_job_links[:max_jobs]:
                    job = {
                        'title': link.get('text', ''),
                        'url': link.get('url', ''),
                        'company': '',  # Will be filled later
                        'location': '',
                        'job_type': 'Full-time',
                        'salary': '',
                        'posted_date': '',
                        'description': '',
                        'job_score': link.get('job_score', 0)
                    }
                    jobs.append(job)
                
                result = {
                    'success': True,
                    'total_jobs_found': len(jobs),
                    'jobs': jobs,
                    'job_links': filtered_job_links[:max_jobs],
                    'source_url': url,
                    'job_links_detected': len(job_links),
                    'job_links_filtered': len(filtered_job_links),
                    'top_job_links': filtered_job_links[:10]
                }
                
                return result
                
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'total_jobs_found': 0,
            'jobs': [],
            'job_links': [],
            'source_url': url,
            'job_links_detected': 0,
            'job_links_filtered': 0,
            'top_job_links': []
        } 