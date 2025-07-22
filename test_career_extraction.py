#!/usr/bin/env python3
"""
Test script for career page extraction
"""
import requests
import json
import time

# Test URLs - mix of company websites and job boards
TEST_URLS = [
    # Vietnamese job boards
    "https://topcv.vn",
    "https://careerbuilder.vn",
    "https://vietnamworks.com",
    
    # International job boards
    "https://linkedin.com/jobs",
    "https://indeed.com",
    
    # Company websites (should have career pages)
    "https://fpt.com.vn",
    "https://tma.vn",
    "https://vng.com.vn"
]

def test_career_extraction():
    """Test career page extraction for various URLs"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Career Page Extraction")
    print("=" * 50)
    
    for url in TEST_URLS:
        print(f"\n🔗 Testing: {url}")
        
        try:
            # Test career extraction
            response = requests.post(
                f"{base_url}/test_career_extraction",
                json={"url": url},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    print(f"✅ Success: {data.get('career_urls_found', 0)} career pages found")
                    print(f"   📊 Total URLs: {data.get('total_urls_found', 0)}")
                    print(f"   🎯 Job Board: {data.get('is_job_board', False)}")
                    print(f"   ⏱️ Time: {data.get('crawl_time', 0):.2f}s")
                    
                    # Show first few career URLs
                    career_urls = data.get('career_urls', [])
                    if career_urls:
                        print(f"   📋 Career URLs found:")
                        for i, career_url in enumerate(career_urls[:5]):  # Show first 5
                            print(f"      {i+1}. {career_url}")
                        if len(career_urls) > 5:
                            print(f"      ... and {len(career_urls) - 5} more")
                else:
                    print(f"❌ Failed: {data.get('error_message', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout")
        except requests.exceptions.ConnectionError:
            print("🔌 Connection Error - Make sure the server is running")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        time.sleep(1)  # Small delay between requests

def test_batch_crawl():
    """Test batch crawl with a company"""
    base_url = "http://localhost:8000"
    
    print("\n\n🚀 Testing Batch Crawl")
    print("=" * 50)
    
    # Test with a Vietnamese tech company
    test_data = {
        "name": "FPT Software",
        "domain": "fpt.com.vn",
        "social": ["https://linkedin.com/company/fpt-software"],
        "career_page": ["https://careers.fpt.com.vn"]
    }
    
    try:
        response = requests.post(
            f"{base_url}/batch_crawl_and_extract",
            json=test_data,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Batch crawl completed")
            print(f"   📊 URLs processed: {data.get('total_urls_processed', 0)}")
            print(f"   ✅ Successful crawls: {data.get('successful_crawls', 0)}")
            print(f"   📧 Emails found: {len(data.get('emails', []))}")
            print(f"   🔗 Social links: {len(data.get('social_links', []))}")
            print(f"   💼 Career pages: {len(data.get('career_pages', []))}")
            print(f"   ⏱️ Total time: {data.get('total_crawl_time', 0):.2f}s")
            
            if data.get('career_pages'):
                print(f"   📋 Career pages found:")
                for i, career_url in enumerate(data.get('career_pages', [])[:5]):
                    print(f"      {i+1}. {career_url}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Career Extraction Tests")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    # Test individual career extraction
    test_career_extraction()
    
    # Test batch crawl
    test_batch_crawl()
    
    print("\n✅ Tests completed!") 