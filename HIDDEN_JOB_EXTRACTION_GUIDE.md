# Hướng dẫn cào Job Ẩn trong Career Page

## Tổng quan

Job ẩn là những job listing không hiển thị ngay lập tức trên career page mà cần tương tác để hiện ra. Hệ thống mới đã được tích hợp 10 kỹ thuật khác nhau để cào được job ẩn.

## Các loại Job Ẩn thường gặp

### 1. 🔍 Job được load bằng JavaScript
```html
<script>
const jobs = [
    {
        "title": "Senior Developer",
        "location": "Ho Chi Minh City",
        "type": "Full-time"
    }
];
</script>
```

### 2. 📂 Job trong collapsed sections
```html
<div class="collapsed-jobs" style="display: none;">
    <div class="job-item">Backend Developer</div>
</div>
<button class="expand">Show More</button>
```

### 3. 📜 Job được lazy load
```html
<div class="job-list">
    <div class="job-item">Job 1</div>
    <div class="job-item">Job 2</div>
    <!-- More jobs load when scroll -->
</div>
```

### 4. 🔄 Job trong tabs/accordions
```html
<div class="tabs">
    <div class="tab" data-tab="engineering">Engineering</div>
    <div class="tab" data-tab="design">Design</div>
</div>
<div class="tab-content" id="engineering">
    <div class="job-item">Software Engineer</div>
</div>
```

### 5. 💻 Job từ API calls
```javascript
fetch('/api/jobs')
    .then(response => response.json())
    .then(jobs => displayJobs(jobs));
```

### 6. 👻 Job trong hidden elements
```html
<div style="display: none;">
    <div class="job-item">Hidden Job</div>
</div>
```

### 7. 📄 Job trong pagination
```html
<div class="pagination">
    <a href="?page=1">1</a>
    <a href="?page=2">2</a>
    <a href="?page=3">3</a>
</div>
```

### 8. 🔍 Job từ search filters
```html
<select name="department">
    <option value="engineering">Engineering</option>
    <option value="design">Design</option>
</select>
```

### 9. 🪟 Job trong modal/popup
```html
<button data-toggle="modal" data-target="#jobModal">View All Jobs</button>
<div class="modal" id="jobModal">
    <div class="job-item">Modal Job</div>
</div>
```

## 10 Kỹ thuật cào Job Ẩn

### 1. 🔍 Wait for Dynamic Content
```python
async def _wait_for_dynamic_content(self, page: Page):
    # Wait for job loading indicators
    selectors = [
        '.job-list', '.career-list', '.position-list',
        '.loading', '.spinner', '.loader'
    ]
    
    for selector in selectors:
        try:
            await page.wait_for_selector(selector, timeout=5000)
            break
        except:
            continue
    
    # Wait for network idle
    await page.wait_for_load_state('networkidle', timeout=10000)
    await page.wait_for_timeout(3000)
```

### 2. 📂 Expand/Collapse Elements
```python
async def _expand_collapsed_sections(self, page: Page):
    expand_selectors = [
        '.expand', '.collapse', '.toggle',
        '.show-more', '.load-more', '.view-more',
        '[data-toggle="collapse"]', '.accordion-button'
    ]
    
    for selector in expand_selectors:
        elements = await page.query_selector_all(selector)
        for element in elements:
            if await element.is_visible():
                await element.click()
                await page.wait_for_timeout(1000)
```

### 3. 📜 Trigger Lazy Loading
```python
async def _trigger_lazy_loading(self, page: Page):
    for i in range(3):
        # Scroll to bottom
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        
        # Check if new content loaded
        job_count_before = await page.query_selector_all('.job-item')
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        job_count_after = await page.query_selector_all('.job-item')
        
        # Stop if no new jobs loaded
        if len(job_count_after) <= len(job_count_before):
            break
```

### 4. 🔄 Switch Tabs/Accordions
```python
async def _switch_tabs_and_accordions(self, page: Page):
    tab_selectors = [
        '.tab', '.tab-item', '[role="tab"]',
        '.job-tab', '.career-tab'
    ]
    
    for selector in tab_selectors:
        tabs = await page.query_selector_all(selector)
        for tab in tabs:
            if await tab.is_visible():
                await tab.click()
                await page.wait_for_timeout(2000)
```

