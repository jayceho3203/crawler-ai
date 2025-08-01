#!/usr/bin/env python3
"""
Test script for advanced job finding endpoint
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_advanced_job_finding():
    """Test advanced job finding endpoint"""
    print("🔍 Testing Advanced Job Finding Endpoint")
    print("=" * 60)
    
    career_url = "https://intx.vn/career"
    
    payload = {
        "career_url": career_url,
        "max_jobs": 50,
        "search_strategy": "comprehensive",
        "include_detailed_analysis": True,
        "quality_threshold": 0.3
    }
    
    try:
        response = requests.post(f"{BASE_URL}/find_jobs_advanced", json=payload)
        result = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"🎯 Total jobs found: {result.get('total_jobs_found', 0)}")
        print(f"⭐ High quality jobs: {result.get('high_quality_jobs', 0)}")
        print(f"📊 Average quality score: {result.get('average_quality_score', 0):.2f}")
        print(f"⏱️ Crawl time: {result.get('crawl_time', 0):.2f}s")
        
        if result.get('jobs'):
            print(f"\n💼 Top 5 jobs by quality:")
            for i, job in enumerate(result['jobs'][:5]):
                print(f"  {i+1}. {job.get('title', 'Unknown')}")
                print(f"     Company: {job.get('company', 'Unknown')}")
                print(f"     Location: {job.get('location', 'Unknown')}")
                print(f"     Quality Score: {job.get('quality_score', 0):.2f}")
                print(f"     URL: {job.get('url', 'N/A')}")
                print()
        
        if result.get('statistics'):
            stats = result['statistics']
            print(f"📈 Statistics:")
            print(f"  Job types: {stats.get('job_types', {})}")
            print(f"  Locations: {stats.get('locations', {})}")
            print(f"  Quality distribution: {stats.get('quality_distribution', {})}")
        
        if result.get('search_methods_used'):
            print(f"🔍 Search methods used: {result['search_methods_used']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_comparison_with_original():
    """Compare advanced job finding with original endpoint"""
    print("\n🔄 Comparing Advanced vs Original Job Finding")
    print("=" * 60)
    
    career_url = "https://intx.vn/career"
    
    # Test original endpoint
    print("📋 Testing original endpoint...")
    original_payload = {"url": career_url}
    try:
        original_response = requests.post(f"{BASE_URL}/crawl_and_extract_contact_info", json=original_payload)
        original_result = original_response.json()
        original_jobs = len(original_result.get('jobs', []))
        original_time = original_result.get('crawl_time', 0)
        print(f"   Original: {original_jobs} jobs in {original_time:.2f}s")
    except Exception as e:
        print(f"   ❌ Original endpoint error: {e}")
        original_jobs = 0
        original_time = 0
    
    # Test advanced endpoint
    print("📋 Testing advanced endpoint...")
    advanced_payload = {
        "career_url": career_url,
        "max_jobs": 100,
        "quality_threshold": 0.0
    }
    try:
        advanced_response = requests.post(f"{BASE_URL}/find_jobs_advanced", json=advanced_payload)
        advanced_result = advanced_response.json()
        advanced_jobs = advanced_result.get('total_jobs_found', 0)
        advanced_time = advanced_result.get('crawl_time', 0)
        print(f"   Advanced: {advanced_jobs} jobs in {advanced_time:.2f}s")
    except Exception as e:
        print(f"   ❌ Advanced endpoint error: {e}")
        advanced_jobs = 0
        advanced_time = 0
    
    # Comparison
    print(f"\n📊 Comparison:")
    print(f"  Jobs found: {original_jobs} → {advanced_jobs} ({advanced_jobs - original_jobs:+d})")
    print(f"  Time taken: {original_time:.2f}s → {advanced_time:.2f}s ({advanced_time - original_time:+.2f}s)")
    
    if advanced_jobs > original_jobs:
        print(f"  ✅ Advanced endpoint found {advanced_jobs - original_jobs} more jobs!")
    elif advanced_jobs < original_jobs:
        print(f"  ⚠️ Advanced endpoint found {original_jobs - advanced_jobs} fewer jobs")
    else:
        print(f"  ➡️ Both endpoints found the same number of jobs")

def test_different_strategies():
    """Test different search strategies"""
    print("\n🎯 Testing Different Search Strategies")
    print("=" * 60)
    
    career_url = "https://intx.vn/career"
    
    strategies = [
        {"name": "Comprehensive", "strategy": "comprehensive"},
        {"name": "Pattern-based", "strategy": "pattern_based"},
        {"name": "Deep crawl", "strategy": "deep_crawl"}
    ]
    
    for strategy in strategies:
        print(f"📋 Testing {strategy['name']} strategy...")
        payload = {
            "career_url": career_url,
            "max_jobs": 30,
            "search_strategy": strategy['strategy'],
            "quality_threshold": 0.0
        }
        
        try:
            response = requests.post(f"{BASE_URL}/find_jobs_advanced", json=payload)
            result = response.json()
            
            jobs_found = result.get('total_jobs_found', 0)
            crawl_time = result.get('crawl_time', 0)
            avg_quality = result.get('average_quality_score', 0)
            
            print(f"   Jobs: {jobs_found}, Time: {crawl_time:.2f}s, Avg Quality: {avg_quality:.2f}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Advanced Job Finding")
    print("=" * 80)
    
    # Test basic functionality
    test_advanced_job_finding()
    
    # Test comparison
    test_comparison_with_original()
    
    # Test different strategies
    test_different_strategies()
    
    print("\n✅ All tests completed!") 