#!/usr/bin/env python3
"""
Quick test script để lấy tất cả jobs từ Sky Solution
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.job_extraction_service import JobExtractionService

async def quick_test():
    """Quick test để lấy tất cả jobs"""
    
    print("🚀 Quick Test - Sky Solution Jobs")
    print("=" * 40)
    
    service = JobExtractionService()
    
    # Test main career page
    career_url = "https://job.skysolution.com/career/"
    print(f"🔍 Testing: {career_url}")
    
    # Step 1: Get job URLs
    print("\n1️⃣ Getting job URLs...")
    job_urls = await service._extract_job_urls_from_career_page(career_url)
    
    if not job_urls:
        print(f"❌ No URLs found")
        return
    
    print(f"✅ Found {len(job_urls)} URLs")
    
    # Debug: Show all URLs
    print(f"\n🔍 All URLs found:")
    for i, url in enumerate(job_urls, 1):
        print(f"   {i}. {url}")
    
    # Step 2: Filter individual job URLs
    individual_jobs = []
    for url in job_urls:
        if any(pattern in url.lower() for pattern in [
            '-developer', '-analyst', '-tester', '-designer', '-manager',
            '-specialist', '-engineer', '-content', '-technical', '-executive'
        ]):
            individual_jobs.append(url)
    
    print(f"\n🎯 Found {len(individual_jobs)} individual job URLs")
    
    # Step 3: Extract details from each job
    print(f"\n2️⃣ Extracting job details...")
    all_jobs = []
    
    for i, job_url in enumerate(individual_jobs, 1):
        print(f"   📄 {i}/{len(individual_jobs)}: {job_url}")
        
        try:
            job_detail = await service.extract_job_details_only(job_url)
            
            if job_detail.get('success') and job_detail.get('job_name'):
                all_jobs.append({
                    'name': job_detail.get('job_name'),
                    'type': job_detail.get('job_type'),
                    'url': job_url,
                    'description_length': len(job_detail.get('job_description', ''))
                })
                print(f"      ✅ {job_detail.get('job_name')}")
            else:
                print(f"      ❌ Failed")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    # Step 4: Show results
    print(f"\n3️⃣ RESULTS:")
    print(f"   Total jobs extracted: {len(all_jobs)}")
    
    if all_jobs:
        print(f"\n📋 Jobs found:")
        for i, job in enumerate(all_jobs, 1):
            print(f"   {i}. {job['name']} ({job['type']})")
            print(f"      URL: {job['url']}")
            print(f"      Description: {job['description_length']} chars")
            print()

if __name__ == "__main__":
    asyncio.run(quick_test())
