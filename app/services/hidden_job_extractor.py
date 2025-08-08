# app/services/hidden_job_extractor.py
"""
Optimized hidden job extraction service for job details
"""

import re
import json
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.async_api import Page

class HiddenJobExtractor:
    """Extract hidden jobs from career pages using optimized techniques"""
    
    def __init__(self):
        self.extracted_jobs = []
        self.visited_urls = set()
        
    async def extract_hidden_jobs_from_page(self, url: str, page: Page) -> List[Dict]:
        """Extract hidden jobs using optimized techniques"""
        jobs = []
        
        try:
            # Technique 1: Wait for dynamic content to load
            await self._wait_for_dynamic_content(page)
            
            # Technique 2: Extract from JavaScript data
            js_jobs = await self._extract_from_javascript_data(page)
            jobs.extend(js_jobs[:5])  # Giới hạn 5 jobs
            
            # Technique 3: Extract from hidden elements
            hidden_jobs = await self._extract_from_hidden_elements(page)
            jobs.extend(hidden_jobs[:5])  # Giới hạn 5 jobs
            
        except Exception as e:
            print(f"Error extracting hidden jobs: {str(e)}")
        
        return jobs
    
    async def _wait_for_dynamic_content(self, page: Page):
        """Wait for dynamic content to load"""
        try:
            # Wait for common job loading indicators
            selectors = [
                '.job-list', '.career-list', '.position-list',
                '.job-item', '.career-item', '.position-item'
            ]
            
            for selector in selectors[:2]:  # Chỉ dùng 2 selectors đầu
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    break
                except:
                    continue
            
            # Wait for network idle
            await page.wait_for_load_state('networkidle', timeout=5000)
            
            # Additional wait for JavaScript execution
            await page.wait_for_timeout(1000)
            
        except Exception as e:
            print(f"Error waiting for dynamic content: {str(e)}")
    
    async def _extract_from_javascript_data(self, page: Page) -> List[Dict]:
        """Extract jobs from JavaScript data"""
        jobs = []
        
        try:
            # Extract job data from JavaScript variables and scripts
            script_content = await page.evaluate("""
                () => {
                    const jobData = [];
                    
                    // Look for job data in global variables
                    const globalVars = ['jobs', 'careers', 'positions', 'openings', 'vacancies'];
                    for (const varName of globalVars) {
                        if (window[varName] && Array.isArray(window[varName])) {
                            jobData.push(...window[varName].slice(0, 5));
                        }
                    }
                    
                    // Look for job data in script tags
                    const scripts = document.querySelectorAll('script');
                    for (const script of scripts.slice(0, 3)) {
                        const content = script.textContent || script.innerHTML;
                        if (content) {
                            // Look for JSON patterns
                            const patterns = [
                                /jobs\\s*:\\s*(\\[.*?\\])/gi,
                                /careers\\s*:\\s*(\\[.*?\\])/gi,
                                /positions\\s*:\\s*(\\[.*?\\])/gi
                            ];
                            
                            for (const pattern of patterns) {
                                const matches = content.match(pattern);
                                if (matches) {
                                    try {
                                        const data = JSON.parse(matches[1]);
                                        if (Array.isArray(data)) {
                                            jobData.push(...data.slice(0, 5));
                                        }
                                    } catch (e) {
                                        // Skip invalid JSON
                                    }
                                }
                            }
                        }
                    }
                    
                    return jobData.slice(0, 10);
                }
            """)
            
            # Process extracted job data
            for job_data in script_content[:5]:
                if isinstance(job_data, dict):
                    job = self._normalize_job_data(job_data)
                    if job:
                        jobs.append(job)
                        
        except Exception as e:
            print(f"Error extracting from JavaScript data: {str(e)}")
        
        return jobs
    
    async def _extract_from_hidden_elements(self, page: Page) -> List[Dict]:
        """Extract jobs from hidden elements"""
        jobs = []
        
        try:
            # Find hidden elements with job-related content
            hidden_elements = await page.evaluate("""
                () => {
                    const hiddenElements = [];
                    const selectors = [
                        '[style*="display: none"]',
                        '[style*="visibility: hidden"]',
                        '.hidden', '.invisible', '.collapsed',
                        '[aria-hidden="true"]', '[hidden]'
                    ];
                    
                    for (const selector of selectors.slice(0, 3)) {
                        const elements = document.querySelectorAll(selector);
                        for (const element of elements.slice(0, 5)) {
                            const text = element.textContent || element.innerText || '';
                            if (text.length > 50 && (
                                text.toLowerCase().includes('job') ||
                                text.toLowerCase().includes('career') ||
                                text.toLowerCase().includes('position') ||
                                text.toLowerCase().includes('tuyển') ||
                                text.toLowerCase().includes('việc')
                            )) {
                                hiddenElements.push({
                                    tagName: element.tagName,
                                    className: element.className,
                                    id: element.id,
                                    text: text.substring(0, 300),
                                    html: element.innerHTML.substring(0, 500)
                                });
                            }
                        }
                    }
                    
                    return hiddenElements.slice(0, 5);
                }
            """)
            
            # Process hidden elements
            for element in hidden_elements[:3]:
                job = self._extract_job_from_element_data(element)
                if job:
                    jobs.append(job)
                    
        except Exception as e:
            print(f"Error extracting from hidden elements: {str(e)}")
        
        return jobs
    
    def _normalize_job_data(self, job_data: Dict) -> Optional[Dict]:
        """Normalize job data to standard format"""
        try:
            if not isinstance(job_data, dict):
                return None
            
            # Extract essential fields
            title = job_data.get('title') or job_data.get('name') or job_data.get('position')
            if not title:
                return None
            
            job = {
                'title': str(title).strip(),
                'company': job_data.get('company', ''),
                'location': job_data.get('location', ''),
                'description': job_data.get('description', ''),
                'job_type': job_data.get('type', ''),
                'salary': job_data.get('salary', ''),
                'requirements': job_data.get('requirements', []),
                'url': job_data.get('url', ''),
                'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'hidden'
            }
            
            # Clean up requirements
            if isinstance(job['requirements'], str):
                job['requirements'] = [req.strip() for req in job['requirements'].split('\n') if req.strip()]
            elif not isinstance(job['requirements'], list):
                job['requirements'] = []
            
            return job
            
        except Exception as e:
            print(f"Error normalizing job data: {str(e)}")
            return None
    
    def _extract_job_from_element_data(self, element_data: Dict) -> Optional[Dict]:
        """Extract job from element data"""
        try:
            text = element_data.get('text', '')
            if not text or len(text) < 10:
                return None
            
            # Extract title from text
            title = None
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line and len(line) > 3 and len(line) < 100:
                    title = line
                    break
            
            if not title:
                return None
            
            job = {
                'title': title,
                'company': '',
                'location': '',
                'description': text[:500] + '...' if len(text) > 500 else text,
                'job_type': '',
                'salary': '',
                'requirements': [],
                'url': '',
                'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'hidden'
            }
            
            return job
            
        except Exception as e:
            print(f"Error extracting job from element data: {str(e)}")
            return None 