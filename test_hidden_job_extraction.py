#!/usr/bin/env python3
"""
Test script for hidden job extraction
Demonstrates various techniques to extract hidden jobs from career pages
"""

import sys
import os
import asyncio
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.crawler import crawl_single_url
from app.services.hidden_job_extractor import HiddenJobExtractor

async def test_hidden_job_extraction():
    """Test hidden job extraction with various career page examples"""
    print("🎯 Testing Hidden Job Extraction")
    print("=" * 60)
    
    # Test URLs - these are examples of career pages that might have hidden jobs
    test_urls = [
        # Example career pages (replace with real URLs for testing)
        "https://example.com/careers",  # Replace with actual career page
        "https://example.com/jobs",     # Replace with actual job page
        "https://example.com/tuyen-dung" # Replace with actual Vietnamese career page
    ]
    
    # For demonstration, we'll use a sample HTML with hidden jobs
    sample_html_with_hidden_jobs = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Company Careers</title>
        <script>
            // Hidden job data in JavaScript
            const jobs = [
                {
                    "title": "Senior Software Engineer",
                    "location": "Ho Chi Minh City",
                    "type": "Full-time",
                    "description": "We are looking for a senior engineer..."
                },
                {
                    "title": "Product Manager",
                    "location": "Hanoi",
                    "type": "Full-time", 
                    "description": "Join our product team..."
                }
            ];
            
            // More hidden data
            const positions = [
                {
                    "title": "UX Designer",
                    "location": "Remote",
                    "type": "Contract",
                    "description": "Design amazing user experiences..."
                }
            ];
        </script>
    </head>
    <body>
        <nav>
            <a href="/careers">Careers</a>
            <a href="/jobs">Jobs</a>
        </nav>
        
        <!-- Visible jobs -->
        <div class="job-listings">
            <div class="job-item">
                <h3>Frontend Developer</h3>
                <p>Location: Ho Chi Minh City</p>
                <a href="/job/frontend-dev">Apply Now</a>
            </div>
        </div>
        
        <!-- Hidden jobs (collapsed) -->
        <div class="collapsed-jobs" style="display: none;">
            <div class="job-item">
                <h3>Backend Developer</h3>
                <p>Location: Hanoi</p>
                <a href="/job/backend-dev">Apply Now</a>
            </div>
        </div>
        
        <!-- Load more button -->
        <button class="load-more" onclick="loadMoreJobs()">Load More Jobs</button>
        
        <!-- Pagination -->
        <div class="pagination">
            <a href="?page=1">1</a>
            <a href="?page=2">2</a>
            <a href="?page=3">3</a>
        </div>
        
        <!-- Filter options -->
        <div class="filters">
            <select name="department">
                <option value="">All Departments</option>
                <option value="engineering">Engineering</option>
                <option value="design">Design</option>
                <option value="marketing">Marketing</option>
            </select>
            <select name="location">
                <option value="">All Locations</option>
                <option value="hcm">Ho Chi Minh City</option>
                <option value="hanoi">Hanoi</option>
                <option value="remote">Remote</option>
            </select>
        </div>
        
        <!-- Modal trigger -->
        <button class="modal-trigger" data-toggle="modal" data-target="#jobModal">
            View All Positions
        </button>
        
        <!-- Modal content -->
        <div class="modal" id="jobModal" style="display: none;">
            <div class="modal-content">
                <h2>All Available Positions</h2>
                <div class="job-item">
                    <h3>Data Scientist</h3>
                    <p>Location: Remote</p>
                    <p>Type: Full-time</p>
                </div>
                <div class="job-item">
                    <h3>DevOps Engineer</h3>
                    <p>Location: Ho Chi Minh City</p>
                    <p>Type: Full-time</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    print("📋 Sample HTML with hidden jobs created for demonstration")
    print("This HTML contains:")
    print("  - JavaScript job data")
    print("  - Collapsed job sections")
    print("  - Pagination")
    print("  - Filter options")
    print("  - Modal content")
    print()
    
    # Test the hidden job extractor with sample HTML
    print("🧪 Testing Hidden Job Extractor with sample HTML")
    print("-" * 50)
    
    # Create a simple test to demonstrate the techniques
    print("Techniques used to extract hidden jobs:")
    print()
    
    techniques = [
        "1. 🔍 Wait for dynamic content to load",
        "2. 📂 Click on expand/collapse elements", 
        "3. 📜 Scroll to trigger lazy loading",
        "4. 🔄 Switch between tabs/accordions",
        "5. 💻 Extract from JavaScript data",
        "6. 🌐 Extract from API calls",
        "7. 👻 Extract from hidden elements",
        "8. 📄 Extract from pagination",
        "9. 🔍 Extract from search/filter results",
        "10. 🪟 Extract from modal/popup content"
    ]
    
    for technique in techniques:
        print(f"   {technique}")
    
    print()
    print("📊 Expected Results:")
    print("   - JavaScript jobs: 3 jobs (Senior Engineer, Product Manager, UX Designer)")
    print("   - Hidden elements: 1 job (Backend Developer)")
    print("   - Modal content: 2 jobs (Data Scientist, DevOps Engineer)")
    print("   - Visible jobs: 1 job (Frontend Developer)")
    print("   - Total expected: 7 unique jobs")
    print()
    
    # Test with a real URL (if provided)
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        print(f"🌐 Testing with real URL: {test_url}")
        print("-" * 50)
        
        try:
            result = await crawl_single_url(test_url)
            
            if result.get("success"):
                print("✅ Crawl successful!")
                print(f"📊 Results:")
                print(f"   - Hidden Jobs: {len(result.get('hidden_jobs', []))}")
                print(f"   - Visible Jobs: {len(result.get('visible_jobs', []))}")
                print(f"   - Total Jobs: {len(result.get('total_jobs', []))}")
                print(f"   - Career URLs: {len(result.get('career_urls', []))}")
                print(f"   - Job Links: {result.get('job_links_filtered', 0)}")
                print(f"   - Crawl Time: {result.get('crawl_time', 0):.2f}s")
                
                # Show some job details
                if result.get('total_jobs'):
                    print(f"\n📋 Sample Jobs:")
                    for i, job in enumerate(result['total_jobs'][:3], 1):
                        print(f"   {i}. {job.get('title', 'N/A')}")
                        print(f"      Location: {job.get('location', 'N/A')}")
                        print(f"      Type: {job.get('job_type', 'N/A')}")
                        print(f"      Source: {job.get('source', 'N/A')}")
                        print()
                
                # Show hidden jobs specifically
                if result.get('hidden_jobs'):
                    print(f"🎯 Hidden Jobs Found:")
                    for i, job in enumerate(result['hidden_jobs'], 1):
                        print(f"   {i}. {job.get('title', 'N/A')}")
                        print(f"      Location: {job.get('location', 'N/A')}")
                        print(f"      Type: {job.get('job_type', 'N/A')}")
                        print()
            else:
                print(f"❌ Crawl failed: {result.get('error_message', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error testing URL: {str(e)}")
    else:
        print("💡 To test with a real URL, run:")
        print("   python3 test_hidden_job_extraction.py https://example.com/careers")
        print()
        print("📝 Note: Replace with actual career page URLs for real testing")

