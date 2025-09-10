#!/usr/bin/env python3
"""
Final comprehensive test script cho Sky Solution jobs
Sử dụng API endpoints để test
"""

import asyncio
import aiohttp
import json
import time

async def test_comprehensive_extraction():
    """Test comprehensive extraction sử dụng API"""
    
    print("🚀 Final Comprehensive Test - Sky Solution Jobs")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # Known individual job URLs
    known_job_urls = [
        "https://job.skysolution.com/middle-to-senior-business-analyst/",
        "https://job.skysolution.com/node-js-golang-backend-developer/",
        "https://job.skysolution.com/software-tester/",
        "https://job.skysolution.com/web-frontend-developer-react-js/",
        "https://job.skysolution.com/web-app-ux-ui-designer/",
        "https://job.skysolution.com/manual-tester/",
        "https://job.skysolution.com/seo-content/",
        "https://job.skysolution.com/seo-technical/"
    ]
    
    all_jobs = []
    successful = 0
    failed = 0
    
    async with aiohttp.ClientSession() as session:
        for i, job_url in enumerate(known_job_urls, 1):
            print(f"\n🔍 Test {i}/{len(known_job_urls)}: {job_url}")
            print("-" * 60)
            
            try:
                # Call extract_job_details API
                async with session.post(
                    f"{base_url}/extract_job_details",
                    json={"url": job_url},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('success') and result.get('job_name'):
                            job_info = {
                                'index': i,
                                'name': result.get('job_name', 'Unknown'),
                                'type': result.get('job_type', 'Unknown'),
                                'role': result.get('job_role', 'Unknown'),
                                'description': result.get('job_description', ''),
                                'url': job_url,
                                'crawl_time': result.get('crawl_time', 0)
                            }
                            all_jobs.append(job_info)
                            successful += 1
                            
                            print(f"✅ Success!")
                            print(f"   Name: {job_info['name']}")
                            print(f"   Type: {job_info['type']}")
                            print(f"   Role: {job_info['role']}")
                            print(f"   Description: {len(job_info['description'])} chars")
                            print(f"   Crawl time: {job_info['crawl_time']:.2f}s")
                        else:
                            failed += 1
                            print(f"❌ Failed to extract job details")
                            print(f"   Success: {result.get('success')}")
                            print(f"   Job name: {result.get('job_name', 'None')}")
                    else:
                        failed += 1
                        print(f"❌ HTTP Error: {response.status}")
                        
            except Exception as e:
                failed += 1
                print(f"❌ Error: {e}")
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   Total jobs tested: {len(known_job_urls)}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   Success rate: {(successful/len(known_job_urls)*100):.1f}%")
    
    if all_jobs:
        print(f"\n📋 All Jobs Extracted:")
        for job in all_jobs:
            print(f"   {job['index']}. {job['name']} ({job['type']})")
            print(f"      Role: {job['role']}")
            print(f"      URL: {job['url']}")
            print(f"      Description: {len(job['description'])} chars")
            print(f"      Crawl time: {job['crawl_time']:.2f}s")
            print()
        
        # Save to JSON file
        output_file = "sky_solution_jobs_final.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_jobs, f, indent=2, ensure_ascii=False)
        print(f"💾 Results saved to: {output_file}")
        
        # Show sample job description
        print(f"\n📄 Sample Job Description (Job 1):")
        print(f"   {all_jobs[0]['name']}")
        print(f"   Description preview: {all_jobs[0]['description'][:300]}...")

if __name__ == "__main__":
    asyncio.run(test_comprehensive_extraction())
