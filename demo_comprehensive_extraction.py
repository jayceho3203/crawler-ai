#!/usr/bin/env python3
"""
Demo script cho comprehensive job extraction
Tự động tìm và extract tất cả jobs từ Sky Solution
"""

import asyncio
import aiohttp
import json
import time

async def comprehensive_job_extraction_demo():
    """
    Demo comprehensive job extraction
    Tự động tìm individual job URLs và extract details
    """
    
    print("🚀 Comprehensive Job Extraction Demo - Sky Solution")
    print("=" * 70)
    
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # Step 1: Tìm individual job URLs từ main career page
    print("\n🔍 STEP 1: Finding Individual Job URLs")
    print("=" * 50)
    
    career_page_url = "https://job.skysolution.com/career/"
    print(f"Scanning: {career_page_url}")
    
    individual_job_urls = []
    
    async with aiohttp.ClientSession() as session:
        try:
            # Get job URLs from career page
            async with session.post(
                f"{base_url}/extract_job_urls",
                json={"url": career_page_url, "max_jobs": 50},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get('success'):
                        all_urls = result.get('job_urls', [])
                        print(f"✅ Found {len(all_urls)} total URLs")
                        
                        # Filter for individual job URLs
                        for url in all_urls:
                            if any(pattern in url.lower() for pattern in [
                                '-developer', '-analyst', '-tester', '-designer', '-manager',
                                '-specialist', '-engineer', '-content', '-technical', '-executive',
                                '-coordinator', '-assistant', '-frontend', '-backend', '-fullstack',
                                '-devops', '-qa', '-seo', '-marketing', '-sales', '-hr', '-admin',
                                '-lead', '-senior', '-junior', '-intern'
                            ]):
                                individual_job_urls.append(url)
                        
                        print(f"🎯 Filtered to {len(individual_job_urls)} individual job URLs")
                        
                        if individual_job_urls:
                            print(f"\n📋 Individual Job URLs found:")
                            for i, url in enumerate(individual_job_urls, 1):
                                print(f"   {i}. {url}")
                        else:
                            print("⚠️ No individual job URLs found in main career page")
                            print("   This suggests jobs might be in category pages or embedded")
                            
                            # Try category pages
                            print(f"\n🔍 Trying category pages...")
                            category_urls = [
                                "https://job.skysolution.com/career/information-technology/",
                                "https://job.skysolution.com/career/business-development/",
                                "https://job.skysolution.com/career/marketing/"
                            ]
                            
                            for cat_url in category_urls:
                                print(f"   Checking: {cat_url}")
                                async with session.post(
                                    f"{base_url}/extract_job_urls",
                                    json={"url": cat_url, "max_jobs": 50},
                                    timeout=aiohttp.ClientTimeout(total=30)
                                ) as cat_response:
                                    
                                    if cat_response.status == 200:
                                        cat_result = await cat_response.json()
                                        if cat_result.get('success'):
                                            direct_jobs = cat_result.get('direct_jobs', [])
                                            if direct_jobs:
                                                print(f"      ✅ Found {len(direct_jobs)} embedded jobs")
                                                # Add embedded jobs to our list
                                                for job in direct_jobs:
                                                    if job.get('job_link'):
                                                        individual_job_urls.append(job['job_link'])
                                            else:
                                                print(f"      ⚠️ No embedded jobs found")
                    else:
                        print(f"❌ Failed to extract URLs: {result.get('error_message')}")
                else:
                    print(f"❌ HTTP Error: {response.status}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Step 2: Extract details from individual job URLs
    print(f"\n🔍 STEP 2: Extracting Job Details")
    print("=" * 50)
    
    if not individual_job_urls:
        print("❌ No individual job URLs found. Using known URLs for demo...")
        # Fallback to known URLs
        individual_job_urls = [
            "https://job.skysolution.com/middle-to-senior-business-analyst/",
            "https://job.skysolution.com/node-js-golang-backend-developer/",
            "https://job.skysolution.com/software-tester/",
            "https://job.skysolution.com/web-app-ux-ui-designer/",
            "https://job.skysolution.com/manual-tester/",
            "https://job.skysolution.com/seo-content/",
            "https://job.skysolution.com/seo-technical/"
        ]
        print(f"Using {len(individual_job_urls)} known job URLs")
    
    all_jobs = []
    successful = 0
    failed = 0
    
    async with aiohttp.ClientSession() as session:
        for i, job_url in enumerate(individual_job_urls, 1):
            print(f"\n📄 Processing {i}/{len(individual_job_urls)}: {job_url}")
            print("-" * 60)
            
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
                            print(f"   Description: {len(job_info['description'])} chars")
                        else:
                            failed += 1
                            print(f"❌ Failed to extract job details")
                    else:
                        failed += 1
                        print(f"❌ HTTP Error: {response.status}")
                        
            except Exception as e:
                failed += 1
                print(f"❌ Error: {e}")
    
    # Step 3: Final Results
    print(f"\n🎉 COMPREHENSIVE EXTRACTION COMPLETED!")
    print("=" * 70)
    
    print(f"📊 SUMMARY:")
    print(f"   Individual job URLs found: {len(individual_job_urls)}")
    print(f"   Jobs successfully extracted: {successful}")
    print(f"   Jobs failed to extract: {failed}")
    print(f"   Success rate: {(successful/len(individual_job_urls)*100):.1f}%")
    
    if all_jobs:
        print(f"\n📋 ALL JOBS EXTRACTED:")
        for job in all_jobs:
            print(f"   {job['index']}. {job['name']} ({job['type']})")
            print(f"      Role: {job['role']}")
            print(f"      URL: {job['url']}")
            print(f"      Description: {len(job['description'])} chars")
            print()
        
        # Save results
        output_file = "comprehensive_extraction_demo.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "career_page_url": career_page_url,
                "individual_job_urls": individual_job_urls,
                "extracted_jobs": all_jobs,
                "summary": {
                    "total_urls_found": len(individual_job_urls),
                    "successful_extractions": successful,
                    "failed_extractions": failed,
                    "success_rate": f"{(successful/len(individual_job_urls)*100):.1f}%"
                }
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {output_file}")
        
        # Show sample job description
        print(f"\n📄 Sample Job Description:")
        print(f"   Job: {all_jobs[0]['name']}")
        print(f"   Description preview: {all_jobs[0]['description'][:200]}...")

if __name__ == "__main__":
    asyncio.run(comprehensive_job_extraction_demo())
