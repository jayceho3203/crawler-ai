#!/usr/bin/env python3
"""
Simple test script for hidden job extraction demonstration
No Playwright required - shows the techniques and concepts
"""

import sys
import os
import json
import re
from bs4 import BeautifulSoup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demonstrate_hidden_job_techniques():
    """Demonstrate the 10 techniques for hidden job extraction"""
    print("🎯 Hidden Job Extraction Techniques Demonstration")
    print("=" * 60)
    
    # Sample HTML with various types of hidden jobs
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Company Careers</title>
        <script>
            // Technique 5: JavaScript Data
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
        
        <!-- Technique 1: Visible jobs -->
        <div class="job-listings">
            <div class="job-item">
                <h3>Frontend Developer</h3>
                <p>Location: Ho Chi Minh City</p>
                <a href="/job/frontend-dev">Apply Now</a>
            </div>
        </div>
        
        <!-- Technique 2: Hidden jobs (collapsed) -->
        <div class="collapsed-jobs" style="display: none;">
            <div class="job-item">
                <h3>Backend Developer</h3>
                <p>Location: Hanoi</p>
                <a href="/job/backend-dev">Apply Now</a>
            </div>
        </div>
        
        <!-- Technique 3: Load more button -->
        <button class="load-more" onclick="loadMoreJobs()">Load More Jobs</button>
        
        <!-- Technique 4: Pagination -->
        <div class="pagination">
            <a href="?page=1">1</a>
            <a href="?page=2">2</a>
            <a href="?page=3">3</a>
        </div>
        
        <!-- Technique 5: Filter options -->
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
        
        <!-- Technique 6: Modal trigger -->
        <button class="modal-trigger" data-toggle="modal" data-target="#jobModal">
            View All Positions
        </button>
        
        <!-- Technique 7: Modal content -->
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
        
        <!-- Technique 8: Hidden elements with visibility: hidden -->
        <div style="visibility: hidden;">
            <div class="job-item">
                <h3>Hidden Job 1</h3>
                <p>Location: Unknown</p>
            </div>
        </div>
        
        <!-- Technique 9: Hidden elements with opacity: 0 -->
        <div style="opacity: 0;">
            <div class="job-item">
                <h3>Hidden Job 2</h3>
                <p>Location: Unknown</p>
            </div>
        </div>
        
        <!-- Technique 10: Tabs/Accordions -->
        <div class="tabs">
            <div class="tab" data-tab="engineering">Engineering</div>
            <div class="tab" data-tab="design">Design</div>
        </div>
        <div class="tab-content" id="engineering">
            <div class="job-item">
                <h3>Software Engineer</h3>
                <p>Location: Ho Chi Minh City</p>
            </div>
        </div>
        <div class="tab-content" id="design" style="display: none;">
            <div class="job-item">
                <h3>UI/UX Designer</h3>
                <p>Location: Hanoi</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    print("📋 Sample HTML with hidden jobs created")
    print("This HTML contains examples of all 10 hidden job types:")
    print()
    
    techniques = [
        "1. 🔍 Visible jobs (Frontend Developer)",
        "2. 📂 Collapsed jobs (Backend Developer)",
        "3. 📜 Load more button",
        "4. 📄 Pagination",
        "5. 🔍 Filter options",
        "6. 🪟 Modal trigger",
        "7. 🪟 Modal content (Data Scientist, DevOps Engineer)",
        "8. 👻 Hidden elements - visibility: hidden (Hidden Job 1)",
        "9. 👻 Hidden elements - opacity: 0 (Hidden Job 2)",
        "10. 🔄 Tabs/Accordions (Software Engineer, UI/UX Designer)"
    ]
    
    for technique in techniques:
        print(f"   {technique}")
    
    print()
    print("🧪 Simulating extraction techniques...")
    print("-" * 50)
    
    # Simulate extraction techniques
    soup = BeautifulSoup(sample_html, 'html.parser')
    
    # Technique 1: Extract visible jobs
    visible_jobs = extract_visible_jobs(soup)
    print(f"📊 Visible jobs found: {len(visible_jobs)}")
    for job in visible_jobs:
        print(f"   - {job['title']} ({job['location']})")
    
    # Technique 2: Extract from JavaScript data
    js_jobs = extract_from_javascript_data(sample_html)
    print(f"\n💻 JavaScript jobs found: {len(js_jobs)}")
    for job in js_jobs:
        print(f"   - {job['title']} ({job['location']})")
    
    # Technique 3: Extract from hidden elements
    hidden_jobs = extract_from_hidden_elements(soup)
    print(f"\n👻 Hidden elements jobs found: {len(hidden_jobs)}")
    for job in hidden_jobs:
        print(f"   - {job['title']} ({job['location']})")
    
    # Technique 4: Extract from modal content
    modal_jobs = extract_from_modal_content(soup)
    print(f"\n🪟 Modal jobs found: {len(modal_jobs)}")
    for job in modal_jobs:
        print(f"   - {job['title']} ({job['location']})")
    
    # Technique 5: Extract from tabs/accordions
    tab_jobs = extract_from_tabs_accordions(soup)
    print(f"\n🔄 Tab/Accordion jobs found: {len(tab_jobs)}")
    for job in tab_jobs:
        print(f"   - {job['title']} ({job['location']})")
    
    # Combine all jobs
    all_jobs = visible_jobs + js_jobs + hidden_jobs + modal_jobs + tab_jobs
    
    # Remove duplicates
    unique_jobs = []
    seen_titles = set()
    for job in all_jobs:
        if job['title'] not in seen_titles:
            unique_jobs.append(job)
            seen_titles.add(job['title'])
    
    print(f"\n📋 Total unique jobs found: {len(unique_jobs)}")
    print("=" * 50)
    for i, job in enumerate(unique_jobs, 1):
        print(f"{i:2d}. {job['title']}")
        print(f"    Location: {job['location']}")
        print(f"    Type: {job['type']}")
        print()

