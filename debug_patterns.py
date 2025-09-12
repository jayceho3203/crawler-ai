#!/usr/bin/env python3
"""
Debug script to test patterns against BiPlus HTML
"""

import asyncio
import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.crawler import crawl_single_url
from bs4 import BeautifulSoup

async def debug_patterns():
    """Debug why patterns don't match"""
    
    url = "https://career.biplus.com.vn/"
    print(f"🔍 Debugging patterns for: {url}")
    
    # Crawl the page
    result = await crawl_single_url(url)
    if not result['success']:
        print("❌ Failed to crawl page")
        return
    
    html_content = result['html']
    soup = BeautifulSoup(html_content, 'html.parser')
    page_text = soup.get_text()
    
    # Test patterns
    patterns_to_test = [
        r'(Thực tập sinh Hành chính nhân sự)',
        r'(Java Developer \(định hướng lead team\))',
        r'(Solution Delivery Engineer)(?!\s+Intern)'
    ]
    
    missing_jobs = [
        "Thực tập sinh Hành chính nhân sự",
        "Java Developer (định hướng lead team)",
        "Solution Delivery Engineer"
    ]
    
    print("\n🔍 Testing patterns:")
    for i, (pattern, job) in enumerate(zip(patterns_to_test, missing_jobs)):
        print(f"\n--- Pattern {i+1}: {pattern} ---")
        print(f"Looking for: {job}")
        
        # Test regex
        matches = re.findall(pattern, page_text, re.IGNORECASE | re.DOTALL)
        print(f"Regex matches: {matches}")
        
        # Test with different flags
        matches_dotall = re.findall(pattern, page_text, re.IGNORECASE | re.DOTALL)
        matches_multiline = re.findall(pattern, page_text, re.IGNORECASE | re.MULTILINE)
        matches_basic = re.findall(pattern, page_text, re.IGNORECASE)
        
        print(f"With DOTALL: {matches_dotall}")
        print(f"With MULTILINE: {matches_multiline}")
        print(f"Basic: {matches_basic}")
        
        # Test if job exists in text
        if job in page_text:
            print(f"✅ Job exists in text")
            # Find position
            pos = page_text.find(job)
            print(f"Position: {pos}")
            # Show context
            context = page_text[max(0, pos-50):pos+len(job)+50]
            print(f"Context: ...{context}...")
        else:
            print(f"❌ Job not found in text")
    
    # Test the actual extraction method
    print("\n🔍 Testing actual extraction method:")
    from app.services.job_extraction_service import JobExtractionService
    
    service = JobExtractionService()
    jobs = service._extract_jobs_by_patterns(page_text, patterns_to_test, url, 'debug')
    
    print(f"Extracted jobs: {len(jobs)}")
    for job in jobs:
        print(f"  - {job.get('title', 'No title')}")

if __name__ == "__main__":
    asyncio.run(debug_patterns())
