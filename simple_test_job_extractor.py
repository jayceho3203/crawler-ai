#!/usr/bin/env python3
"""
Simple test script for job extractor without server
"""
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_job_extractor():
    """Test the job extractor directly"""
    try:
        from job_extractor import extract_jobs_from_page
        
        print("🧪 Testing Job Extractor Directly")
        print("=" * 50)
        
        # Test URLs
        test_urls = [
            "https://career.vng.com.vn/co-hoi-nghe-nghiep",
            "https://fpt.com.vn/vi/co-hoi-nghe-nghiep"
        ]
        
        for url in test_urls:
            print(f"\n🔗 Testing: {url}")
            
            try:
                result = extract_jobs_from_page(url, max_jobs=5)
                
                if result.get("success"):
                    print(f"✅ Success!")
                    print(f"   💼 Jobs found: {result.get('total_jobs_found', 0)}")
                    
                    jobs = result.get('jobs', [])
                    if jobs:
                        print(f"   💼 Jobs:")
                        for i, job in enumerate(jobs[:3]):  # Show first 3
                            title = job.get('title', 'No title')
                            company = job.get('company', 'No company')
                            location = job.get('location', 'No location')
                            print(f"      {i+1}. {title}")
                            print(f"         Company: {company}")
                            print(f"         Location: {location}")
                            if job.get('url'):
                                print(f"         URL: {job['url']}")
                            print()
                    else:
                        print(f"   ❌ No jobs found")
                else:
                    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure job_extractor.py is in the same directory")

if __name__ == "__main__":
    print("🚀 Testing Job Extractor")
    print()
    
    test_job_extractor()
    
    print("\n✅ Test completed!") 