### 5. 💻 Extract from JavaScript Data
```python
async def _extract_from_javascript_data(self, page: Page):
    script_content = await page.evaluate("""
        () => {
            const scripts = document.querySelectorAll('script');
            const jobData = [];
            
            for (const script of scripts) {
                const content = script.textContent || script.innerHTML;
                
                // Look for job-related JSON data
                const patterns = [
                    /jobs?\s*[:=]\s*(\[.*?\])/gi,
                    /positions?\s*[:=]\s*(\[.*?\])/gi,
                    /careers?\s*[:=]\s*(\[.*?\])/gi
                ];
                
                for (const pattern of patterns) {
                    const matches = content.match(pattern);
                    if (matches) {
                        try {
                            const data = JSON.parse(matches[1]);
                            jobData.push(...data);
                        } catch (e) {
                            // Handle invalid JSON
                        }
                    }
                }
            }
            
            return jobData;
        }
    """)
```

### 6. 🌐 Extract from API Calls
```python
async def _extract_from_api_calls(self, page: Page, base_url: str):
    api_responses = await page.evaluate("""
        () => {
            return new Promise((resolve) => {
                const responses = [];
                
                // Override fetch to capture responses
                const originalFetch = window.fetch;
                window.fetch = async (...args) => {
                    const response = await originalFetch(...args);
                    
                    const url = args[0];
                    if (typeof url === 'string' && (
                        url.includes('job') || 
                        url.includes('career') || 
                        url.includes('position') ||
                        url.includes('api')
                    )) {
                        try {
                            const clone = response.clone();
                            const data = await clone.json();
                            responses.push({ url, data });
                        } catch (e) {
                            // Not JSON response
                        }
                    }
                    
                    return response;
                };
                
                setTimeout(() => resolve(responses), 5000);
            });
        }
    """)
```

### 7. 👻 Extract from Hidden Elements
```python
async def _extract_from_hidden_elements(self, page: Page):
    hidden_elements = await page.evaluate("""
        () => {
            const hiddenElements = [];
            const allElements = document.querySelectorAll('*');
            
            for (const element of allElements) {
                const style = window.getComputedStyle(element);
                const isHidden = style.display === 'none' || 
                               style.visibility === 'hidden' ||
                               style.opacity === '0';
                
                if (isHidden) {
                    const text = element.textContent || '';
                    const hasJobKeywords = /job|career|position|hiring|recruitment|tuyển dụng|việc làm/i.test(text);
                    
                    if (hasJobKeywords) {
                        hiddenElements.push({
                            tagName: element.tagName,
                            className: element.className,
                            text: text.substring(0, 500)
                        });
                    }
                }
            }
            
            return hiddenElements;
        }
    """)
```

### 8. 📄 Extract from Pagination
```python
async def _extract_from_pagination(self, page: Page):
    page_number = 1
    max_pages = 10
    
    while page_number <= max_pages:
        # Look for next page button
        next_button = None
        pagination_selectors = [
            '.pagination', '.next', '.page-number',
            '.load-more', '.show-more'
        ]
        
        for selector in pagination_selectors:
            buttons = await page.query_selector_all(selector)
            for button in buttons:
                button_text = await button.text_content()
                if button_text and any(keyword in button_text.lower() 
                                     for keyword in ['next', '>', '»', 'more', 'load']):
                    next_button = button
                    break
            if next_button:
                break
        
        if not next_button:
            break
        
        # Click next page
        await next_button.click()
        await page.wait_for_timeout(3000)
        
        # Extract jobs from current page
        page_jobs = await self._extract_jobs_from_current_page(page)
        jobs.extend(page_jobs)
        
        page_number += 1
```

### 9. 🔍 Extract from Search Filters
```python
async def _extract_from_search_filters(self, page: Page):
    filter_combinations = [
        {'department': 'engineering', 'location': 'all'},
        {'department': 'design', 'location': 'all'},
        {'department': 'marketing', 'location': 'all'},
        {'type': 'full-time', 'location': 'all'},
        {'type': 'remote', 'location': 'all'},
        {'level': 'senior', 'location': 'all'},
        {'level': 'junior', 'location': 'all'}
    ]
    
    for combination in filter_combinations:
        # Apply filters
        for filter_name, filter_value in combination.items():
            await self._apply_filter(page, filter_name, filter_value)
        
        # Wait for results to load
        await page.wait_for_timeout(3000)
        
        # Extract jobs from filtered results
        filtered_jobs = await self._extract_jobs_from_current_page(page)
        jobs.extend(filtered_jobs)
```