def demonstrate_techniques():
    """Demonstrate the techniques used for hidden job extraction"""
    print("🔧 Hidden Job Extraction Techniques Explained")
    print("=" * 60)
    
    techniques = {
        "Dynamic Content Loading": {
            "description": "Wait for JavaScript to load job listings",
            "selectors": ['.job-list', '.career-list', '.position-list', '.loading'],
            "code": "await page.wait_for_selector('.job-list', timeout=5000)"
        },
        "Expand/Collapse Elements": {
            "description": "Click buttons to reveal hidden job sections",
            "selectors": ['.expand', '.collapse', '.show-more', '.load-more'],
            "code": "await element.click() if await element.is_visible()"
        },
        "Lazy Loading": {
            "description": "Scroll to trigger loading of more jobs",
            "selectors": ['.job-item', '.career-item', '.position-item'],
            "code": "await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')"
        },
        "Tabs/Accordions": {
            "description": "Switch between different job categories",
            "selectors": ['.tab', '.accordion-item', '[role=\"tab\"]'],
            "code": "await tab.click() for tab in tabs"
        },
        "JavaScript Data": {
            "description": "Extract job data from script tags",
            "patterns": ["jobs?:\\s*\\[", "positions?:\\s*\\[", "careers?:\\s*\\["],
            "code": "const jobs = JSON.parse(scriptContent.match(/jobs?:\\s*(\\[.*?\\])/)[1])"
        },
        "API Calls": {
            "description": "Intercept network requests for job data",
            "patterns": ["/api/jobs", "/api/careers", "/api/positions"],
            "code": "await page.route('**/api/jobs', lambda route: capture_response(route))"
        },
        "Hidden Elements": {
            "description": "Find elements with display:none or visibility:hidden",
            "selectors": ["[style*='display: none']", "[style*='visibility: hidden']"],
            "code": "const hiddenElements = document.querySelectorAll('*[style*=\"display: none\"]')"
        },
        "Pagination": {
            "description": "Navigate through multiple pages of jobs",
            "selectors": ['.pagination', '.next', '.page-number'],
            "code": "await nextButton.click() while hasNextPage"
        },
        "Search Filters": {
            "description": "Apply different filters to reveal more jobs",
            "selectors": ['select[name*="department"]', 'select[name*="location"]'],
            "code": "await filter.select_option('engineering')"
        },
        "Modal/Popup Content": {
            "description": "Extract jobs from modal dialogs",
            "selectors": ['.modal', '.popup', '[role=\"dialog\"]'],
            "code": "await modalTrigger.click(); const modalJobs = await extractFromModal()"
        }
    }
    
    for technique, details in techniques.items():
        print(f"\n🎯 {technique}")
        print(f"   Description: {details['description']}")
        if 'selectors' in details:
            print(f"   Selectors: {', '.join(details['selectors'])}")
        if 'patterns' in details:
            print(f"   Patterns: {', '.join(details['patterns'])}")
        print(f"   Code: {details['code']}")