def extract_visible_jobs(soup):
    """Extract visible jobs from HTML"""
    jobs = []
    job_elements = soup.select('.job-item')
    
    for element in job_elements:
        # Skip hidden elements
        if element.get('style') and ('display: none' in element.get('style') or 
                                   'visibility: hidden' in element.get('style') or
                                   'opacity: 0' in element.get('style')):
            continue
        
        title_elem = element.select_one('h3')
        if title_elem:
            title = title_elem.get_text(strip=True)
            
            # Extract location
            location = "Unknown"
            location_elem = element.select_one('p')
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                if 'Location:' in location_text:
                    location = location_text.replace('Location:', '').strip()
            
            jobs.append({
                'title': title,
                'location': location,
                'type': 'Unknown',
                'source': 'visible'
            })
    
    return jobs

def extract_from_javascript_data(html_content):
    """Extract jobs from JavaScript data in HTML"""
    jobs = []
    
    # Look for job data in script tags
    patterns = [
        r'jobs?\s*[:=]\s*(\[.*?\])',
        r'positions?\s*[:=]\s*(\[.*?\])',
        r'careers?\s*[:=]\s*(\[.*?\])'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            try:
                job_data = json.loads(match)
                if isinstance(job_data, list):
                    for job in job_data:
                        if isinstance(job, dict) and 'title' in job:
                            jobs.append({
                                'title': job.get('title', 'Unknown'),
                                'location': job.get('location', 'Unknown'),
                                'type': job.get('type', 'Unknown'),
                                'source': 'javascript'
                            })
            except json.JSONDecodeError:
                continue
    
    return jobs

def extract_from_hidden_elements(soup):
    """Extract jobs from hidden elements"""
    jobs = []
    
    # Find elements with hidden styles
    hidden_selectors = [
        '[style*="display: none"]',
        '[style*="visibility: hidden"]',
        '[style*="opacity: 0"]'
    ]
    
    for selector in hidden_selectors:
        elements = soup.select(selector)
        for element in elements:
            job_elements = element.select('.job-item')
            for job_elem in job_elements:
                title_elem = job_elem.select_one('h3')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    
                    # Extract location
                    location = "Unknown"
                    location_elem = job_elem.select_one('p')
                    if location_elem:
                        location_text = location_elem.get_text(strip=True)
                        if 'Location:' in location_text:
                            location = location_text.replace('Location:', '').strip()
                    
                    jobs.append({
                        'title': title,
                        'location': location,
                        'type': 'Unknown',
                        'source': 'hidden_elements'
                    })
    
    return jobs

def extract_from_modal_content(soup):
    """Extract jobs from modal content"""
    jobs = []
    
    modal_elements = soup.select('.modal, .popup, [role="dialog"]')
    for modal in modal_elements:
        job_elements = modal.select('.job-item')
        for job_elem in job_elements:
            title_elem = job_elem.select_one('h3')
            if title_elem:
                title = title_elem.get_text(strip=True)
                
                # Extract location
                location = "Unknown"
                location_elem = job_elem.select_one('p')
                if location_elem:
                    location_text = location_elem.get_text(strip=True)
                    if 'Location:' in location_text:
                        location = location_text.replace('Location:', '').strip()
                
                jobs.append({
                    'title': title,
                    'location': location,
                    'type': 'Unknown',
                    'source': 'modal'
                })
    
    return jobs

def extract_from_tabs_accordions(soup):
    """Extract jobs from tabs and accordions"""
    jobs = []
    
    # Find tab content
    tab_content_elements = soup.select('.tab-content, [role="tabpanel"]')
    for tab_content in tab_content_elements:
        job_elements = tab_content.select('.job-item')
        for job_elem in job_elements:
            title_elem = job_elem.select_one('h3')
            if title_elem:
                title = title_elem.get_text(strip=True)
                
                # Extract location
                location = "Unknown"
                location_elem = job_elem.select_one('p')
                if location_elem:
                    location_text = location_elem.get_text(strip=True)
                    if 'Location:' in location_text:
                        location = location_text.replace('Location:', '').strip()
                
                jobs.append({
                    'title': title,
                    'location': location,
                    'type': 'Unknown',
                    'source': 'tabs_accordions'
                })
    
    return jobs

def show_technique_explanations():
    """Show detailed explanations of each technique"""
    print("\n🔧 Detailed Technique Explanations")
    print("=" * 60)
    
    techniques = {
        "1. Dynamic Content Loading": {
            "description": "Wait for JavaScript to load job listings",
            "when_to_use": "Modern websites that load content dynamically",
            "example": "Career pages that show loading spinners",
            "code": "await page.wait_for_selector('.job-list', timeout=5000)"
        },
        "2. Expand/Collapse Elements": {
            "description": "Click buttons to reveal hidden job sections",
            "when_to_use": "Pages with 'Show More' or 'Load More' buttons",
            "example": "Career pages that initially show only 10 jobs",
            "code": "await element.click() if await element.is_visible()"
        },
        "3. Lazy Loading": {
            "description": "Scroll to trigger loading of more jobs",
            "when_to_use": "Infinite scroll or lazy-loaded content",
            "example": "Social media style job listings",
            "code": "await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')"
        },
        "4. Tabs/Accordions": {
            "description": "Switch between different job categories",
            "when_to_use": "Pages organized by department or location",
            "example": "Engineering, Design, Marketing tabs",
            "code": "await tab.click() for tab in tabs"
        },
        "5. JavaScript Data": {
            "description": "Extract job data from script tags",
            "when_to_use": "SPA applications that embed data in HTML",
            "example": "React/Vue.js career pages",
            "code": "const jobs = JSON.parse(scriptContent.match(/jobs?:\\s*(\\[.*?\\])/)[1])"
        },
        "6. API Calls": {
            "description": "Intercept network requests for job data",
            "when_to_use": "Modern APIs that serve job data",
            "example": "REST APIs with /api/jobs endpoints",
            "code": "await page.route('**/api/jobs', lambda route: capture_response(route))"
        },
        "7. Hidden Elements": {
            "description": "Find elements with display:none or visibility:hidden",
            "when_to_use": "Pages that hide content with CSS",
            "example": "Collapsed sections or hidden modals",
            "code": "const hiddenElements = document.querySelectorAll('*[style*=\"display: none\"]')"
        },
        "8. Pagination": {
            "description": "Navigate through multiple pages of jobs",
            "when_to_use": "Traditional paginated job listings",
            "example": "Page 1, 2, 3 navigation",
            "code": "await nextButton.click() while hasNextPage"
        },
        "9. Search Filters": {
            "description": "Apply different filters to reveal more jobs",
            "when_to_use": "Pages with department/location filters",
            "example": "Filter by Engineering department",
            "code": "await filter.select_option('engineering')"
        },
        "10. Modal/Popup Content": {
            "description": "Extract jobs from modal dialogs",
            "when_to_use": "Pages with popup job listings",
            "example": "Click 'View All Positions' to open modal",
            "code": "await modalTrigger.click(); const modalJobs = await extractFromModal()"
        }
    }
    
    for technique, details in techniques.items():
        print(f"\n🎯 {technique}")
        print(f"   Description: {details['description']}")
        print(f"   When to use: {details['when_to_use']}")
        print(f"   Example: {details['example']}")
        print(f"   Code: {details['code']}")

def show_usage_tips():
    """Show practical usage tips"""
    print("\n💡 Practical Usage Tips")
    print("=" * 60)
    
    tips = [
        "🎯 Start with the main career page URL (e.g., /careers, /jobs, /tuyen-dung)",
        "⏱️ Be patient - JavaScript-heavy sites need time to load",
        "🔍 Try different filter combinations (Engineering, Design, Marketing)",
        "📜 Scroll down to trigger lazy loading",
        "🪟 Look for 'View All Positions' or 'Load More' buttons",
        "💻 Check browser DevTools for API calls",
        "👻 Look for hidden elements with display:none",
        "📄 Navigate through pagination if available",
        "🔄 Switch between tabs/accordions",
        "📱 Test on different viewport sizes"
    ]
    
    for tip in tips:
        print(f"   {tip}")
    
    print("\n🚀 Best Practices:")
    print("   - Use Playwright for JavaScript-heavy sites")
    print("   - Combine multiple techniques for best results")
    print("   - Handle errors gracefully")
    print("   - Respect rate limits and robots.txt")
    print("   - Cache results to avoid repeated requests")

def main():
    """Main demonstration function"""
    print("🚀 Hidden Job Extraction Demonstration")
    print("=" * 60)
    
    try:
        # Demonstrate techniques
        demonstrate_hidden_job_techniques()
        
        # Show detailed explanations
        show_technique_explanations()
        
        # Show usage tips
        show_usage_tips()
        
        print("\n✅ Demonstration completed successfully!")
        print("\n📝 Next steps:")
        print("   1. Install Playwright: pip install playwright")
        print("   2. Install browsers: playwright install")
        print("   3. Test with real URLs: python3 test_hidden_job_extraction.py https://example.com/careers")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 