### 10. 🪟 Extract from Modals
```python
async def _extract_from_modals(self, page: Page):
    modal_triggers = await page.query_selector_all(
        '[data-toggle="modal"], [data-bs-toggle="modal"], .modal-trigger'
    )
    
    for trigger in modal_triggers:
        if await trigger.is_visible():
            # Click to open modal
            await trigger.click()
            await page.wait_for_timeout(2000)
            
            # Extract content from modal
            modal_content = await page.query_selector('.modal, .popup, [role="dialog"]')
            if modal_content:
                modal_jobs = await self._extract_jobs_from_element(modal_content)
                jobs.extend(modal_jobs)
            
            # Close modal
            close_button = await page.query_selector('.modal .close, .modal .btn-close')
            if close_button:
                await close_button.click()
                await page.wait_for_timeout(1000)
```

## Cách sử dụng

### 1. Sử dụng với Crawler chính
```python
from app.services.crawler import crawl_single_url

# Crawl career page với hidden job extraction
result = await crawl_single_url("https://company.com/careers")

# Kết quả
hidden_jobs = result.get('hidden_jobs', [])
visible_jobs = result.get('visible_jobs', [])
total_jobs = result.get('total_jobs', [])

print(f"Total jobs found: {len(total_jobs)}")
print(f"Hidden jobs: {len(hidden_jobs)}")
print(f"Visible jobs: {len(visible_jobs)}")
```

### 2. Sử dụng trực tiếp HiddenJobExtractor
```python
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
```

## Cấu hình và tùy chỉnh

### 1. Điều chỉnh timeout
```python
# Trong constants.py
DEFAULT_TIMEOUT = 15000  # 15 seconds
CAREER_SCORE_THRESHOLD = 6
JOB_LINK_SCORE_THRESHOLD = 5
```

### 2. Thêm selectors mới
```python
# Trong constants.py
JOB_LINK_SELECTORS = [
    # Existing selectors...
    '.custom-job-selector',  # Add your custom selector
    '[data-custom-job]'      # Add your custom data attribute
]
```

### 3. Tùy chỉnh filter combinations
```python
# Trong hidden_job_extractor.py
filter_combinations = [
    {'department': 'engineering', 'location': 'all'},
    {'department': 'design', 'location': 'all'},
    # Add your custom combinations
    {'department': 'sales', 'location': 'hcm'},
    {'type': 'part-time', 'location': 'hanoi'}
]
```

## Tips và Best Practices

### 1. 🎯 Chọn đúng career page
- Tìm URL có pattern: `/careers`, `/jobs`, `/tuyen-dung`
- Tránh các trang: `/about`, `/contact`, `/blog`

### 2. ⏱️ Kiên nhẫn với loading
- JavaScript-heavy sites cần thời gian load
- Sử dụng `networkidle` wait state
- Thêm delay giữa các actions

### 3. 🔍 Thử nhiều filter combinations
- Engineering, Design, Marketing
- Full-time, Part-time, Remote
- Senior, Junior, Lead levels

### 4. 📜 Scroll và pagination
- Scroll xuống để trigger lazy loading
- Click "Load More" buttons
- Navigate qua các trang pagination

### 5. 🪟 Check modals và popups
- Click "View All Positions" buttons
- Look for modal triggers
- Extract content từ dialog boxes

### 6. 💻 Monitor network requests
- Check browser DevTools Network tab
- Look for API calls to `/api/jobs`, `/api/careers`
- Intercept và parse JSON responses

### 7. 👻 Find hidden elements
- Elements với `display: none`
- Elements với `visibility: hidden`
- Elements với `opacity: 0`

## Troubleshooting

### 1. Không tìm thấy job nào
```python
# Check if page loaded properly
await page.wait_for_load_state('networkidle')
await page.wait_for_timeout(5000)

# Check for job-related elements
job_elements = await page.query_selector_all('.job-item, .career-item')
print(f"Found {len(job_elements)} job elements")
```

### 2. JavaScript errors
```python
# Enable JavaScript error logging
page.on('console', lambda msg: print(f'Console: {msg.text}'))
page.on('pageerror', lambda err: print(f'Page error: {err}'))
```

### 3. Timeout issues
```python
# Increase timeout for slow sites
await page.wait_for_selector('.job-list', timeout=30000)  # 30 seconds
```

### 4. Rate limiting
```python
# Add delays between requests
import time
time.sleep(2)  # Wait 2 seconds between requests
```

## Kết luận

Với 10 kỹ thuật khác nhau, hệ thống có thể cào được hầu hết các loại job ẩn:

- ✅ JavaScript-loaded jobs
- ✅ Collapsed/expanded sections
- ✅ Lazy-loaded content
- ✅ Tab/accordion content
- ✅ API-served jobs
- ✅ Hidden elements
- ✅ Pagination content
- ✅ Filtered results
- ✅ Modal/popup content

Hệ thống tự động thử tất cả các kỹ thuật và kết hợp kết quả để có được danh sách job đầy đủ nhất có thể. 