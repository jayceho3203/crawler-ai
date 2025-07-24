# app/services/hidden_job_extractor.py
"""
Hidden job extraction service
Handles various types of hidden job listings in career pages
"""

import re
import json
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
from playwright.async_api import async_playwright, Page

class HiddenJobExtractor:
    """Extract hidden jobs from career pages using various techniques"""
    
    def __init__(self):
        self.extracted_jobs = []
        self.visited_urls = set()
        
    async def extract_hidden_jobs_from_page(self, url: str, page: Page) -> List[Dict]:
        """Extract hidden jobs using multiple techniques"""
        jobs = []
        
        try:
            # Technique 1: Wait for dynamic content to load
            await self._wait_for_dynamic_content(page)
            
            # Technique 2: Click on expand/collapse elements
            await self._expand_collapsed_sections(page)
            
            # Technique 3: Scroll to trigger lazy loading
            await self._trigger_lazy_loading(page)
            
            # Technique 4: Switch between tabs/accordions
            await self._switch_tabs_and_accordions(page)
            
            # Technique 5: Extract from JavaScript data
            js_jobs = await self._extract_from_javascript_data(page)
            jobs.extend(js_jobs)
            
            # Technique 6: Extract from API calls
            api_jobs = await self._extract_from_api_calls(page, url)
            jobs.extend(api_jobs)
            
            # Technique 7: Extract from hidden elements
            hidden_jobs = await self._extract_from_hidden_elements(page)
            jobs.extend(hidden_jobs)
            
            # Technique 8: Extract from pagination
            pagination_jobs = await self._extract_from_pagination(page)
            jobs.extend(pagination_jobs)
            
            # Technique 9: Extract from search/filter results
            filter_jobs = await self._extract_from_search_filters(page)
            jobs.extend(filter_jobs)
            
            # Technique 10: Extract from modal/popup content
            modal_jobs = await self._extract_from_modals(page)
            jobs.extend(modal_jobs)
            
        except Exception as e:
            print(f"Error extracting hidden jobs: {str(e)}")
        
        return jobs
    
    async def _wait_for_dynamic_content(self, page: Page):
        """Wait for dynamic content to load"""
        try:
            # Wait for common job loading indicators
            selectors = [
                '.job-list', '.career-list', '.position-list',
                '.job-item', '.career-item', '.position-item',
                '[data-job]', '[data-position]', '[data-career]',
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
            
            # Additional wait for JavaScript execution
            await page.wait_for_timeout(3000)
            
        except Exception as e:
            print(f"Error waiting for dynamic content: {str(e)}")
    
    async def _expand_collapsed_sections(self, page: Page):
        """Click on expand/collapse elements to reveal hidden content"""
        try:
            # Common expand/collapse selectors
            expand_selectors = [
                '.expand', '.collapse', '.toggle',
                '.show-more', '.load-more', '.view-more',
                '[data-toggle="collapse"]', '[data-bs-toggle="collapse"]',
                '.accordion-button', '.accordion-header',
                '.expand-btn', '.more-btn', '.load-btn',
                'button[aria-expanded="false"]',
                '.job-expand', '.position-expand'
            ]
            
            for selector in expand_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        # Check if element is visible and clickable
                        is_visible = await element.is_visible()
                        if is_visible:
                            await element.click()
                            await page.wait_for_timeout(1000)  # Wait for content to load
                except:
                    continue
                    
        except Exception as e:
            print(f"Error expanding collapsed sections: {str(e)}")
    
    async def _trigger_lazy_loading(self, page: Page):
        """Scroll to trigger lazy loading of job listings"""
        try:
            # Scroll to bottom multiple times to trigger lazy loading
            for i in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
                # Check if new content loaded
                job_count_before = await page.query_selector_all('.job-item, .career-item, .position-item')
                
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
                job_count_after = await page.query_selector_all('.job-item, .career-item, .position-item')
                
                # If no new jobs loaded, stop scrolling
                if len(job_count_after) <= len(job_count_before):
                    break
                    
        except Exception as e:
            print(f"Error triggering lazy loading: {str(e)}")
    
    async def _switch_tabs_and_accordions(self, page: Page):
        """Switch between tabs and accordions to reveal hidden jobs"""
        try:
            # Tab selectors
            tab_selectors = [
                '.tab', '.tab-item', '.nav-tab',
                '[role="tab"]', '[data-tab]', '[data-bs-tab]',
                '.job-tab', '.career-tab', '.position-tab'
            ]
            
            for selector in tab_selectors:
                try:
                    tabs = await page.query_selector_all(selector)
                    for tab in tabs:
                        if await tab.is_visible():
                            await tab.click()
                            await page.wait_for_timeout(2000)  # Wait for content to load
                except:
                    continue
            
            # Accordion selectors
            accordion_selectors = [
                '.accordion-item', '.accordion-header',
                '.collapse-header', '.expand-header',
                '[data-toggle="collapse"]', '[data-bs-toggle="collapse"]'
            ]
            
            for selector in accordion_selectors:
                try:
                    accordions = await page.query_selector_all(selector)
                    for accordion in accordions:
                        if await accordion.is_visible():
                            await accordion.click()
                            await page.wait_for_timeout(1000)
                except:
                    continue
                    
        except Exception as e:
            print(f"Error switching tabs/accordions: {str(e)}")
    
    async def _extract_from_javascript_data(self, page: Page) -> List[Dict]:
        """Extract jobs from JavaScript data embedded in the page"""
        jobs = []
        
        try:
            # Look for JSON data in script tags
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
                            /careers?\s*[:=]\s*(\[.*?\])/gi,
                            /openings?\s*[:=]\s*(\[.*?\])/gi,
                            /opportunities?\s*[:=]\s*(\[.*?\])/gi,
                            /vacancies?\s*[:=]\s*(\[.*?\])/gi
                        ];
                        
                        for (const pattern of patterns) {
                            const matches = content.match(pattern);
                            if (matches) {
                                try {
                                    const data = JSON.parse(matches[1]);
                                    if (Array.isArray(data)) {
                                        jobData.push(...data);
                                    }
                                } catch (e) {
                                    // Try to extract individual job objects
                                    const jobMatches = content.match(/\{[^}]*"title"[^}]*\}/gi);
                                    if (jobMatches) {
                                        for (const jobMatch of jobMatches) {
                                            try {
                                                const job = JSON.parse(jobMatch);
                                                jobData.push(job);
                                            } catch (e2) {
                                                // Skip invalid JSON
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    return jobData;
                }
            """)
            
            # Process extracted job data
            for job_data in script_content:
                if isinstance(job_data, dict):
                    job = self._normalize_job_data(job_data)
                    if job:
                        jobs.append(job)
                        
        except Exception as e:
            print(f"Error extracting from JavaScript data: {str(e)}")
        
        return jobs
    
    async def _extract_from_api_calls(self, page: Page, base_url: str) -> List[Dict]:
        """Extract jobs from API calls made by the page"""
        jobs = []
        
        try:
            # Intercept network requests to find job-related APIs
            api_responses = await page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        const responses = [];
                        
                        // Override fetch to capture responses
                        const originalFetch = window.fetch;
                        window.fetch = async (...args) => {
                            const response = await originalFetch(...args);
                            
                            // Check if this is a job-related API call
                            const url = args[0];
                            if (typeof url === 'string' && (
                                url.includes('job') || 
                                url.includes('career') || 
                                url.includes('position') ||
                                url.includes('api') ||
                                url.includes('data')
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
                        
                        // Wait a bit for API calls to complete
                        setTimeout(() => resolve(responses), 5000);
                    });
                }
            """)
            
            # Process API responses
            for response in api_responses:
                if isinstance(response.get('data'), list):
                    for job_data in response['data']:
                        if isinstance(job_data, dict):
                            job = self._normalize_job_data(job_data)
                            if job:
                                jobs.append(job)
                                
        except Exception as e:
            print(f"Error extracting from API calls: {str(e)}")
        
        return jobs
    
    async def _extract_from_hidden_elements(self, page: Page) -> List[Dict]:
        """Extract jobs from hidden elements (display: none, visibility: hidden)"""
        jobs = []
        
        try:
            # Find hidden elements that might contain job data
            hidden_elements = await page.evaluate("""
                () => {
                    const hiddenElements = [];
                    
                    // Find elements with display: none or visibility: hidden
                    const allElements = document.querySelectorAll('*');
                    
                    for (const element of allElements) {
                        const style = window.getComputedStyle(element);
                        const isHidden = style.display === 'none' || 
                                       style.visibility === 'hidden' ||
                                       style.opacity === '0';
                        
                        if (isHidden) {
                            // Check if element contains job-related content
                            const text = element.textContent || '';
                            const hasJobKeywords = /job|career|position|hiring|recruitment|tuyển dụng|việc làm/i.test(text);
                            
                            if (hasJobKeywords) {
                                hiddenElements.push({
                                    tagName: element.tagName,
                                    className: element.className,
                                    id: element.id,
                                    text: text.substring(0, 500),
                                    html: element.innerHTML.substring(0, 1000)
                                });
                            }
                        }
                    }
                    
                    return hiddenElements;
                }
            """)
            
            # Process hidden elements
            for element in hidden_elements:
                job = self._extract_job_from_element_data(element)
                if job:
                    jobs.append(job)
                    
        except Exception as e:
            print(f"Error extracting from hidden elements: {str(e)}")
        
        return jobs
    
    async def _extract_from_pagination(self, page: Page) -> List[Dict]:
        """Extract jobs from pagination by navigating through pages"""
        jobs = []
        
        try:
            # Find pagination elements
            pagination_selectors = [
                '.pagination', '.pager', '.page-nav',
                '.next', '.prev', '.page-number',
                '[data-page]', '[aria-label*="page"]',
                '.load-more', '.show-more', '.view-more'
            ]
            
            page_number = 1
            max_pages = 10  # Limit to prevent infinite loops
            
            while page_number <= max_pages:
                # Look for next page button
                next_button = None
                for selector in pagination_selectors:
                    try:
                        buttons = await page.query_selector_all(selector)
                        for button in buttons:
                            button_text = await button.text_content()
                            if button_text and any(keyword in button_text.lower() for keyword in ['next', '>', '»', 'more', 'load']):
                                next_button = button
                                break
                        if next_button:
                            break
                    except:
                        continue
                
                if not next_button:
                    break
                
                # Click next page
                try:
                    await next_button.click()
                    await page.wait_for_timeout(3000)  # Wait for content to load
                    
                    # Extract jobs from current page
                    page_jobs = await self._extract_jobs_from_current_page(page)
                    jobs.extend(page_jobs)
                    
                    page_number += 1
                except:
                    break
                    
        except Exception as e:
            print(f"Error extracting from pagination: {str(e)}")
        
        return jobs
    
    async def _extract_from_search_filters(self, page: Page) -> List[Dict]:
        """Extract jobs by applying different search filters"""
        jobs = []
        
        try:
            # Common job filter selectors
            filter_selectors = [
                'select[name*="department"]', 'select[name*="location"]',
                'select[name*="type"]', 'select[name*="level"]',
                'input[name*="keyword"]', 'input[name*="search"]',
                '.filter-select', '.filter-dropdown', '.filter-option'
            ]
            
            # Try different filter combinations
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
                try:
                    # Apply filters
                    for filter_name, filter_value in combination.items():
                        await self._apply_filter(page, filter_name, filter_value)
                    
                    # Wait for results to load
                    await page.wait_for_timeout(3000)
                    
                    # Extract jobs from filtered results
                    filtered_jobs = await self._extract_jobs_from_current_page(page)
                    jobs.extend(filtered_jobs)
                    
                except Exception as e:
                    print(f"Error applying filter combination {combination}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error extracting from search filters: {str(e)}")
        
        return jobs
    
    async def _extract_from_modals(self, page: Page) -> List[Dict]:
        """Extract jobs from modal/popup content"""
        jobs = []
        
        try:
            # Look for modal triggers
            modal_triggers = await page.query_selector_all(
                '[data-toggle="modal"], [data-bs-toggle="modal"], .modal-trigger, .popup-trigger'
            )
            
            for trigger in modal_triggers:
                try:
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
                        close_button = await page.query_selector('.modal .close, .modal .btn-close, [data-dismiss="modal"]')
                        if close_button:
                            await close_button.click()
                            await page.wait_for_timeout(1000)
                            
                except Exception as e:
                    print(f"Error extracting from modal: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error extracting from modals: {str(e)}")
        
        return jobs
    
    async def _extract_jobs_from_current_page(self, page: Page) -> List[Dict]:
        """Extract jobs from the current page content"""
        jobs = []
        
        try:
            # Common job element selectors
            job_selectors = [
                '.job-item', '.career-item', '.position-item',
                '.job-card', '.career-card', '.position-card',
                '.job-listing', '.career-listing', '.position-listing',
                '[data-job]', '[data-position]', '[data-career]',
                'article', '.card', '.item'
            ]
            
            for selector in job_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        job = await self._extract_job_from_element(element)
                        if job:
                            jobs.append(job)
                except:
                    continue
                    
        except Exception as e:
            print(f"Error extracting jobs from current page: {str(e)}")
        
        return jobs
    
    async def _extract_job_from_element(self, element) -> Optional[Dict]:
        """Extract job information from a single element"""
        try:
            # Extract text content
            text_content = await element.text_content()
            if not text_content or len(text_content.strip()) < 10:
                return None
            
            # Extract job title
            title = await self._extract_job_title(element)
            if not title:
                return None
            
            # Extract other job details
            job = {
                'title': title,
                'description': text_content[:500] + '...' if len(text_content) > 500 else text_content,
                'location': await self._extract_job_location(element),
                'company': await self._extract_job_company(element),
                'job_type': await self._extract_job_type(element),
                'salary': await self._extract_job_salary(element),
                'requirements': await self._extract_job_requirements(element),
                'url': await self._extract_job_url(element),
                'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return job
            
        except Exception as e:
            print(f"Error extracting job from element: {str(e)}")
            return None
    
    async def _extract_job_title(self, element) -> Optional[str]:
        """Extract job title from element"""
        try:
            # Look for title in headings
            title_selectors = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', '.title', '.job-title', '.position-title']
            
            for selector in title_selectors:
                title_elem = await element.query_selector(selector)
                if title_elem:
                    title = await title_elem.text_content()
                    if title and len(title.strip()) > 3:
                        return title.strip()
            
            # Look for title in data attributes
            title_attr = await element.get_attribute('data-title') or await element.get_attribute('title')
            if title_attr:
                return title_attr.strip()
            
            return None
            
        except Exception as e:
            return None
    
    async def _extract_job_location(self, element) -> Optional[str]:
        """Extract job location from element"""
        try:
            location_selectors = ['.location', '.job-location', '.position-location', '[data-location]']
            
            for selector in location_selectors:
                location_elem = await element.query_selector(selector)
                if location_elem:
                    location = await location_elem.text_content()
                    if location and len(location.strip()) > 2:
                        return location.strip()
            
            return None
            
        except Exception as e:
            return None
    
    async def _extract_job_company(self, element) -> Optional[str]:
        """Extract company name from element"""
        try:
            company_selectors = ['.company', '.job-company', '.position-company', '[data-company]']
            
            for selector in company_selectors:
                company_elem = await element.query_selector(selector)
                if company_elem:
                    company = await company_elem.text_content()
                    if company and len(company.strip()) > 2:
                        return company.strip()
            
            return None
            
        except Exception as e:
            return None
    
    async def _extract_job_type(self, element) -> Optional[str]:
        """Extract job type from element"""
        try:
            type_selectors = ['.job-type', '.position-type', '.employment-type', '[data-type]']
            
            for selector in type_selectors:
                type_elem = await element.query_selector(selector)
                if type_elem:
                    job_type = await type_elem.text_content()
                    if job_type and len(job_type.strip()) > 2:
                        return job_type.strip()
            
            return None
            
        except Exception as e:
            return None
    
    async def _extract_job_salary(self, element) -> Optional[str]:
        """Extract salary information from element"""
        try:
            salary_selectors = ['.salary', '.job-salary', '.position-salary', '[data-salary]']
            
            for selector in salary_selectors:
                salary_elem = await element.query_selector(selector)
                if salary_elem:
                    salary = await salary_elem.text_content()
                    if salary and len(salary.strip()) > 2:
                        return salary.strip()
            
            return None
            
        except Exception as e:
            return None
    
    async def _extract_job_requirements(self, element) -> List[str]:
        """Extract job requirements from element"""
        try:
            requirements = []
            req_selectors = ['.requirements', '.job-requirements', '.position-requirements', '.qualifications']
            
            for selector in req_selectors:
                req_elem = await element.query_selector(selector)
                if req_elem:
                    req_text = await req_elem.text_content()
                    if req_text:
                        # Split requirements into list
                        req_list = [req.strip() for req in req_text.split('\n') if req.strip()]
                        requirements.extend(req_list)
            
            return requirements
            
        except Exception as e:
            return []
    
    async def _extract_job_url(self, element) -> Optional[str]:
        """Extract job URL from element"""
        try:
            # Look for link within the element
            link = await element.query_selector('a[href]')
            if link:
                href = await link.get_attribute('href')
                if href:
                    return href
            
            # Look for data-url attribute
            data_url = await element.get_attribute('data-url')
            if data_url:
                return data_url
            
            return None
            
        except Exception as e:
            return None
    
    async def _apply_filter(self, page: Page, filter_name: str, filter_value: str):
        """Apply a filter to the page"""
        try:
            # Find filter element
            filter_selectors = [
                f'select[name*="{filter_name}"]',
                f'input[name*="{filter_name}"]',
                f'[data-filter="{filter_name}"]',
                f'.filter-{filter_name}'
            ]
            
            for selector in filter_selectors:
                try:
                    filter_elem = await page.query_selector(selector)
                    if filter_elem:
                        if await filter_elem.get_attribute('tagName') == 'SELECT':
                            await filter_elem.select_option(filter_value)
                        else:
                            await filter_elem.fill(filter_value)
                        return
                except:
                    continue
                    
        except Exception as e:
            print(f"Error applying filter {filter_name}: {str(e)}")
    
    def _normalize_job_data(self, job_data: Dict) -> Optional[Dict]:
        """Normalize job data from various sources"""
        try:
            # Common field mappings
            field_mappings = {
                'title': ['title', 'name', 'position', 'job_title', 'position_title'],
                'description': ['description', 'desc', 'summary', 'details', 'content'],
                'location': ['location', 'city', 'place', 'address'],
                'company': ['company', 'employer', 'organization', 'firm'],
                'job_type': ['type', 'employment_type', 'job_type', 'work_type'],
                'salary': ['salary', 'compensation', 'pay', 'wage'],
                'requirements': ['requirements', 'qualifications', 'skills', 'experience'],
                'url': ['url', 'link', 'href', 'apply_url', 'job_url']
            }
            
            normalized_job = {}
            
            for target_field, source_fields in field_mappings.items():
                for source_field in source_fields:
                    if source_field in job_data:
                        value = job_data[source_field]
                        if value:
                            normalized_job[target_field] = value
                            break
            
            # Ensure we have at least a title
            if not normalized_job.get('title'):
                return None
            
            # Add extraction timestamp
            normalized_job['extracted_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            return normalized_job
            
        except Exception as e:
            print(f"Error normalizing job data: {str(e)}")
            return None
    
    def _extract_job_from_element_data(self, element_data: Dict) -> Optional[Dict]:
        """Extract job from element data"""
        try:
            # Look for job-related patterns in text
            text = element_data.get('text', '')
            
            # Simple pattern matching for job information
            job = {}
            
            # Extract title (look for patterns like "Senior Developer", "Software Engineer", etc.)
            title_patterns = [
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Developer|Engineer|Designer|Manager|Analyst|Specialist))',
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Position|Role|Job))',
                r'(Senior|Junior|Lead|Principal)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, text)
                if match:
                    job['title'] = match.group(1)
                    break
            
            if not job.get('title'):
                return None
            
            # Extract other information
            job['description'] = text[:500] + '...' if len(text) > 500 else text
            job['extracted_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            return job
            
        except Exception as e:
            print(f"Error extracting job from element data: {str(e)}")
            return None 