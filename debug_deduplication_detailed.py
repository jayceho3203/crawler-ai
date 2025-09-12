#!/usr/bin/env python3
"""
Debug deduplication logic in detail
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.crawler import crawl_single_url
from app.services.job_extraction_service import JobExtractionService

async def debug_deduplication_detailed():
    """Debug deduplication step by step"""
    
    url = "https://career.biplus.com.vn/"
    print(f"🔍 Debugging deduplication in detail for: {url}")
    
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
    for i, job in enumerate(jobs):
        print(f"  {i+1}. {job.get('title', 'No title')}")
    
    # Test deduplication step by step
    print("\n🔍 Testing deduplication step by step:")
    
    # Filter out generic/noise titles
    filtered_jobs = []
    generic_titles = ['engineer', 'developer', 'manager', 'analyst', 'assistant', 'specialist']
    noise_titles = ['nhân viên tự làm chủ', 'định hướng lead', 'tự làm chủ']
    
    print("\n--- Filtering step ---")
    for job in jobs:
        title = job.get('title', '').lower().strip()
        print(f"Checking: '{title}'")
        
        # Skip if too generic (single word)
        if len(title.split()) <= 1 and title in generic_titles:
            print(f"  ❌ Skipped: too generic")
            continue
            
        # Skip noise titles
        if any(noise in title for noise in noise_titles):
            print(f"  ❌ Skipped: noise title")
            continue
            
        # Skip if title is too short
        if len(title) < 5:
            print(f"  ❌ Skipped: too short")
            continue
            
        print(f"  ✅ Kept")
        filtered_jobs.append(job)
    
    print(f"\nFiltered jobs: {len(filtered_jobs)}")
    for i, job in enumerate(filtered_jobs):
        print(f"  {i+1}. {job.get('title', 'No title')}")
    
    # Deduplicate by title similarity
    print("\n--- Deduplication step ---")
    unique_jobs = []
    seen_titles = set()
    
    for i, job in enumerate(filtered_jobs):
        title = job.get('title', '').strip()
        title_lower = title.lower()
        print(f"\nProcessing job {i+1}: '{title}'")
        
        # Check for exact match
        if title_lower in seen_titles:
            print(f"  ❌ Skipped: exact match")
            continue
            
        # Check for similarity (fuzzy matching)
        is_duplicate = False
        for seen_title in seen_titles:
            similar = service._are_titles_similar(title_lower, seen_title)
            print(f"  Comparing with '{seen_title}': {similar}")
            if similar:
                is_duplicate = True
                break
        
        if not is_duplicate:
            print(f"  ✅ Added")
            unique_jobs.append(job)
            seen_titles.add(title_lower)
        else:
            print(f"  ❌ Skipped: duplicate")
    
    print(f"\nFinal unique jobs: {len(unique_jobs)}")
    for i, job in enumerate(unique_jobs):
        print(f"  {i+1}. {job.get('title', 'No title')}")

if __name__ == "__main__":
    asyncio.run(debug_deduplication_detailed())
