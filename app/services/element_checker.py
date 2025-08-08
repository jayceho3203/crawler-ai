# app/services/element_checker.py
"""
Element checker service for job-related content
"""

import re
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

def get_domain(url: str) -> str:
    """Extract domain from URL"""
    return urlparse(url).netloc.lower()

def check_element_for_job(element, base_url: str) -> Dict:
    """
    Check if an element contains job information
    """
    try:
        # Extract text content
        text = element.get_text(strip=True)
        if not text or len(text) < 10:
            return {
                'is_likely_job': False,
                'confidence': 0.0,
                'reason': 'Text too short'
            }
        
        # Check for job-related keywords
        job_keywords = [
            'job', 'career', 'position', 'opportunity', 'vacancy',
            'hiring', 'recruitment', 'employment', 'work',
            'tuyển dụng', 'việc làm', 'cơ hội', 'vị trí',
            'nghề nghiệp', 'công việc', 'làm việc'
        ]
        
        text_lower = text.lower()
        keyword_matches = sum(1 for keyword in job_keywords if keyword in text_lower)
        
        # Check for job-related patterns
        patterns = [
            r'\b(developer|engineer|designer|manager|analyst|specialist)\b',
            r'\b(full.?time|part.?time|remote|hybrid|onsite)\b',
            r'\b(experience|skill|requirement|qualification)\b',
            r'\b(salary|compensation|benefit|package)\b',
            r'\b(apply|application|submit|join|work)\b'
        ]
        
        pattern_matches = 0
        for pattern in patterns:
            if re.search(pattern, text_lower):
                pattern_matches += 1
        
        # Calculate confidence score
        confidence = 0.0
        
        # Base score from keywords
        if keyword_matches > 0:
            confidence += min(keyword_matches * 0.2, 0.6)
        
        # Pattern score
        if pattern_matches > 0:
            confidence += min(pattern_matches * 0.15, 0.4)
        
        # Check for job-specific attributes
        if element.get('data-job') or element.get('data-position') or element.get('data-career'):
            confidence += 0.3
        
        # Check for job-related classes
        class_attr = element.get('class', [])
        if isinstance(class_attr, list):
            class_text = ' '.join(class_attr).lower()
            if any(keyword in class_text for keyword in ['job', 'career', 'position', 'opportunity']):
                confidence += 0.2
        
        # Check for job-related IDs
        id_attr = element.get('id', '').lower()
        if any(keyword in id_attr for keyword in ['job', 'career', 'position', 'opportunity']):
            confidence += 0.2
        
        # Determine if likely job
        is_likely_job = confidence >= 0.3
        
        return {
            'is_likely_job': is_likely_job,
            'confidence': min(confidence, 1.0),
            'reason': f'Keywords: {keyword_matches}, Patterns: {pattern_matches}',
            'text_preview': text[:200] + '...' if len(text) > 200 else text
        }
        
    except Exception as e:
        return {
            'is_likely_job': False,
            'confidence': 0.0,
            'reason': f'Error: {str(e)}'
        }

async def check_selectors_on_page(url: str, selectors: List[str]) -> Dict:
    """
    Check specific CSS selectors on a page for job information
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                response.raise_for_status()
                
                soup = BeautifulSoup(await response.text(), 'html.parser')
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

async def interactive_element_checker(url: str):
    """
    Interactive element checker for debugging
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                response.raise_for_status()
                
                soup = BeautifulSoup(await response.text(), 'html.parser')
                
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