#!/usr/bin/env python3
"""
Test script to verify the new strict career page filtering logic
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from contact_extractor import (
    process_extracted_crawl_results,
    HIGH_PRIORITY_CAREER_KEYWORDS,
    NON_CAREER_KEYWORDS,
    CAREER_PATH_PATTERNS
)

def test_career_page_filtering():
    """Test the new strict career page filtering logic"""
    
    # Test URLs - mix of good and bad career pages
    test_urls = [
        # GOOD career pages (should be accepted)
        "https://fpt.com.vn/tuyen-dung",
        "https://vng.com.vn/careers",
        "https://tma.com.vn/vi/tuyen-dung",
        "https://cmc.com.vn/career",
        "https://company.com/jobs",
        "https://company.com/careers/",
        "https://company.com/tuyen-dung/",
        "https://company.com/co-hoi-nghe-nghiep",
        "https://company.com/join-us",
        "https://company.com/work-with-us",
        
        # BAD career pages (should be rejected)
        "https://company.com/blog/job-market-trends",
        "https://company.com/news/software-development",
        "https://company.com/products/ai-development",
        "https://company.com/services/cloud-devops",
        "https://company.com/about/team",
        "https://company.com/contact/support",
        "https://company.com/industry/market-analysis",
        "https://company.com/2024/01/15/job-opportunities",
        "https://company.com/case-study/success-story",
        "https://company.com/whitepaper/technology-report",
        "https://company.com/webinar/recruitment-tips",
        "https://company.com/very/long/path/with/many/segments",
        "https://company.com/job/12345-specific-job-id",
        "https://company.com/career/abc123def456",
    ]
    
    print("🧪 Testing STRICT Career Page Filtering Logic")
    print("=" * 60)
    
    # Create test data
    test_data = []
    for url in test_urls:
        test_data.append({"label": "url", "value": url})
    
    # Process with new logic
    result = process_extracted_crawl_results(test_data, "https://company.com")
    
    accepted = result["career_pages"]
    rejected = [url for url in test_urls if url not in accepted]
    
    print(f"✅ ACCEPTED ({len(accepted)} URLs):")
    for url in accepted:
        print(f"  ✓ {url}")
    
    print(f"\n❌ REJECTED ({len(rejected)} URLs):")
    for url in rejected:
        print(f"  ✗ {url}")
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total URLs tested: {len(test_urls)}")
    print(f"  Accepted: {len(accepted)} ({len(accepted)/len(test_urls)*100:.1f}%)")
    print(f"  Rejected: {len(rejected)} ({len(rejected)/len(test_urls)*100:.1f}%)")
    
    # Test specific cases
    print(f"\n🔍 DETAILED ANALYSIS:")
    
    # Test high priority keywords
    print(f"  High Priority Keywords: {len(HIGH_PRIORITY_CAREER_KEYWORDS)}")
    print(f"  Non-Career Keywords: {len(NON_CAREER_KEYWORDS)}")
    print(f"  Career Path Patterns: {len(CAREER_PATH_PATTERNS)}")
    
    # Test specific patterns
    good_patterns = [
        "/tuyen-dung", "/careers", "/jobs", "/hiring",
        "/co-hoi", "/join-us", "/work-with-us"
    ]
    
    bad_patterns = [
        "/blog", "/news", "/product", "/service",
        "/about", "/contact", "/industry"
    ]
    
    print(f"\n  Good patterns found in accepted URLs:")
    for pattern in good_patterns:
        count = sum(1 for url in accepted if pattern in url)
        if count > 0:
            print(f"    {pattern}: {count} URLs")
    
    print(f"\n  Bad patterns found in rejected URLs:")
    for pattern in bad_patterns:
        count = sum(1 for url in rejected if pattern in url)
        if count > 0:
            print(f"    {pattern}: {count} URLs")

if __name__ == "__main__":
    test_career_page_filtering() 