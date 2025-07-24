# app/services/job_extractor.py
"""
Job extraction service
Enhanced with detailed job link detection and validation
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

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
    
    job_keyword_count = 0
    for keyword in job_keywords:
        if keyword in path_lower:
            job_keyword_count += 1
            if job_keyword_count <= 3:
                score += 2
                score_breakdown[f'job_keyword_path_{keyword}'] = 2
    
    # LINK TEXT ANALYSIS (+3 points for job-related text)
    job_text_indicators = [
        'apply', 'apply now', 'apply for this position',
        'view job', 'view position', 'view opportunity',
        'job details', 'position details', 'opportunity details',
        'join our team', 'work with us', 'join us',
        'tuyển dụng', 'việc làm', 'cơ hội', 'vị trí',
        'ứng tuyển', 'nộp đơn', 'xem chi tiết',
        'developer', 'engineer', 'designer', 'manager',
        'full-time', 'part-time', 'remote', 'hybrid'
    ]
    
    for indicator in job_text_indicators:
        if indicator in text_lower:
            score += 3
            score_breakdown[f'job_text_{indicator}'] = 3
            break
    
    # QUERY PARAMETER ANALYSIS (+2 points each)
    job_query_params = ['job', 'position', 'career', 'hiring', 'recruitment', 'apply', 'id']
    for param in job_query_params:
        if param in query_params:
            score += 2
            score_breakdown[f'query_param_{param}'] = 2
    
    # ELEMENT ATTRIBUTES ANALYSIS (+2 points each)
    if element_attrs:
        # Check for job-related classes
        class_attr = element_attrs.get('class', [])
        if isinstance(class_attr, str):
            class_attr = [class_attr]
        
        job_class_indicators = ['job', 'career', 'position', 'opportunity', 'vacancy', 'apply']
        for indicator in job_class_indicators:
            if any(indicator in cls.lower() for cls in class_attr):
                score += 2
                score_breakdown[f'class_indicator_{indicator}'] = 2
                break
        
        # Check for job-related IDs
        id_attr = element_attrs.get('id', '').lower()
        for indicator in job_class_indicators:
            if indicator in id_attr:
                score += 2
                score_breakdown[f'id_indicator_{indicator}'] = 2
                break
        
        # Check for data attributes
        for attr_name, attr_value in element_attrs.items():
            if attr_name.startswith('data-') and isinstance(attr_value, str):
                attr_lower = attr_value.lower()
                for indicator in job_class_indicators:
                    if indicator in attr_lower:
                        score += 1
                        score_breakdown[f'data_attr_{attr_name}_{indicator}'] = 1
                        break
    
    # PATH STRUCTURE BONUS (+3 points for clean job paths)
    clean_job_paths = ['/job/', '/jobs/', '/position/', '/career/', '/apply/']
    if any(path in path_lower for path in clean_job_paths):
        score += 3
        score_breakdown['clean_job_path'] = 3
    
    # PENALTIES
    penalties = 0
    
    # Non-job keywords penalty (-3 points each)
    non_job_keywords = ['blog', 'news', 'article', 'product', 'service', 'about', 'contact', 'home']
    for keyword in non_job_keywords:
        if keyword in path_lower or keyword in text_lower:
            penalties -= 3
            score_breakdown[f'penalty_non_job_{keyword}'] = -3
    
    # Very deep paths penalty (-2 points per level over 4)
    if link_analysis['path_depth'] > 4:
        depth_penalty = -(link_analysis['path_depth'] - 4) * 2
        penalties += depth_penalty
        score_breakdown['penalty_deep_path'] = depth_penalty
    
    # Generic paths penalty (-2 points)
    generic_paths = ['/page/', '/item/', '/detail/', '/view/', '/show/']
    if any(path in path_lower for path in generic_paths):
        penalties -= 2
        score_breakdown['penalty_generic_path'] = -2
    
    # Numbers/IDs penalty (-1 point)
    if re.search(r'/\d+', path_lower) or re.search(r'/[a-f0-9]{4,}', path_lower):
        penalties -= 1
        score_breakdown['penalty_contains_ids'] = -1
    
    score += penalties
    
    return score, score_breakdown

def validate_job_link_content(url: str, html_content: str = None) -> Tuple[bool, str]:
    """Validate if the link leads to actual job content"""
    if not html_content:
        return True, "No content to validate"
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check page title for job indicators
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True).lower()
            job_title_indicators = [
                'job', 'position', 'career', 'opportunity', 'vacancy',
                'tuyển dụng', 'việc làm', 'cơ hội', 'vị trí'
            ]
            if any(indicator in title_text for indicator in job_title_indicators):
                return True, "Job-related title found"
        
        # Check for job application form
        form_selectors = [
            'form[action*="apply"]', 'form[action*="application"]',
            'form[action*="submit"]', 'form[action*="job"]',
            '.apply-form', '.application-form', '.job-form',
            '#apply-form', '#application-form', '#job-form'
        ]
        
        for selector in form_selectors:
            if soup.select(selector):
                return True, "Job application form found"
        
        # Check for job details sections
        job_detail_selectors = [
            '.job-details', '.position-details', '.career-details',
            '.job-description', '.position-description',
            '.job-requirements', '.position-requirements',
            '.job-benefits', '.position-benefits',
            '[class*="job-detail"]', '[class*="position-detail"]'
        ]
        
        for selector in job_detail_selectors:
            if soup.select(selector):
                return True, "Job details section found"
        
        # Check for job-related text content
        body_text = soup.get_text().lower()
        job_text_indicators = [
            'apply now', 'apply for this position', 'submit application',
            'job description', 'position requirements', 'job benefits',
            'tuyển dụng', 'việc làm', 'cơ hội', 'vị trí',
            'ứng tuyển', 'nộp đơn', 'mô tả công việc', 'yêu cầu công việc'
        ]
        
        job_text_count = sum(1 for indicator in job_text_indicators if indicator in body_text)
        if job_text_count >= 2:
            return True, f"Found {job_text_count} job text indicators"
        
        return False, "No job content validation passed"
        
    except Exception as e:
        return True, f"Validation error: {str(e)}"

def extract_job_links_detailed(soup: BeautifulSoup, base_url: str) -> List[Dict]:
    """Extract job links with detailed analysis and validation"""
    job_links = []
    
    # Comprehensive job link selectors
    job_link_selectors = [
        # Direct job links
        'a[href*="/job/"]', 'a[href*="/jobs/"]', 'a[href*="/position/"]',
        'a[href*="/career/"]', 'a[href*="/opportunity/"]', 'a[href*="/vacancy/"]',
        'a[href*="/apply/"]', 'a[href*="/application/"]',
        'a[href*="/tuyen-dung/"]', 'a[href*="/viec-lam/"]', 'a[href*="/co-hoi/"]',
        
        # Job-related classes
        '.job a', '.career a', '.position a', '.opportunity a',
        '.vacancy a', '.apply a', '.application a',
        '.job-item a', '.career-item a', '.position-item a',
        '.job-card a', '.career-card a', '.position-card a',
        
        # Generic selectors with job context
        'article a', '.card a', '.item a', '.listing a',
        '.post a', '.entry a', '.content a',
        
        # Navigation and menu links
        '.nav a', '.menu a', '.navigation a', '.navbar a',
        'nav a', 'header a', 'footer a',
        
        # Button and action links
        '.btn a', '.button a', '.action a', '.cta a',
        'button a', '[role="button"] a'
    ]
    
    for selector in job_link_selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if not href:
                    continue
                
                # Normalize URL
                full_url = urljoin(base_url, href)
                
                # Skip external links (optional)
                if not full_url.startswith(base_url):
                    continue
                
                # Extract link text and attributes
                link_text = element.get_text(strip=True)
                element_attrs = {
                    'class': element.get('class', []),
                    'id': element.get('id', ''),
                    'title': element.get('title', ''),
                    'aria-label': element.get('aria-label', ''),
                    'data-*': {k: v for k, v in element.attrs.items() if k.startswith('data-')}
                }
                
                # Calculate job link score
                job_score, score_breakdown = calculate_job_link_score(full_url, link_text, element_attrs)
                
                # Early filtering: only process links with reasonable scores
                if job_score >= 3:
                    job_links.append({
                        'url': full_url,
                        'link_text': link_text,
                        'element_attrs': element_attrs,
                        'job_score': job_score,
                        'score_breakdown': score_breakdown,
                        'selector_used': selector
                    })
        
        except Exception as e:
            continue
    
    # Remove duplicates and sort by score
    unique_links = {}
    for link in job_links:
        url = link['url']
        if url not in unique_links or link['job_score'] > unique_links[url]['job_score']:
            unique_links[url] = link
    
    # Sort by job score (highest first)
    sorted_links = sorted(unique_links.values(), key=lambda x: x['job_score'], reverse=True)
    
    return sorted_links

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
            return None
        
        # Extract job details
        job = {
            'title': title,
            'url': base_url,
            'company': extract_company_name(base_url, soup),
            'location': extract_location_from_text(text),
            'description': text[:500] + '...' if len(text) > 500 else text,
            'job_type': 'Full-time',  # Default
            'salary': None,
            'requirements': [],
            'source_url': base_url,
            'extracted_at': datetime.now().isoformat()
        }
        
        # Extract job type
        job_type_patterns = {
            'Full-time': r'\b(full.?time|toàn thời gian|chính thức)\b',
            'Part-time': r'\b(part.?time|bán thời gian|thời vụ)\b',
            'Internship': r'\b(intern|internship|thực tập|trainee)\b',
            'Remote': r'\b(remote|work from home|wfh|từ xa)\b',
            'Contract': r'\b(contract|hợp đồng|temporary)\b'
        }
        
        text_lower = text.lower()
        for job_type, pattern in job_type_patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                job['job_type'] = job_type
                break
        
        # Extract salary
        salary_patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:triệu|million|tr|USD|VND)',
            r'(\$\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
            r'(Phụ cấp|Thỏa thuận|Competitive|Negotiable)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                job['salary'] = match.group(1)
                break
        
        # Extract requirements
        requirement_keywords = [
            'experience', 'skill', 'requirement', 'qualification',
            'yêu cầu', 'kinh nghiệm', 'kỹ năng', 'trình độ'
        ]
        
        sentences = re.split(r'[.!?]', text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in requirement_keywords):
                if len(sentence.strip()) > 10:
                    job['requirements'].append(sentence.strip())
        
        return job
        
    except Exception as e:
        return None

def extract_jobs_flexible(soup: BeautifulSoup, base_url: str, max_jobs: int) -> List[Dict]:
    """Extract jobs using flexible approach"""
    jobs = []
    
    # Try different selectors for job elements
    job_selectors = [
        '.job', '.career', '.position', '.opportunity', '.vacancy',
        '.job-item', '.career-item', '.position-item',
        '[class*="job"]', '[class*="career"]', '[class*="position"]',
        'article', '.card', '.item', '.listing'
    ]
    
    for selector in job_selectors:
        if len(jobs) >= max_jobs:
            break
            
        elements = soup.select(selector)
        for element in elements:
            if len(jobs) >= max_jobs:
                break
                
            job = extract_job_from_element(element, base_url, soup)
            if job:
                # Check for duplicates
                is_duplicate = any(existing_job['title'] == job['title'] for existing_job in jobs)
                if not is_duplicate:
                    jobs.append(job)
    
    return jobs

def extract_jobs_from_page(url: str, max_jobs: int = 50) -> Dict:
    """Extract jobs from a single page with enhanced job link detection"""
    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # First, try to extract job links for detailed analysis
        job_links = extract_job_links_detailed(soup, url)
        
        # Filter job links based on score and validation
        filtered_job_links = []
        for link in job_links:
            if link['job_score'] >= 5:  # High score threshold
                # Optional: Validate job link content
                # This would require fetching each link, which might be slow
                # For now, we'll rely on the scoring system
                filtered_job_links.append(link)
        
        # Extract jobs from the main page
        jobs = extract_jobs_flexible(soup, url, max_jobs)
        
        # Add job links information to the result
        result = {
            'success': True,
            'total_jobs_found': len(jobs),
            'jobs': jobs,
            'source_url': url,
            'job_links_detected': len(job_links),
            'job_links_filtered': len(filtered_job_links),
            'top_job_links': filtered_job_links[:10]  # Top 10 job links
        }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'total_jobs_found': 0,
            'jobs': [],
            'source_url': url,
            'job_links_detected': 0,
            'job_links_filtered': 0,
            'top_job_links': []
        } 