# app/services/element_checker.py
"""
Element checking service for job detection
Refactored from element_checker.py
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
from typing import Dict, List, Optional

def get_domain(url: str) -> str:
    """Extract domain from URL"""
    return urlparse(url).netloc.lower()

def check_element_for_job(element, base_url: str) -> Dict:
    """
    Check if an element contains job information
    Returns detailed analysis of the element
    """
    try:
        # Get element info
        element_info = {
            'tag': element.name,
            'classes': element.get('class', []),
            'id': element.get('id', ''),
            'text_length': len(element.get_text(strip=True)),
            'has_links': bool(element.find_all('a')),
            'has_images': bool(element.find_all('img')),
            'html_preview': str(element)[:200] + '...' if len(str(element)) > 200 else str(element)
        }
        
        # Get text content
        text = element.get_text(strip=True)
        element_info['text_content'] = text[:300] + '...' if len(text) > 300 else text
        
        # Check for job indicators
        job_indicators = {
            'has_job_keywords': False,
            'has_salary_info': False,
            'has_location_info': False,
            'has_company_info': False,
            'has_apply_button': False,
            'job_score': 0
        }
        
        # Job keywords check
        job_keywords = [
            'tuyển dụng', 'tuyển', 'việc làm', 'cơ hội', 'vị trí',
            'career', 'job', 'position', 'opportunity', 'vacancy',
            'hiring', 'recruitment', 'apply', 'application',
            'developer', 'engineer', 'analyst', 'manager', 'designer',
            'intern', 'internship', 'thực tập', 'full-time', 'part-time'
        ]
        
        text_lower = text.lower()
        found_keywords = []
        for keyword in job_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
                job_indicators['has_job_keywords'] = True
                job_indicators['job_score'] += 1
        
        job_indicators['found_keywords'] = found_keywords
        
        # Salary check
        salary_patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:triệu|million|tr|USD|VND)',
            r'(\$\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
            r'(Phụ cấp)', r'(Thỏa thuận)', r'(Competitive)', r'(Negotiable)'
        ]
        
        for pattern in salary_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                job_indicators['has_salary_info'] = True
                job_indicators['job_score'] += 2
                break
        
        # Location check
        location_patterns = [
            r'(Hà Nội|Hanoi|HN)', r'(TP\.?HCM|Ho Chi Minh|HCM|Saigon)',
            r'(Remote|Hybrid|On-site)', r'(New York|NYC|NY)',
            r'(San Francisco|SF|Silicon Valley)', r'(London|UK)',
            r'(Berlin|Germany)', r'(Singapore|SG)', r'(Tokyo|Japan)'
        ]
        
        for pattern in location_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                job_indicators['has_location_info'] = True
                job_indicators['job_score'] += 1
                break
        
        # Apply button check
        apply_indicators = ['apply', 'apply now', 'apply for', 'send resume', 'đăng ký', 'ứng tuyển']
        for indicator in apply_indicators:
            if indicator in text_lower:
                job_indicators['has_apply_button'] = True
                job_indicators['job_score'] += 2
                break
        
        # Company info check
        company_patterns = [
            r'(About|Giới thiệu|Company|Công ty)',
            r'(Founded|Thành lập|Established)',
            r'(Industry|Ngành nghề|Sector)'
        ]
        
        for pattern in company_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                job_indicators['has_company_info'] = True
                job_indicators['job_score'] += 1
                break
        
        # Combine results
        result = {
            'element_info': element_info,
            'job_indicators': job_indicators,
            'is_likely_job': job_indicators['job_score'] >= 3,
            'confidence': min(job_indicators['job_score'] / 5.0, 1.0)
        }
        
        return result
        
    except Exception as e:
        return {
            'error': str(e),
            'is_likely_job': False,
            'confidence': 0.0
        }

def check_selectors_on_page(url: str, selectors: List[str]) -> Dict:
    """
    Check specific CSS selectors on a page for job information
    """
    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                selector_results = []
                
                for element in elements[:5]:  # Limit to first 5 elements
                    result = check_element_for_job(element, url)
                    selector_results.append(result)
                
                results.append({
                    'selector': selector,
                    'elements_found': len(elements),
                    'results': selector_results
                })
                
            except Exception as e:
                results.append({
                    'selector': selector,
                    'error': str(e),
                    'elements_found': 0,
                    'results': []
                })
        
        return {
            'url': url,
            'success': True,
            'results': results
        }
        
    except Exception as e:
        return {
            'url': url,
            'success': False,
            'error': str(e),
            'results': []
        }

def interactive_element_checker(url: str):
    """
    Interactive element checker for debugging
    """
    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all elements with job-related content
        job_elements = []
        
        # Check common job-related selectors
        job_selectors = [
            '.job', '.career', '.position', '.opportunity',
            '.vacancy', '.hiring', '.recruitment',
            '[class*="job"]', '[class*="career"]', '[class*="position"]',
            '[id*="job"]', '[id*="career"]', '[id*="position"]'
        ]
        
        for selector in job_selectors:
            elements = soup.select(selector)
            for element in elements:
                result = check_element_for_job(element, url)
                if result['is_likely_job']:
                    job_elements.append({
                        'selector': selector,
                        'result': result
                    })
        
        return {
            'url': url,
            'job_elements_found': len(job_elements),
            'job_elements': job_elements
        }
        
    except Exception as e:
        return {
            'url': url,
            'error': str(e),
            'job_elements_found': 0,
            'job_elements': []
        } 