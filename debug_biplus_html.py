#!/usr/bin/env python3
"""
Debug script to check HTML structure for missing BiPlus jobs
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.crawler import crawl_single_url
from bs4 import BeautifulSoup
import re

async def debug_biplus_html():
    """Debug HTML structure for missing jobs"""
    
    url = "https://career.biplus.com.vn/"
    print(f"🔍 Debugging HTML for: {url}")
    
    # Crawl the page
    result = await crawl_single_url(url)
    if not result['success']:
        print("❌ Failed to crawl page")
        return
    
    html_content = result['html']
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Get all text content
    page_text = soup.get_text()
    
    # Look for missing jobs
    missing_jobs = [
        "Thực tập sinh Hành chính nhân sự",
        "Java Developer (định hướng lead team)"
    ]
    
    print("\n🔍 Searching for missing jobs in HTML:")
    for job in missing_jobs:
        print(f"\n--- Searching for: '{job}' ---")
        
        # Search in raw HTML
        if job in html_content:
            print(f"✅ Found in raw HTML")
            # Find the context
            start = html_content.find(job)
            context = html_content[max(0, start-100):start+len(job)+100]
            print(f"Context: ...{context}...")
        else:
            print(f"❌ Not found in raw HTML")
        
        # Search in text content
        if job in page_text:
            print(f"✅ Found in text content")
            # Find the context
            start = page_text.find(job)
            context = page_text[max(0, start-100):start+len(job)+100]
            print(f"Context: ...{context}...")
        else:
            print(f"❌ Not found in text content")
        
        # Search with regex
        pattern = re.escape(job)
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        if matches:
            print(f"✅ Found with regex: {matches}")
        else:
            print(f"❌ Not found with regex")
    
    # Look for similar patterns
    print("\n🔍 Looking for similar patterns:")
    
    # Look for "Hành chính nhân sự"
    hr_patterns = [
        r'Hành chính nhân sự',
        r'hành chính nhân sự',
        r'Hành chính',
        r'nhân sự'
    ]
    
    for pattern in hr_patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        if matches:
            print(f"✅ Found pattern '{pattern}': {matches}")
    
    # Look for "Java Developer" variations
    java_patterns = [
        r'Java Developer.*?lead',
        r'Java Developer.*?team',
        r'định hướng lead',
        r'lead team'
    ]
    
    for pattern in java_patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        if matches:
            print(f"✅ Found pattern '{pattern}': {matches}")

if __name__ == "__main__":
    asyncio.run(debug_biplus_html())
