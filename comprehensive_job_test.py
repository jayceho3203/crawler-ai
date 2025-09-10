#!/usr/bin/env python3
"""
Comprehensive job extraction test script
Test tất cả các loại pages: main career, category pages, và individual jobs
"""

import asyncio
import aiohttp
import json
import time

async def test_all_pages():
    """Test comprehensive extraction từ tất cả các loại pages"""
    
    print("🚀 Comprehensive Job Extraction Test - Sky Solution")
    print("=" * 70)
    
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # Test URLs
    test_cases = [
        {
            "name": "Main Career Page",
            "url": "https://job.skysolution.com/career/",
            "type": "main_career"
        },
        {
            "name": "IT Category Page", 
            "url": "https://job.skysolution.com/career/information-technology/",
            "type": "category"
        },
        {
            "name": "Business Development Category",
            "url": "https://job.skysolution.com/career/business-development/",
            "type": "category"
        },
        {
            "name": "Marketing Category",
            "url": "https://job.skysolution.com/career/marketing/",
            "type": "category"
        }
    ]
    
    # Known individual job URLs
    individual_jobs = [
        "https://job.skysolution.com/middle-to-senior-business-analyst/",
        "https://job.skysolution.com/node-js-golang-backend-developer/",
        "https://job.skysolution.com/software-tester/",
        "https://job.skysolution.com/web-frontend-developer-react-js/",
        "https://job.skysolution.com/web-app-ux-ui-designer/",
        "https://job.skysolution.com/manual-tester/",
        "https://job.skysolution.com/seo-content/",
        "https://job.skysolution.com/seo-technical/"
    ]
    
    all_results = []
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Career pages (URLs extraction)
        print("\n🔍 TEST 1: Career Pages (URL Extraction)")
        print("=" * 50)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['name']}: {test_case['url']}")
            print("-" * 40)
            
            try:
                async with session.post(
                    f"{base_url}/extract_job_urls",
                    json={"url": test_case['url'], "max_jobs": 50},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('success'):
                            job_urls = result.get('job_urls', [])
                            direct_jobs = result.get('direct_jobs', [])
                            
                            print(f"✅ Success!")
                            print(f"   Job URLs found: {len(job_urls)}")
                            print(f"   Direct jobs: {len(direct_jobs)}")
                            print(f"   Has individual URLs: {result.get('has_individual_urls', False)}")
                            
                            # Show first few URLs
                            if job_urls:
                                print(f"   Sample URLs:")
                                for j, url in enumerate(job_urls[:3], 1):
                                    print(f"      {j}. {url}")
                                if len(job_urls) > 3:
                                    print(f"      ... and {len(job_urls) - 3} more")
                            
                            all_results.append({
                                "test_case": test_case,
                                "result": result,
                                "success": True
                            })
                        else:
                            print(f"❌ Failed: {result.get('error_message', 'Unknown error')}")
                            all_results.append({
                                "test_case": test_case,
                                "result": result,
                                "success": False
                            })
                    else:
                        print(f"❌ HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Test 2: Individual job details extraction
        print(f"\n🔍 TEST 2: Individual Job Details Extraction")
        print("=" * 50)
        
        job_details = []
        successful_jobs = 0
        failed_jobs = 0
        
        for i, job_url in enumerate(individual_jobs, 1):
            print(f"\n{i}/{len(individual_jobs)}: {job_url}")
            print("-" * 40)
            
            try:
                async with session.post(
                    f"{base_url}/extract_job_details",
                    json={"url": job_url},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('success') and result.get('job_name'):
                            job_info = {
                                'name': result.get('job_name', 'Unknown'),
                                'type': result.get('job_type', 'Unknown'),
                                'role': result.get('job_role', 'Unknown'),
                                'description': result.get('job_description', ''),
                                'url': job_url,
                                'crawl_time': result.get('crawl_time', 0)
                            }
                            job_details.append(job_info)
                            successful_jobs += 1
                            
                            print(f"✅ Success!")
                            print(f"   Name: {job_info['name']}")
                            print(f"   Type: {job_info['type']}")
                            print(f"   Description: {len(job_info['description'])} chars")
                        else:
                            failed_jobs += 1
                            print(f"❌ Failed to extract job details")
                    else:
                        failed_jobs += 1
                        print(f"❌ HTTP Error: {response.status}")
                        
            except Exception as e:
                failed_jobs += 1
                print(f"❌ Error: {e}")
    
    # Final Summary
    print(f"\n📊 FINAL SUMMARY")
    print("=" * 50)
    
    # Career pages summary
    career_success = len([r for r in all_results if r['success']])
    print(f"Career Pages Tested: {len(test_cases)}")
    print(f"Career Pages Success: {career_success}")
    print(f"Career Pages Success Rate: {(career_success/len(test_cases)*100):.1f}%")
    
    # Individual jobs summary
    print(f"\nIndividual Jobs Tested: {len(individual_jobs)}")
    print(f"Individual Jobs Success: {successful_jobs}")
    print(f"Individual Jobs Success Rate: {(successful_jobs/len(individual_jobs)*100):.1f}%")
    
    # Save detailed results
    detailed_results = {
        "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "career_pages_results": all_results,
        "individual_jobs": job_details,
        "summary": {
            "career_pages_tested": len(test_cases),
            "career_pages_success": career_success,
            "individual_jobs_tested": len(individual_jobs),
            "individual_jobs_success": successful_jobs
        }
    }
    
    output_file = "comprehensive_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Show sample job details
    if job_details:
        print(f"\n📋 Sample Job Details:")
        for i, job in enumerate(job_details[:3], 1):
            print(f"   {i}. {job['name']} ({job['type']})")
            print(f"      Description: {job['description'][:100]}...")
            print()

if __name__ == "__main__":
    asyncio.run(test_all_pages())
