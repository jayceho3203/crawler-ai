# app/services/career_detector.py
"""
Career page detection and filtering logic
Enhanced with strict filtering and detailed analysis
"""

import re
from urllib.parse import urlparse
from typing import List, Dict, Tuple
from bs4 import BeautifulSoup
from ..utils.constants import (
    CAREER_KEYWORDS_VI, JOB_BOARD_DOMAINS, CAREER_SELECTORS,
    STRONG_NON_CAREER_INDICATORS, CAREER_EXACT_PATTERNS
)

def is_job_board_url(url: str) -> bool:
    """Check if URL is from a known job board platform"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Remove www. prefix for comparison
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain in JOB_BOARD_DOMAINS

def analyze_url_structure(url: str) -> Dict[str, any]:
    """Detailed analysis of URL structure for career page detection"""
    parsed = urlparse(url)
    path_lower = parsed.path.lower() if parsed.path else ""
    query_lower = parsed.query.lower()
    fragment_lower = parsed.fragment.lower() if parsed.fragment else ""
    
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
    
    return {
        'path': path_lower,
        'path_segments': path_segments,
        'path_depth': path_depth,
        'query': query_lower,
        'query_params': query_params,
        'fragment': fragment_lower,
        'full_path': f"{path_lower}?{query_lower}#{fragment_lower}"
    }

def check_early_rejection(url: str, url_analysis: Dict) -> Tuple[bool, str]:
    """Early rejection checks with detailed reasoning"""
    path_lower = url_analysis['path']
    query_lower = url_analysis['query']
    path_segments = url_analysis['path_segments']
    
    # 1. Strong non-career indicators
    for indicator in STRONG_NON_CAREER_INDICATORS:
        if indicator in path_lower or indicator in query_lower:
            return True, f"Contains non-career indicator: {indicator}"
    
    # 2. Date patterns (likely news/blog posts)
    date_patterns = [
        r'/\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD or YYYY-MM-DD
        r'/\d{4}/\d{1,2}',  # YYYY/MM
        r'/\d{1,2}/\d{4}',  # MM/YYYY
    ]
    for pattern in date_patterns:
        if re.search(pattern, path_lower):
            return True, f"Contains date pattern: {pattern}"
    
    # 3. Long IDs (likely specific content)
    id_patterns = [
        r'/[a-f0-9]{8,}',  # Long hex IDs
        r'/\d{5,}',  # Long numeric IDs
        r'/[a-z0-9]{10,}',  # Long alphanumeric IDs
    ]
    for pattern in id_patterns:
        if re.search(pattern, path_lower):
            return True, f"Contains long ID pattern: {pattern}"
    
    # 4. File extensions (likely documents/media)
    file_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                      '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.zip']
    for ext in file_extensions:
        if ext in path_lower:
            return True, f"Contains file extension: {ext}"
    
    # 5. Very deep paths (unlikely to be main career pages)
    if url_analysis['path_depth'] > 5:
        return True, f"Path too deep: {url_analysis['path_depth']} levels"
    
    # 6. Specific non-career path patterns
    non_career_paths = [
        '/admin', '/login', '/register', '/signup', '/signin',
        '/dashboard', '/profile', '/settings', '/account',
        '/cart', '/checkout', '/payment', '/order',
        '/search', '/filter', '/sort', '/category',
        '/tag', '/author', '/user', '/member'
    ]
    for pattern in non_career_paths:
        if pattern in path_lower:
            return True, f"Contains non-career path: {pattern}"
    
    return False, ""

def calculate_career_score(url: str, url_analysis: Dict) -> Tuple[int, Dict[str, int]]:
    """Calculate comprehensive career score with detailed breakdown"""
    path_lower = url_analysis['path']
    query_lower = url_analysis['query']
    path_segments = url_analysis['path_segments']
    query_params = url_analysis['query_params']
    
    score = 0
    score_breakdown = {}
    
    # HIGH PRIORITY indicators (+5 points each)
    high_priority_patterns = [
        '/tuyen-dung', '/tuyển-dụng', '/tuyendung',
        '/career', '/careers', '/job', '/jobs',
        '/recruitment', '/hiring', '/employment'
    ]
    for pattern in high_priority_patterns:
        if pattern in path_lower:
            score += 5
            score_breakdown[f'high_priority_{pattern}'] = 5
            break  # Only count the first match
    
    # MEDIUM PRIORITY indicators (+3 points each)
    medium_priority_patterns = [
        '/viec-lam', '/việc-làm', '/vieclam',
        '/co-hoi', '/cơ-hội', '/cohoi',
        '/nhan-vien', '/nhân-viên', '/nhanvien',
        '/ung-vien', '/ứng-viên', '/ungvien',
        '/position', '/positions', '/opportunity',
        '/vacancy', '/vacancies', '/apply'
    ]
    for pattern in medium_priority_patterns:
        if pattern in path_lower:
            score += 3
            score_breakdown[f'medium_priority_{pattern}'] = 3
            break
    
    # CAREER KEYWORDS (+2 points each, max 3)
    career_keyword_count = 0
    for keyword in CAREER_KEYWORDS_VI:
        if keyword in path_lower or keyword in query_lower:
            career_keyword_count += 1
            if career_keyword_count <= 3:  # Limit to 3 keywords
                score += 2
                score_breakdown[f'career_keyword_{keyword}'] = 2
    
    # EXACT CAREER PATTERNS (+4 points each)
    for pattern in CAREER_EXACT_PATTERNS:
        if pattern in path_lower:
            score += 4
            score_breakdown[f'exact_pattern_{pattern}'] = 4
            break
    
    # QUERY PARAMETER ANALYSIS (+1 point each)
    career_query_params = ['job', 'career', 'position', 'hiring', 'recruitment', 'apply']
    for param in career_query_params:
        if param in query_params:
            score += 1
            score_breakdown[f'query_param_{param}'] = 1
    
    # PATH STRUCTURE BONUS (+2 points for clean career paths)
    if path_lower in ['/career', '/careers', '/job', '/jobs', '/tuyen-dung', '/viec-lam']:
        score += 2
        score_breakdown['clean_career_path'] = 2
    
    # PENALTIES
    penalties = 0
    
    # Non-career keywords penalty (-3 points each)
    non_career_keywords = ['blog', 'news', 'article', 'product', 'service', 'about', 'contact']
    for keyword in non_career_keywords:
        if keyword in path_lower or keyword in query_lower:
            penalties -= 3
            score_breakdown[f'penalty_non_career_{keyword}'] = -3
    
    # Long paths penalty (-1 point per level over 3)
    if url_analysis['path_depth'] > 3:
        depth_penalty = -(url_analysis['path_depth'] - 3)
        penalties += depth_penalty
        score_breakdown['penalty_deep_path'] = depth_penalty
    
    # Numbers/IDs penalty (-2 points)
    if re.search(r'/\d+', path_lower) or re.search(r'/[a-f0-9]{4,}', path_lower):
        penalties -= 2
        score_breakdown['penalty_contains_ids'] = -2
    
    # Special characters penalty (-1 point)
    if re.search(r'[%&$#@!]', path_lower):
        penalties -= 1
        score_breakdown['penalty_special_chars'] = -1
    
    score += penalties
    
    return score, score_breakdown

def validate_career_page_content(url: str, html_content: str = None) -> Tuple[bool, str]:
    """Validate if the page actually contains career-related content"""
    if not html_content:
        return True, "No content to validate"  # Skip validation if no content
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check page title
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True).lower()
            career_title_indicators = ['career', 'job', 'tuyển dụng', 'việc làm', 'hiring', 'recruitment']
            if any(indicator in title_text for indicator in career_title_indicators):
                return True, "Career-related title found"
        
        # Check meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            desc_text = meta_desc.get('content', '').lower()
            if any(indicator in desc_text for indicator in career_title_indicators):
                return True, "Career-related meta description found"
        
        # Check for career-related text content
        body_text = soup.get_text().lower()
        career_text_indicators = [
            'tuyển dụng', 'việc làm', 'career', 'job', 'hiring', 'recruitment',
            'apply now', 'join our team', 'work with us', 'open position'
        ]
        
        career_text_count = sum(1 for indicator in career_text_indicators if indicator in body_text)
        if career_text_count >= 2:
            return True, f"Found {career_text_count} career text indicators"
        
        return False, "No career content validation passed"
        
    except Exception as e:
        return True, f"Validation error: {str(e)}"  # Skip validation on error

def filter_career_urls(career_urls: List[str], html_contents: Dict[str, str] = None) -> List[Dict]:
    """Apply strict filtering to career URLs with detailed analysis"""
    filtered_results = []
    
    for url_found in career_urls:
        # Step 1: URL Structure Analysis
        url_analysis = analyze_url_structure(url_found)
        
        # Step 2: Early Rejection Check
        is_rejected, rejection_reason = check_early_rejection(url_found, url_analysis)
        if is_rejected:
            continue
        
        # Step 3: Career Score Calculation
        career_score, score_breakdown = calculate_career_score(url_found, url_analysis)
        
        # Step 4: Content Validation (if HTML content available)
        html_content = html_contents.get(url_found) if html_contents else None
        content_valid, content_reason = validate_career_page_content(url_found, html_content)
        
        # Step 5: Final Decision Logic
        is_accepted = False
        acceptance_reason = ""
        
        # STRICT CRITERIA: Must meet multiple conditions
        if career_score >= 6:  # High score requirement
            if content_valid or html_content is None:  # Content validation or no content to check
                # Additional strict checks
                path_lower = url_analysis['path']
                
                # Must have clear career path pattern
                has_clear_career_pattern = any(pattern in path_lower for pattern in CAREER_EXACT_PATTERNS)
                
                # Must not be too deep
                is_reasonable_depth = url_analysis['path_depth'] <= 4
                
                # Must not contain suspicious patterns
                has_no_suspicious_patterns = not any([
                    re.search(r'/\d{4}', path_lower),  # No years
                    re.search(r'/[a-f0-9]{8,}', path_lower),  # No long hex IDs
                    re.search(r'/\d{5,}', path_lower),  # No long numeric IDs
                ])
                
                if has_clear_career_pattern and is_reasonable_depth and has_no_suspicious_patterns:
                    is_accepted = True
                    acceptance_reason = f"High score ({career_score}) with clear career pattern"
        
        # Record result with detailed analysis
        result = {
            'url': url_found,
            'is_accepted': is_accepted,
            'career_score': career_score,
            'score_breakdown': score_breakdown,
            'url_analysis': url_analysis,
            'content_valid': content_valid,
            'content_reason': content_reason,
            'acceptance_reason': acceptance_reason if is_accepted else f"Rejected: score={career_score}, content_valid={content_valid}"
        }
        
        if is_accepted:
            filtered_results.append(result)
    
    # Sort by career score (highest first)
    filtered_results.sort(key=lambda x: x['career_score'], reverse=True)
    
    return filtered_results

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
                    from urllib.parse import urljoin
                    full_url = urljoin(base_url, href)
                    # Only add if it's not the same job board
                    if not is_job_board_url(full_url):
                        career_pages.append(full_url)
        except:
            continue
    
    return list(set(career_pages)) 