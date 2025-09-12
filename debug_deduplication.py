#!/usr/bin/env python3
"""
Debug deduplication logic
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.crawler import crawl_single_url
from app.services.job_extraction_service import JobExtractionService

async def debug_deduplication():
    """Debug why jobs are being filtered out"""
    
    url = "https://career.biplus.com.vn/"
    print(f"🔍 Debugging deduplication for: {url}")
    
    # Crawl the page
    result = await crawl_single_url(url)
    if not result['success']:
        print("❌ Failed to crawl page")
        return
    
    html_content = result['html']
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    page_text = soup.get_text()
    
    # Test patterns
    patterns = [
        r'(Thực tập sinh Hành chính nhân sự)',
        r'(Java Developer \(định hướng lead team\))',
        r'(Solution Delivery Engineer)(?!\s+Intern)'
    ]
    
    service = JobExtractionService()
    
    # Extract jobs without deduplication
    print("\n🔍 Extracting jobs without deduplication:")
    jobs = service._extract_jobs_by_patterns(page_text, patterns, url, 'debug')
    print(f"Raw jobs: {len(jobs)}")
    for job in jobs:
        print(f"  - {job.get('title', 'No title')}")
    
    # Test deduplication
    print("\n🔍 Testing deduplication:")
    deduplicated = service._deduplicate_jobs_by_title(jobs)
    print(f"Deduplicated jobs: {len(deduplicated)}")
    for job in deduplicated:
        print(f"  - {job.get('title', 'No title')}")
    
    # Test similarity function
    print("\n🔍 Testing similarity function:")
    test_titles = [
        "Java Developer (định hướng lead team)",
        "Java Developer",
        "Thực tập sinh Hành chính nhân sự",
        "Solution Delivery Engineer"
    ]
    
    for i, title1 in enumerate(test_titles):
        for j, title2 in enumerate(test_titles):
            if i != j:
                similar = service._are_titles_similar(title1.lower(), title2.lower())
                print(f"'{title1}' vs '{title2}': {similar}")

if __name__ == "__main__":
    asyncio.run(debug_deduplication())
