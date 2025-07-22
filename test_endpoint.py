#!/usr/bin/env python3
"""
Test script for updated crawl_and_extract_contact_info endpoint
"""
import requests
import json
import time

def test_endpoint():
    """Test the updated crawl_and_extract_contact_info endpoint"""
    base_url = "http://localhost:8000"
    
    # Test URLs
    test_urls = [
        "https://fpt.com.vn",
        "https://vng.com.vn"
    ]
    
    print("🧪 Testing Updated crawl_and_extract_contact_info Endpoint")
    print("=" * 60)
    
    for url in test_urls:
        print(f"\n🔗 Testing: {url}")
        
        try:
            response = requests.post(
                f"{base_url}/crawl_and_extract_contact_info",
                json={"url": url},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    print(f"✅ Success!")
                    print(f"   📧 Emails: {len(data.get('emails', []))}")
                    print(f"   🔗 Social links: {len(data.get('social_links', []))}")
                    print(f"   💼 Career pages: {len(data.get('career_pages', []))}")
                    print(f"   💼 Jobs found: {data.get('total_jobs_found', 0)}")
                    print(f"   ⏱️ Crawl time: {data.get('crawl_time', 0):.2f}s")
                    
                    # Show jobs if found
                    jobs = data.get('jobs', [])
                    if jobs:
                        print(f"   💼 Jobs:")
                        for i, job in enumerate(jobs[:3]):  # Show first 3
                            title = job.get('title', 'No title')
                            company = job.get('company', 'No company')
                            print(f"      {i+1}. {title} - {company}")
                        if len(jobs) > 3:
                            print(f"      ... and {len(jobs) - 3} more")
                    else:
                        print(f"   ❌ No jobs found")
                        
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
        
        time.sleep(2)

if __name__ == "__main__":
    print("🚀 Testing Updated Endpoint")
    print("This endpoint now extracts jobs from career pages!")
    print()
    
    test_endpoint()
    
    print("\n✅ Test completed!")
    print("\n📋 Summary:")
    print("   - Endpoint now extracts jobs automatically")
    print("   - Jobs available in 'jobs' field")
    print("   - Compatible with existing N8N workflow") 