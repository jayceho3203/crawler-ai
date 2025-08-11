# app/utils/contact_extractor.py
"""
Contact extraction utilities
Refactored from contact_extractor.py
"""

import re
from urllib.parse import urlparse, urljoin, unquote, ParseResult
from typing import List, Dict, Set, Optional

try:
    from yarl import URL
except ImportError:
    URL = None

# Import constants from the main constants file
from .constants import CAREER_KEYWORDS_VI, CAREER_EXACT_PATTERNS, REJECTED_NON_CAREER_PATHS

def to_text(v) -> str:
    """Convert any value to text, handling URL objects and bytes"""
    if isinstance(v, (bytes, bytearray)):
        return v.decode("utf-8", errors="ignore")
    if URL and isinstance(v, URL):
        return str(v)
    if isinstance(v, ParseResult):
        return v.geturl()
    return str(v)

# Social media domains
SOCIAL_DOMAINS: Set[str] = {
    "linkedin.com", "twitter.com", "facebook.com", "instagram.com",
    "github.com", "gitlab.com", "behance.net", "dribbble.com",
    "medium.com", "stackoverflow.com", "quora.com", "reddit.com",
    "producthunt.com", "angel.co", "crunchbase.com", "dev.to",
    "polywork.com", "toptal.com", "upwork.com", "freelancer.com", "x.com", "tiktok.com", "wa.me"
}

# English career keywords
CAREER_KEYWORDS: Set[str] = {
    "career", "job", "hiring", "join us", "work with us", "employment",
    "vacancy", "opportunity", "position", "recruiting", "talent",
    "apply now", "open roles", "we're hiring"
}

# High priority career keywords for strict detection
HIGH_PRIORITY_CAREER_KEYWORDS = {
    'tuyen-dung', 'career', 'job', 'recruitment', 'hiring',
    'viec-lam', 'position', 'opportunity', 'vacancy'
}

# Non-career keywords for filtering
NON_CAREER_KEYWORDS = {
    'blog', 'news', 'article', 'post', 'story', 'product', 'service',
    'about', 'contact', 'company', 'team', 'leadership', 'investor',
    'press', 'media', 'careers', 'jobs'  # These are career-related but not main career pages
}

def is_career_page_strict(url: str, title: str, content: str) -> bool:
    """
    Strict career page detection using multiple criteria
    """
    url_lower = url.lower()
    title_lower = title.lower()
    content_lower = content.lower()
    
    # Check URL patterns
    url_score = 0
    for pattern in CAREER_EXACT_PATTERNS:
        if pattern in url_lower:
            url_score += 3
            break
    
    # Check for career keywords in URL
    for keyword in HIGH_PRIORITY_CAREER_KEYWORDS:
        if keyword in url_lower:
            url_score += 2
            break
    
    # Check title for career indicators
    title_score = 0
    career_title_indicators = [
        'career', 'job', 'hiring', 'recruitment', 'tuyển dụng', 'việc làm',
        'opportunity', 'position', 'vacancy', 'join us', 'work with us'
    ]
    
    for indicator in career_title_indicators:
        if indicator in title_lower:
            title_score += 2
            break
    
    # Check content for career indicators
    content_score = 0
    career_content_indicators = [
        'apply now', 'send resume', 'submit application', 'đăng ký',
        'ứng tuyển', 'gửi CV', 'nộp đơn', 'job description', 'requirements'
    ]
    
    for indicator in career_content_indicators:
        if indicator in content_lower:
            content_score += 1
    
    # Penalty for non-career indicators
    penalty = 0
    for keyword in NON_CAREER_KEYWORDS:
        if keyword in url_lower:
            penalty -= 2
    
    total_score = url_score + title_score + content_score + penalty
    
    # Must have positive score and at least one strong indicator
    return total_score > 0 and (url_score >= 2 or title_score >= 2)

