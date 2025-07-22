#!/usr/bin/env python3
"""
Debug script to analyze FPT recruitment page structure
"""
import requests
from bs4 import BeautifulSoup
import re

def analyze_fpt_structure():
    """Analyze the structure of tuyendung.fpt.com"""
    url = "https://tuyendung.fpt.com"
    
    print(f"🔍 Analyzing structure of: {url}")
    print("=" * 60)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"📄 Page title: {soup.title.string if soup.title else 'No title'}")
        print()
        
        # Look for job-related content
        print("🔍 Looking for job-related content...")
        
        # Check for job listings in different ways
        job_patterns = [
            r'\.Net Developer',
            r'Business Analyst',
            r'iOS Developer', 
            r'Data Scientist',
            r'AI Engineer',
            r'Frontend Developer',
            r'Trưởng nhóm',
            r'Tester',
            r'Data Analyst'
        ]
        
        page_text = soup.get_text()
        found_jobs = []
        
        for pattern in job_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                found_jobs.extend(matches)
        
        print(f"   Found job titles in text: {len(found_jobs)}")
        for job in found_jobs[:10]:
            print(f"      - {job}")
        
        # Look for specific elements that might contain jobs
        print(f"\n🔍 Looking for job containers...")
        
        # Check for common job container selectors
        selectors_to_check = [
            '.job-list', '.job-item', '.career-list', '.career-item',
            '.position-list', '.position-item', '.vacancy-list', '.vacancy-item',
            '.tuyen-dung-list', '.tuyen-dung-item', '.viec-lam-list', '.viec-lam-item',
            '.co-hoi-list', '.co-hoi-item', '.nhan-vien-list', '.nhan-vien-item',
            '.job', '.career', '.position', '.vacancy', '.opportunity',
            '.item', '.listing', '.card', '.post', '.entry'
        ]
        
        for selector in selectors_to_check:
            elements = soup.select(selector)
            if elements:
                print(f"   Selector '{selector}': {len(elements)} elements")
                for i, elem in enumerate(elements[:2]):
                    text = elem.get_text(strip=True)[:100]
                    classes = ' '.join(elem.get('class', []))
                    print(f"      Element {i+1}: {text}... (classes: {classes})")
        
        # Look for links that might be job links
        print(f"\n🔍 Looking for job-related links...")
        
        job_links = []
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            link_href = link.get('href')
            
            if not link_text or len(link_text) < 3:
                continue
            
            # Check if this looks like a job link
            text_lower = link_text.lower()
            href_lower = link_href.lower()
            
            job_keywords = [
                'developer', 'engineer', 'analyst', 'tester', 'designer',
                'frontend', 'backend', 'fullstack', 'mobile', 'ios', 'android',
                'data', 'ai', 'devops', 'qa', 'ba', 'pm', 'manager', 'leader',
                'senior', 'junior', 'middle', 'trưởng nhóm', 'lập trình',
                'kiểm thử', 'phân tích', 'thiết kế', 'quản lý'
            ]
            
            for keyword in job_keywords:
                if keyword in text_lower or keyword in href_lower:
                    job_links.append({
                        'text': link_text,
                        'href': link_href,
                        'keyword': keyword
                    })
                    break
        
        print(f"   Found {len(job_links)} potential job links")
        for i, link in enumerate(job_links[:10]):
            print(f"      {i+1}. {link['text']} -> {link['href']} (keyword: {link['keyword']})")
        
        # Look for specific job titles mentioned in the image
        print(f"\n🔍 Looking for specific job titles from the image...")
        
        specific_jobs = [
            '.Net Developer', 'Business Analyst', 'iOS Developer', 'Data Scientist',
            'AI Engineer', 'Frontend Developer', 'Trưởng nhóm Lập trình', 'Tester',
            'Data Analyst'
        ]
        
        for job_title in specific_jobs:
            if job_title in page_text:
                print(f"   ✅ Found: {job_title}")
            else:
                print(f"   ❌ Not found: {job_title}")
        
        # Check if this is a different page than expected
        print(f"\n🔍 Page analysis summary:")
        print(f"   URL: {response.url}")
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)} characters")
        
        # Look for redirects or different content
        if 'tuyendung.fpt.com' not in response.url:
            print(f"   ⚠️  Page was redirected to: {response.url}")
        
    except Exception as e:
        print(f"❌ Error analyzing page: {e}")

if __name__ == "__main__":
    analyze_fpt_structure() 