#!/usr/bin/env python3
"""
Element Checker Tool - Check if specific elements contain job information
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
            r'(Join|Work with|Careers at)\s+([A-Z][a-zA-Z\s&]+)',
            r'([A-Z][a-zA-Z\s&]+)\s+(?:is hiring|is looking for|seeks)'
        ]
        
        for pattern in company_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                job_indicators['has_company_info'] = True
                job_indicators['job_score'] += 1
                break
        
        # Check links
        links = element.find_all('a', href=True)
        job_links = []
        for link in links:
            href = link.get('href', '').lower()
            link_text = link.get_text(strip=True).lower()
            
            # Check if link looks job-related
            job_link_indicators = [
                'career', 'job', 'position', 'opportunity', 'vacancy',
                'tuyen-dung', 'viec-lam', 'co-hoi', 'apply', 'apply-now',
                'detail', 'view', 'read-more', 'learn-more'
            ]
            
            is_job_link = any(indicator in href or indicator in link_text for indicator in job_link_indicators)
            
            if is_job_link:
                job_links.append({
                    'text': link.get_text(strip=True),
                    'href': urljoin(base_url, link.get('href')),
                    'is_job_related': True
                })
                job_indicators['job_score'] += 1
        
        element_info['job_links'] = job_links
        
        # Determine if this is likely a job element
        is_job_element = job_indicators['job_score'] >= 2
        
        return {
            'element_info': element_info,
            'job_indicators': job_indicators,
            'is_job_element': is_job_element,
            'recommendation': 'EXTRACT' if is_job_element else 'SKIP'
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'is_job_element': False,
            'recommendation': 'ERROR'
        }

def check_selectors_on_page(url: str, selectors: List[str]) -> Dict:
    """
    Check multiple CSS selectors on a page for job content
    """
    print(f"🔍 Checking selectors on: {url}")
    
    try:
        # Get page content
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = {
            'url': url,
            'domain': get_domain(url),
            'selectors_checked': len(selectors),
            'elements_found': 0,
            'job_elements': 0,
            'selector_results': []
        }
        
        for selector in selectors:
            print(f"   📍 Checking selector: {selector}")
            elements = soup.select(selector)
            
            selector_result = {
                'selector': selector,
                'elements_count': len(elements),
                'job_elements_count': 0,
                'elements_analysis': []
            }
            
            for i, element in enumerate(elements[:10]):  # Limit to first 10 elements
                print(f"      Element {i+1}/{len(elements)}")
                analysis = check_element_for_job(element, url)
                selector_result['elements_analysis'].append(analysis)
                
                if analysis.get('is_job_element', False):
                    selector_result['job_elements_count'] += 1
                    results['job_elements'] += 1
            
            results['elements_found'] += len(elements)
            results['selector_results'].append(selector_result)
            
            print(f"      ✅ Found {len(elements)} elements, {selector_result['job_elements_count']} job elements")
        
        # Summary
        results['summary'] = {
            'total_elements': results['elements_found'],
            'total_job_elements': results['job_elements'],
            'success_rate': f"{(results['job_elements'] / max(results['elements_found'], 1)) * 100:.1f}%"
        }
        
        return results
        
    except Exception as e:
        return {
            'url': url,
            'error': str(e),
            'success': False
        }

def interactive_element_checker(url: str):
    """
    Interactive tool to check elements one by one
    """
    print(f"🔍 Interactive Element Checker for: {url}")
    print("=" * 60)
    
    try:
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Common selectors to try
        common_selectors = [
            '.job-item', '.job-listing', '.career-item', '.position-item',
            '.job-card', '.career-card', '.position-card',
            'li.job', 'li.career', 'li.position',
            'div[class*="job"]', 'div[class*="career"]', 'div[class*="position"]',
            'article', 'section', 'div[class*="item"]',
            '.wixui-repeater__item', 'div[role="listitem"]'
        ]
        
        print("📋 Common selectors to check:")
        for i, selector in enumerate(common_selectors, 1):
            elements = soup.select(selector)
            print(f"   {i}. {selector} → {len(elements)} elements")
        
        print("\n🎯 Enter selector to check (or 'quit' to exit):")
        
        while True:
            selector = input("Selector: ").strip()
            if selector.lower() == 'quit':
                break
            
            elements = soup.select(selector)
            print(f"   Found {len(elements)} elements")
            
            if not elements:
                print("   ❌ No elements found")
                continue
            
            # Check first few elements
            for i, element in enumerate(elements[:5]):
                print(f"\n   📍 Element {i+1}:")
                analysis = check_element_for_job(element, url)
                
                if analysis.get('is_job_element', False):
                    print(f"      ✅ LIKELY JOB ELEMENT (Score: {analysis['job_indicators']['job_score']})")
                else:
                    print(f"      ❌ NOT A JOB ELEMENT (Score: {analysis['job_indicators']['job_score']})")
                
                print(f"      Text: {analysis['element_info']['text_content'][:100]}...")
                print(f"      Keywords: {analysis['job_indicators']['found_keywords']}")
                
                if analysis['job_indicators']['has_salary_info']:
                    print(f"      💰 Has salary info")
                if analysis['job_indicators']['has_location_info']:
                    print(f"      📍 Has location info")
                if analysis['job_indicators']['has_apply_button']:
                    print(f"      🔗 Has apply button")
                
                if analysis['element_info']['job_links']:
                    print(f"      🔗 Job links: {len(analysis['element_info']['job_links'])}")
            
            if len(elements) > 5:
                print(f"   ... and {len(elements) - 5} more elements")
        
        print("👋 Goodbye!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python element_checker.py <url>                    # Interactive mode")
        print("  python element_checker.py <url> <selector1> <selector2> ...  # Batch mode")
        sys.exit(1)
    
    url = sys.argv[1]
    
    if len(sys.argv) == 2:
        # Interactive mode
        interactive_element_checker(url)
    else:
        # Batch mode
        selectors = sys.argv[2:]
        results = check_selectors_on_page(url, selectors)
        print(json.dumps(results, indent=2, ensure_ascii=False)) 