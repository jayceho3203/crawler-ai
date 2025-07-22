#!/usr/bin/env python3
"""
Simple test script for career extraction logic
"""
import requests
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Vietnamese career keywords for testing
CAREER_KEYWORDS_VI = [
    'tuyen-dung', 'tuyển-dụng', 'viec-lam', 'việc-làm',
    'co-hoi', 'cơ-hội', 'nhan-vien', 'nhân-viên',
    'tuyen', 'tuyển', 'ung-vien', 'ứng-viên',
    'cong-viec', 'công-việc', 'lam-viec', 'làm-việc',
    'moi', 'mời', 'thu-viec', 'thử-việc',
    'chinh-thuc', 'chính-thức'
]

def extract_career_pages_simple(url):
    """Simple career page extraction using requests only"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        print(f"🔗 Crawling: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract all URLs
        urls = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            if href:
                full_url = urljoin(url, href)
                urls.append(full_url)
        
        # Look for career-related URLs
        career_urls = []
        for url_found in urls:
            url_lower = url_found.lower()
            for keyword in CAREER_KEYWORDS_VI:
                if keyword in url_lower:
                    career_urls.append(url_found)
                    break
        
        # Remove duplicates
        career_urls = list(set(career_urls))
        
        return {
            "success": True,
            "total_urls": len(urls),
            "career_urls": career_urls,
            "career_urls_count": len(career_urls)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def test_career_extraction():
    """Test career page extraction"""
    test_urls = [
        "https://fpt.com.vn",
        "https://vng.com.vn",
        "https://tma.vn"
    ]
    
    print("🧪 Testing Career Page Extraction (Simple Version)")
    print("=" * 60)
    
    for url in test_urls:
        print(f"\n🔗 Testing: {url}")
        
        result = extract_career_pages_simple(url)
        
        if result["success"]:
            print(f"✅ Success!")
            print(f"   📊 Total URLs found: {result['total_urls']}")
            print(f"   💼 Career URLs found: {result['career_urls_count']}")
            
            if result['career_urls']:
                print(f"   📋 Career URLs:")
                for i, career_url in enumerate(result['career_urls'][:5]):  # Show first 5
                    print(f"      {i+1}. {career_url}")
                if len(result['career_urls']) > 5:
                    print(f"      ... and {len(result['career_urls']) - 5} more")
            else:
                print(f"   ❌ No career URLs found")
        else:
            print(f"❌ Failed: {result['error']}")

if __name__ == "__main__":
    print("🚀 Starting Simple Career Extraction Test")
    print()
    
    test_career_extraction()
    
    print("\n✅ Test completed!") 