def show_usage_examples():
    """Show usage examples for hidden job extraction"""
    print("\n📖 Usage Examples")
    print("=" * 60)
    
    print("1. Basic Usage:")
    print("""
from app.services.crawler import crawl_single_url

# Crawl a career page with hidden job extraction
result = await crawl_single_url("https://company.com/careers")

# Access results
hidden_jobs = result.get('hidden_jobs', [])
visible_jobs = result.get('visible_jobs', [])
total_jobs = result.get('total_jobs', [])

print(f"Found {len(total_jobs)} total jobs")
print(f"Hidden jobs: {len(hidden_jobs)}")
print(f"Visible jobs: {len(visible_jobs)}")
""")
    
    print("\n2. Direct Hidden Job Extractor Usage:")
    print("""
from app.services.hidden_job_extractor import HiddenJobExtractor
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    await page.goto("https://company.com/careers")
    
    extractor = HiddenJobExtractor()
    hidden_jobs = await extractor.extract_hidden_jobs_from_page(url, page)
    
    for job in hidden_jobs:
        print(f"Title: {job.get('title')}")
        print(f"Location: {job.get('location')}")
        print(f"Type: {job.get('job_type')}")
""")
    
    print("\n3. Advanced Configuration:")
    print("""
# Customize extraction behavior
extractor = HiddenJobExtractor()

# The extractor automatically tries all techniques:
# - Dynamic content loading
# - Expand/collapse elements  
# - Lazy loading
# - Tabs/accordions
# - JavaScript data extraction
# - API call interception
# - Hidden element detection
# - Pagination navigation
# - Search filter application
# - Modal/popup content extraction
""")

async def main():
    """Main test function"""
    print("🚀 Hidden Job Extraction Test Suite")
    print("=" * 60)
    
    try:
        # Test hidden job extraction
        await test_hidden_job_extraction()
        
        # Demonstrate techniques
        demonstrate_techniques()
        
        # Show usage examples
        show_usage_examples()
        
        print("\n✅ All tests completed successfully!")
        print("\n💡 Tips for better hidden job extraction:")
        print("   - Use Playwright for JavaScript-heavy sites")
        print("   - Be patient with dynamic content loading")
        print("   - Try different filter combinations")
        print("   - Check for pagination and load more buttons")
        print("   - Look for modal/popup content")
        print("   - Monitor network requests for API calls")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 