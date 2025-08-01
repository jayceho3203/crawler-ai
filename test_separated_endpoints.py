#!/usr/bin/env python3
"""
Test script for separated endpoints
"""

import asyncio
import json
import requests
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_contact_extraction():
    """Test contact extraction endpoint"""
    print("🔍 Testing Contact Extraction Endpoint")
    print("=" * 50)
    
    url = "https://intx.vn"
    
    payload = {
        "url": url,
        "include_social": True,
        "include_emails": True,
        "include_phones": True,
        "max_depth": 2,
        "timeout": 30
    }
    
    try:
        response = requests.post(f"{BASE_URL}/extract_contact_info", json=payload)
        result = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"📧 Emails found: {len(result.get('emails', []))}")
        print(f"📱 Phones found: {len(result.get('phones', []))}")
        print(f"🔗 Social links found: {len(result.get('social_links', []))}")
        print(f"📝 Contact forms found: {len(result.get('contact_forms', []))}")
        print(f"⏱️ Crawl time: {result.get('crawl_time', 0):.2f}s")
        
        if result.get('emails'):
            print(f"📧 Sample emails: {result['emails'][:3]}")
        if result.get('social_links'):
            print(f"🔗 Sample social links: {result['social_links'][:3]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_career_page_detection():
    """Test career page detection endpoint"""
    print("\n🔍 Testing Career Page Detection Endpoint")
    print("=" * 50)
    
    url = "https://intx.vn"
    
    payload = {
        "url": url,
        "include_subdomain_search": True,
        "max_pages_to_scan": 50,
        "strict_filtering": True,
        "include_job_boards": False
    }
    
    try:
        response = requests.post(f"{BASE_URL}/detect_career_pages", json=payload)
        result = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"🎯 Career pages found: {len(result.get('career_pages', []))}")
        print(f"⚠️ Potential career pages: {len(result.get('potential_career_pages', []))}")
        print(f"❌ Rejected URLs: {len(result.get('rejected_urls', []))}")
        print(f"📊 Confidence score: {result.get('confidence_score', 0):.2f}")
        print(f"⏱️ Crawl time: {result.get('crawl_time', 0):.2f}s")
        
        if result.get('career_pages'):
            print(f"🎯 Career pages: {result['career_pages']}")
        if result.get('rejected_urls'):
            print(f"❌ Sample rejected URLs: {result['rejected_urls'][:3]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_job_extraction():
    """Test job extraction endpoint"""
    print("\n🔍 Testing Job Extraction Endpoint")
    print("=" * 50)
    
    career_pages = ["https://intx.vn/career"]
    
    payload = {
        "career_page_urls": career_pages,
        "max_jobs_per_page": 20,
        "include_hidden_jobs": True,
        "include_job_details": True,
        "job_types_filter": ["full-time", "part-time"],
        "location_filter": ["hanoi", "ho_chi_minh"],
        "salary_range": {"min": 10000000, "max": 50000000},
        "posted_date_filter": "last_month"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/extract_jobs", json=payload)
        result = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"💼 Total jobs found: {result.get('total_jobs_found', 0)}")
        print(f"👁️ Visible jobs: {result.get('visible_jobs_count', 0)}")
        print(f"🔍 Hidden jobs: {result.get('hidden_jobs_count', 0)}")
        print(f"⏱️ Crawl time: {result.get('crawl_time', 0):.2f}s")
        
        if result.get('jobs'):
            print(f"💼 Sample jobs:")
            for i, job in enumerate(result['jobs'][:3]):
                print(f"  {i+1}. {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                print(f"     Location: {job.get('location', 'Unknown')}")
                print(f"     Type: {job.get('job_type', 'Unknown')}")
                print(f"     Salary: {job.get('salary', 'Unknown')}")
                print()
        
        if result.get('job_summary'):
            summary = result['job_summary']
            print(f"📊 Job Summary:")
            print(f"  Total: {summary.get('total_jobs', 0)}")
            print(f"  Job types: {summary.get('job_types', {})}")
            print(f"  Locations: {summary.get('locations', {})}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_workflow():
    """Test complete workflow using separated endpoints"""
    print("\n🔄 Testing Complete Workflow")
    print("=" * 50)
    
    url = "https://intx.vn"
    
    # Step 1: Extract contact info
    print("Step 1: Extracting contact info...")
    contact_payload = {"url": url}
    contact_response = requests.post(f"{BASE_URL}/extract_contact_info", json=contact_payload)
    contact_result = contact_response.json()
    
    if not contact_result.get('success'):
        print(f"❌ Contact extraction failed: {contact_result.get('error_message')}")
        return
    
    print(f"✅ Contact extraction completed in {contact_result.get('crawl_time', 0):.2f}s")
    
    # Step 2: Detect career pages
    print("Step 2: Detecting career pages...")
    career_payload = {"url": url}
    career_response = requests.post(f"{BASE_URL}/detect_career_pages", json=career_payload)
    career_result = career_response.json()
    
    if not career_result.get('success'):
        print(f"❌ Career page detection failed: {career_result.get('error_message')}")
        return
    
    career_pages = career_result.get('career_pages', [])
    print(f"✅ Found {len(career_pages)} career pages in {career_result.get('crawl_time', 0):.2f}s")
    
    # Step 3: Extract jobs (if career pages found)
    if career_pages:
        print("Step 3: Extracting jobs...")
        job_payload = {
            "career_page_urls": career_pages[:3],  # Limit to first 3
            "max_jobs_per_page": 20
        }
        job_response = requests.post(f"{BASE_URL}/extract_jobs", json=job_payload)
        job_result = job_response.json()
        
        if job_result.get('success'):
            print(f"✅ Extracted {job_result.get('total_jobs_found', 0)} jobs in {job_result.get('crawl_time', 0):.2f}s")
        else:
            print(f"❌ Job extraction failed: {job_result.get('error_message')}")
    else:
        print("⚠️ No career pages found, skipping job extraction")
    
    # Summary
    total_time = (contact_result.get('crawl_time', 0) + 
                 career_result.get('crawl_time', 0) + 
                 job_result.get('crawl_time', 0) if career_pages else 0)
    
    print(f"\n📊 Workflow Summary:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Emails found: {len(contact_result.get('emails', []))}")
    print(f"  Social links: {len(contact_result.get('social_links', []))}")
    print(f"  Career pages: {len(career_pages)}")
    print(f"  Jobs found: {job_result.get('total_jobs_found', 0) if career_pages else 0}")

if __name__ == "__main__":
    print("🚀 Testing Separated Endpoints")
    print("=" * 60)
    
    # Test individual endpoints
    test_contact_extraction()
    test_career_page_detection()
    test_job_extraction()
    
    # Test complete workflow
    test_workflow()
    
    print("\n✅ All tests completed!") 