def extract_valid_email(email_str: str) -> Optional[str]:
    """Extract and validate email address"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Skip image files and invalid emails
    if any(ext in email_str.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico']):
        return None
    
    match = re.search(email_pattern, email_str)
    if match:
        email = match.group(0).lower()
        # Additional validation
        if len(email) > 5 and '@' in email and '.' in email.split('@')[1]:
            return email
    return None

def extract_valid_phone(phone_str: str) -> Optional[str]:
    """Extract and validate phone number"""
    # Remove common prefixes and clean up
    phone = re.sub(r'[^\d+\-\s\(\)]', '', phone_str)
    
    # Vietnamese phone patterns - more strict
    vn_patterns = [
        r'\+84\s?\d{1,2}\s?\d{3}\s?\d{3}\s?\d{3}',  # +84 1900 638399
        r'0\d{1,2}\s?\d{3}\s?\d{3}\s?\d{3}',         # 01900 638399
        r'\d{10,11}',                                 # 1900638399
    ]
    
    for pattern in vn_patterns:
        match = re.search(pattern, phone)
        if match:
            phone_number = match.group(0)
            
            # Additional validation: must be reasonable length and format
            clean_number = re.sub(r'[^\d]', '', phone_number)
            
            # Must be 10-11 digits for Vietnamese numbers
            if len(clean_number) >= 10 and len(clean_number) <= 11:
                # Must start with valid Vietnamese prefixes
                valid_prefixes = ['0', '84', '+84']
                if any(clean_number.startswith(prefix) for prefix in valid_prefixes):
                    return phone_number
    
    return None



def extract_embedded_url(href_content: str, base_domain_netloc: Optional[str] = None) -> str:
    """Extract URL from href content with proper handling"""
    try:
        # Remove common prefixes/suffixes
        href_content = href_content.strip()
        
        # Handle mailto: links
        if href_content.startswith('mailto:'):
            return href_content
        
        # Handle tel: links
        if href_content.startswith('tel:'):
            return href_content
        
        # Handle javascript: links
        if href_content.startswith('javascript:'):
            return href_content
        
        # Handle relative URLs
        if href_content.startswith('/'):
            if base_domain_netloc:
                return f"https://{base_domain_netloc}{href_content}"
            return href_content
        
        # Handle protocol-relative URLs
        if href_content.startswith('//'):
            return f"https:{href_content}"
        
        # Handle absolute URLs
        if href_content.startswith(('http://', 'https://')):
            return href_content
        
        # Handle relative URLs without leading slash
        if base_domain_netloc and not href_content.startswith(('http://', 'https://', 'mailto:', 'tel:', 'javascript:')):
            return f"https://{base_domain_netloc}/{href_content}"
        
        return href_content
        
    except Exception:
        return href_content

def normalize_url(url_str: str, base_url: str) -> str:
    """Normalize URL with proper handling of various formats"""
    try:
        # Convert URL objects to string first
        url_str = to_text(url_str)
        base_url = to_text(base_url)
        
        # Clean the URL
        url_str = url_str.strip()
        
        # Handle empty or invalid URLs
        if not url_str or url_str == '#':
            return base_url
        
        # Parse base URL
        base_parsed = urlparse(base_url)
        base_domain = base_parsed.netloc
        
        # Extract embedded URL
        extracted_url = extract_embedded_url(url_str, base_domain)
        
        # Handle relative URLs
        if not extracted_url.startswith(('http://', 'https://', 'mailto:', 'tel:', 'javascript:')):
            if extracted_url.startswith('/'):
                extracted_url = f"https://{base_domain}{extracted_url}"
            else:
                extracted_url = f"https://{base_domain}/{extracted_url}"
        
        # Clean up the URL
        extracted_url = extracted_url.replace(' ', '%20')
        extracted_url = unquote(extracted_url)
        
        return extracted_url
        
    except Exception:
        return base_url

def process_extracted_crawl_results(
    raw_extracted_list: List[Dict[str, str]],
    base_url: str
) -> Dict[str, List[str]]:
    """
    Process raw extracted data and classify into categories
    """
    emails = set()
    social_links = set()
    phones = set()
    
    base_domain = urlparse(base_url).netloc.lower()
    
    for item in raw_extracted_list:
        label = item.get('label', '').lower()
        value = item.get('value', '').strip()
        
        if not value:
            continue
        
        # Process emails
        if label == 'email':
            email = extract_valid_email(value)
            if email:
                emails.add(email)
        
        # Process phone numbers
        elif label == 'phone':
            phone = extract_valid_phone(value)
            if phone:
                phones.add(phone)
        
        # Process URLs - only contact-related URLs
        elif label == 'url':
            # Convert value to text first to handle URL objects
            url_value = to_text(value)
            normalized_url = normalize_url(url_value, base_url)
            
            # Reject non-HTTP URLs (mailto, tel, javascript, etc.)
            if not normalized_url.startswith(('http://', 'https://')):
                continue
            
            # Check if it's a social media link
            url_domain = urlparse(normalized_url).netloc.lower()
            if any(social_domain in url_domain for social_domain in SOCIAL_DOMAINS):
                social_links.add(normalized_url)
            
            # Only add contact-related URLs (contact, about, etc.)
            url_lower = normalized_url.lower()
            contact_keywords = ['contact', 'about', 'team', 'company', 'lien-he', 'gioi-thieu']
            
            is_contact_related = False
            for keyword in contact_keywords:
                if keyword in url_lower:
                    is_contact_related = True
                    break
            
            # Don't add career pages to contact info
            # Don't add general URLs that are not contact-related
    
    return {
        'emails': sorted(list(emails)),
        'phones': sorted(list(phones)),
        'social_links': sorted(list(social_links)),
        'website': base_url
    }

async def extract_contact_info_from_url(url: str) -> Dict[str, List[str]]:
    """
    Extract contact information from a company website URL
    """
    try:
        # Import here to avoid circular imports
        from app.services.crawler import crawl_website
        
        # Crawl the website to get raw data
        raw_data = await crawl_website(url)
        
        # Process the extracted data
        contact_info = process_extracted_crawl_results(raw_data, url)
        
        return contact_info
        
    except Exception as e:
        print(f"Error extracting contact info from {url}: {e}")
        return {
            'emails': [],
            'social_links': [],
            'career_pages': []
        } 