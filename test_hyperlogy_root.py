#!/usr/bin/env python3
"""
Test script for Hyperlogy root URL to verify career page filtering
"""

import requests
import json
import time

def test_hyperlogy_root():
    """Test the career page filtering with Hyperlogy root URL"""
    
    url = "https://www.hyperlogy.com/"
    api_url = "https://crawler-ai.fly.dev/crawl_and_extract_contact_info"
    
    print("🧪 Testing Career Page Filtering with Hyperlogy Root")
    print("=" * 60)
    print(f"🔍 Testing: {url}")
    
    try:
        # Make API call
        payload = {"url": url}
        response = requests.post(api_url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            career_pages = data.get("career_pages", [])
            total_jobs = data.get("total_jobs_found", 0)
            crawl_time = data.get("crawl_time", 0)
            
            print(f"✅ Success - {len(career_pages)} career pages, {total_jobs} jobs")
            print(f"⏱️  Crawl time: {crawl_time:.2f}s")
            
            if career_pages:
                print(f"\n📋 Career pages found ({len(career_pages)} total):")
                for i, career_url in enumerate(career_pages, 1):
                    print(f"  {i:2d}. {career_url}")
                
                # Analyze the career pages
                print(f"\n🔍 ANALYSIS:")
                
                # Count by pattern
                patterns = {
                    'tuyen-dung': 0,
                    'career': 0,
                    'job': 0,
                    'recruitment': 0,
                    'hiring': 0,
                    'co-hoi': 0,
                    'other': 0
                }
                
                for career_url in career_pages:
                    url_lower = career_url.lower()
                    if 'tuyen-dung' in url_lower:
                        patterns['tuyen-dung'] += 1
                    elif 'career' in url_lower:
                        patterns['career'] += 1
                    elif 'job' in url_lower:
                        patterns['job'] += 1
                    elif 'recruitment' in url_lower:
                        patterns['recruitment'] += 1
                    elif 'hiring' in url_lower:
                        patterns['hiring'] += 1
                    elif 'co-hoi' in url_lower:
                        patterns['co-hoi'] += 1
                    else:
                        patterns['other'] += 1
                
                print(f"  Pattern breakdown:")
                for pattern, count in patterns.items():
                    if count > 0:
                        print(f"    {pattern}: {count} URLs")
                
                # Check for problematic URLs
                problematic = []
                for career_url in career_pages:
                    url_lower = career_url.lower()
                    if any(keyword in url_lower for keyword in ['news', 'article', 'product', 'service', 'solution', 'technology', 'digital', 'business', 'customer', 'experience', 'management', 'implementation', 'deployed', 'successfully']):
                        problematic.append(career_url)
                
                if problematic:
                    print(f"\n⚠️  POTENTIALLY PROBLEMATIC URLs ({len(problematic)}):")
                    for i, url in enumerate(problematic, 1):
                        print(f"  {i}. {url}")
                else:
                    print(f"\n✅ All career pages look legitimate!")
                
            else:
                print(f"❌ No career pages found")
                
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout after 60s")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_hyperlogy_root() 