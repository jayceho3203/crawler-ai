#!/usr/bin/env python3
"""
Test script to verify the new strict career page filtering logic with real websites
"""

import requests
import json
import time

def test_real_crawl():
    """Test the new strict career page filtering with real websites"""
    
    # Test URLs - real company websites
    test_urls = [
        "https://fpt.com.vn",
        "https://vng.com.vn", 
        "https://tma.com.vn",
        "https://cmc.com.vn",
        "https://hyperlogy.com",
        "https://nobisoft.com.vn"
    ]
    
    api_url = "https://crawler-ai.fly.dev/crawl_and_extract_contact_info"
    
    print("🧪 Testing STRICT Career Page Filtering with Real Websites")
    print("=" * 70)
    
    results = []
    
    for url in test_urls:
        print(f"\n🔍 Testing: {url}")
        
        try:
            # Make API call
            payload = {"url": url}
            response = requests.post(api_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                career_pages = data.get("career_pages", [])
                total_jobs = data.get("total_jobs_found", 0)
                crawl_time = data.get("crawl_time", 0)
                
                print(f"  ✅ Success - {len(career_pages)} career pages, {total_jobs} jobs")
                print(f"  ⏱️  Crawl time: {crawl_time:.2f}s")
                
                if career_pages:
                    print(f"  📋 Career pages found:")
                    for i, career_url in enumerate(career_pages[:5], 1):  # Show first 5
                        print(f"    {i}. {career_url}")
                    if len(career_pages) > 5:
                        print(f"    ... and {len(career_pages) - 5} more")
                else:
                    print(f"  ❌ No career pages found")
                
                results.append({
                    "url": url,
                    "success": True,
                    "career_pages": len(career_pages),
                    "jobs": total_jobs,
                    "crawl_time": crawl_time
                })
                
            else:
                print(f"  ❌ HTTP {response.status_code}: {response.text}")
                results.append({
                    "url": url,
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                })
                
        except requests.exceptions.Timeout:
            print(f"  ⏰ Timeout after 60s")
            results.append({
                "url": url,
                "success": False,
                "error": "Timeout"
            })
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results.append({
                "url": url,
                "success": False,
                "error": str(e)
            })
        
        # Wait between requests to avoid overwhelming the server
        time.sleep(2)
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print("=" * 70)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"  Total tested: {len(results)}")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    
    if successful:
        total_career_pages = sum(r["career_pages"] for r in successful)
        total_jobs = sum(r["jobs"] or 0 for r in successful)
        avg_crawl_time = sum(r["crawl_time"] for r in successful) / len(successful)
        
        print(f"\n  📈 Performance:")
        print(f"    Total career pages found: {total_career_pages}")
        print(f"    Total jobs found: {total_jobs}")
        print(f"    Average crawl time: {avg_crawl_time:.2f}s")
        print(f"    Average career pages per site: {total_career_pages/len(successful):.1f}")
        
        print(f"\n  🏆 Best performers:")
        # Sort by career pages found
        sorted_results = sorted(successful, key=lambda x: x["career_pages"], reverse=True)
        for i, result in enumerate(sorted_results[:3], 1):
            print(f"    {i}. {result['url']} - {result['career_pages']} career pages, {result['jobs']} jobs")
    
    if failed:
        print(f"\n  ❌ Failed URLs:")
        for result in failed:
            print(f"    - {result['url']}: {result['error']}")

if __name__ == "__main__":
    test_real_crawl() 