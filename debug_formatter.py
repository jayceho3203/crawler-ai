#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.simple_job_formatter import SimpleJobFormatter

# Test data
sample_jobs = [
    {
        "title": "Middle PHP Developer (Laravel)",
        "company": "Vitex.Asia",
        "location": "Remote",
        "type": "Remote",
        "salary": "500,000",
        "posted_date": "2 days ago",
        "job_link": "https://vitex.asia/career/middle-php-developer-laravel/",
        "description": "We are looking for a Software Engineer..."
    }
]

def test_formatter():
    print("Testing SimpleJobFormatter...")
    
    try:
        formatter = SimpleJobFormatter()
        print("✅ Formatter created successfully")
        
        result = formatter.format_jobs_list(sample_jobs)
        print("✅ format_jobs_list called successfully")
        print(f"Result: {result}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_formatter() 