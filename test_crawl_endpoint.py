#!/usr/bin/env python3
"""
Test script for crawl_and_extract_contact_info endpoint
"""
import requests
import json

def test_crawl_endpoint():
    """Test the crawl_and_extract_contact_info endpoint"""
    base_url = "http://localhost:8000"
    
    # Test URLs - Vietnamese companies that should have career pages
    test_urls = [
        "https://fpt.com.vn",
        "https://vng.com.vn", 
        "https://tma.vn",
        "https://topcv.vn",
        "https://careerbuilder.vn"
    ]
    
    print("🧪 Testing crawl_and_extract_contact_info endpoint")
    print("=" * 60)
    
    for url in test_urls:
        print(f"\n🔗 Testing: {url}")
        
        try:
            response = requests.post(
                f"{base_url}/crawl_and_extract_contact_info",
                json={"url": url},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    print(f"✅ Success!")
                    print(f"   📧 Emails: {len(data.get('emails', []))}")
                    print(f"   🔗 Social links: {len(data.get('social_links', []))}")
                    print(f"   💼 Career pages: {len(data.get('career_pages', []))}")
                    print(f"   ⏱️ Crawl time: {data.get('crawl_time', 0):.2f}s")
                    print(f"   🔧 Method: {data.get('crawl_method', 'unknown')}")
                    
                    # Show career pages if found
                    career_pages = data.get('career_pages', [])
                    if career_pages:
                        print(f"   📋 Career pages found:")
                        for i, career_url in enumerate(career_pages[:3]):  # Show first 3
                            print(f"      {i+1}. {career_url}")
                        if len(career_pages) > 3:
                            print(f"      ... and {len(career_pages) - 3} more")
                    else:
                        print(f"   ❌ No career pages found")
                        
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

def test_stats():
    """Test the stats endpoint"""
    base_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{base_url}/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Server Stats:")
            print(f"   Cache size: {data.get('cache_size', 0)}")
            print(f"   Features: {data.get('features', {})}")
        else:
            print(f"❌ Stats HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Crawl Endpoint Tests")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    # Test stats first
    test_stats()
    
    # Test crawl endpoint
    test_crawl_endpoint()
    
    print("\n✅ Tests completed!") 