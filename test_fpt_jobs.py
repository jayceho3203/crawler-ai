#!/usr/bin/env python3
"""
Test script for FPT job extraction
"""
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fpt_jobs():
    """Test job extraction from FPT recruitment site"""
    try:
        from job_extractor import extract_jobs_from_page
        
        print("🧪 Testing FPT Job Extraction")
        print("=" * 50)
        
        # Test URLs
        test_urls = [
            "https://tuyendung.fpt.com",
            "https://tuyendung.fpt.com/",
            "https://fpt.com.vn/vi/co-hoi-nghe-nghiep"
        ]
        
        for url in test_urls:
            print(f"\n🔗 Testing: {url}")
            
            try:
                result = extract_jobs_from_page(url, max_jobs=20)
                
                if result.get("success"):
                    print(f"✅ Success!")
                    print(f"   💼 Jobs found: {result.get('total_jobs_found', 0)}")
                    
                    jobs = result.get('jobs', [])
                    if jobs:
                        print(f"   💼 Jobs:")
                        for i, job in enumerate(jobs[:10]):  # Show first 10
                            title = job.get('title', 'No title')
                            company = job.get('company', 'No company')
                            location = job.get('location', 'No location')
                            url = job.get('url', 'No URL')
                            print(f"      {i+1}. {title}")
                            print(f"         Company: {company}")
                            print(f"         Location: {location}")
                            print(f"         URL: {url}")
                            print()
                    else:
                        print(f"   ❌ No jobs found")
                        
                        # Let's also check what selectors are available
                        print(f"   🔍 Checking page structure...")
                        import requests
                        from bs4 import BeautifulSoup
                        
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8'
                        }
                        
                        response = requests.get(url, headers=headers, timeout=30)
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Look for common job-related elements
                        job_elements = soup.find_all(['div', 'li', 'article'], class_=lambda x: x and any(word in x.lower() for word in ['job', 'career', 'position', 'tuyen', 'viec', 'co-hoi']))
                        print(f"   Found {len(job_elements)} potential job elements")
                        
                        # Show first few elements
                        for i, elem in enumerate(job_elements[:3]):
                            text = elem.get_text(strip=True)[:100]
                            classes = ' '.join(elem.get('class', []))
                            print(f"      Element {i+1}: {text}... (classes: {classes})")
                else:
                    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure job_extractor.py is in the same directory")

if __name__ == "__main__":
    print("🚀 Testing FPT Job Extraction")
    print("Focusing on tuyendung.fpt.com")
    print()
    
    test_fpt_jobs()
    
    print("\n✅ Test completed!") 