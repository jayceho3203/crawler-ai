# app/services/hidden_job_extractor_requests.py
"""
Requests-only hidden job extraction service for Render compatibility
"""

import re
import json
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import aiohttp

class HiddenJobExtractor:
    """Extract hidden jobs from career pages using HTML parsing (requests-only mode)"""
    
    def __init__(self):
        self.extracted_jobs = []
        self.visited_urls = set()
        
    async def extract_hidden_jobs_from_page(self, url: str, html_content: str) -> List[Dict]:
        """Extract hidden jobs using HTML content (requests-only mode)"""
        jobs = []
        
        try:
            # Technique 1: Extract from JavaScript data in HTML
            js_jobs = await self._extract_from_javascript_data_html(html_content)
            jobs.extend(js_jobs[:5])  # Giới hạn 5 jobs
            
            # Technique 2: Extract from hidden elements in HTML
            hidden_jobs = await self._extract_from_hidden_elements_html(html_content)
            jobs.extend(hidden_jobs[:5])  # Giới hạn 5 jobs
            
        except Exception as e:
            print(f"Error extracting hidden jobs: {str(e)}")
        
        return jobs
    
    async def _extract_from_javascript_data_html(self, html_content: str) -> List[Dict]:
        """Extract jobs from JavaScript data in HTML content"""
        jobs = []
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for job data in script tags
            scripts = soup.find_all('script')
            for script in scripts[:3]:  # Limit to first 3 scripts
                content = script.string or script.get_text()
                if content:
                    # Look for JSON patterns
                    patterns = [
                        r'jobs\s*:\s*(\[.*?\])',
                        r'careers\s*:\s*(\[.*?\])',
                        r'positions\s*:\s*(\[.*?\])',
                        r'openings\s*:\s*(\[.*?\])',
                        r'vacancies\s*:\s*(\[.*?\])'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                        for match in matches:
                            try:
                                job_data = json.loads(match)
                                if isinstance(job_data, list):
                                    for job in job_data[:5]:  # Limit to 5 jobs
                                        if isinstance(job, dict):
                                            normalized_job = self._normalize_job_data(job)
                                            if normalized_job:
                                                jobs.append(normalized_job)
                            except json.JSONDecodeError:
                                continue
            
        except Exception as e:
            print(f"Error extracting from JavaScript data: {str(e)}")
        
        return jobs
    
    async def _extract_from_hidden_elements_html(self, html_content: str) -> List[Dict]:
        """Extract jobs from hidden elements in HTML content"""
        jobs = []
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for hidden job elements
            hidden_selectors = [
                '[style*="display: none"]',
                '[style*="visibility: hidden"]',
                '.hidden',
                '.invisible',
                '[aria-hidden="true"]'
            ]
            
            for selector in hidden_selectors:
                elements = soup.select(selector)
                for element in elements[:3]:  # Limit to 3 elements per selector
                    job_data = self._extract_job_from_element_data({
                        'tag': element.name,
                        'text': element.get_text(strip=True),
                        'attributes': dict(element.attrs)
                    })
                    if job_data:
                        jobs.append(job_data)
            
            # Look for job data in data attributes
            data_elements = soup.find_all(attrs={'data-job': True})
            for element in data_elements[:5]:  # Limit to 5 elements
                try:
                    job_json = element.get('data-job')
                    if job_json:
                        job_data = json.loads(job_json)
                        if isinstance(job_data, dict):
                            normalized_job = self._normalize_job_data(job_data)
                            if normalized_job:
                                jobs.append(normalized_job)
                except (json.JSONDecodeError, AttributeError):
                    continue
            
        except Exception as e:
            print(f"Error extracting from hidden elements: {str(e)}")
        
        return jobs
    
    def _normalize_job_data(self, job_data: Dict) -> Optional[Dict]:
        """Normalize job data to standard format"""
        try:
            # Extract basic job information
            title = job_data.get('title', '') or job_data.get('name', '') or job_data.get('position', '')
            company = job_data.get('company', '') or job_data.get('employer', '')
            location = job_data.get('location', '') or job_data.get('city', '') or job_data.get('address', '')
            description = job_data.get('description', '') or job_data.get('summary', '') or job_data.get('details', '')
            url = job_data.get('url', '') or job_data.get('link', '') or job_data.get('apply_url', '')
            
            # Validate required fields
            if not title or len(title.strip()) < 3:
                return None
            
            # Normalize job type
            job_type = job_data.get('job_type', '') or job_data.get('type', '') or job_data.get('employment_type', '')
            if job_type:
                job_type = self._normalize_job_type(job_type)
            else:
                job_type = 'Full-time'
            
            # Normalize salary
            salary = job_data.get('salary', '') or job_data.get('compensation', '') or job_data.get('pay', '')
            
            # Normalize posted date
            posted_date = job_data.get('posted_date', '') or job_data.get('date', '') or job_data.get('created_at', '')
            
            # Normalize requirements
            requirements = job_data.get('requirements', '') or job_data.get('qualifications', '') or job_data.get('skills', '')
            
            # Normalize benefits
            benefits = job_data.get('benefits', '') or job_data.get('perks', '') or job_data.get('advantages', '')
            
            return {
                'title': title.strip(),
                'company': company.strip() if company else '',
                'location': location.strip() if location else '',
                'job_type': job_type,
                'salary': salary.strip() if salary else '',
                'posted_date': posted_date.strip() if posted_date else '',
                'url': url.strip() if url else '',
                'description': description.strip() if description else '',
                'requirements': requirements.strip() if requirements else '',
                'benefits': benefits.strip() if benefits else ''
            }
            
        except Exception as e:
            print(f"Error normalizing job data: {str(e)}")
            return None
    
    def _normalize_job_type(self, job_type: str) -> str:
        """Normalize job type to standard format"""
        job_type_lower = job_type.lower().strip()
        
        if any(word in job_type_lower for word in ['full-time', 'fulltime', 'full time', 'permanent']):
            return 'Full-time'
        elif any(word in job_type_lower for word in ['part-time', 'parttime', 'part time', 'casual']):
            return 'Part-time'
        elif any(word in job_type_lower for word in ['contract', 'temporary', 'temp', 'freelance']):
            return 'Contract'
        elif any(word in job_type_lower for word in ['internship', 'intern', 'student', 'graduate']):
            return 'Internship'
        else:
            return 'Full-time'
    
    def _extract_job_from_element_data(self, element_data: Dict) -> Optional[Dict]:
        """Extract job information from element data"""
        try:
            text = element_data.get('text', '')
            if not text or len(text) < 50:
                return None
            
            # Check if text contains job-related keywords
            job_keywords = [
                'job', 'career', 'position', 'opportunity', 'vacancy', 'opening',
                'tuyển dụng', 'việc làm', 'cơ hội', 'vị trí', 'công việc'
            ]
            
            text_lower = text.lower()
            if not any(keyword in text_lower for keyword in job_keywords):
                return None
            
            # Extract basic information using regex patterns
            title_pattern = r'(?:job|position|title|vị trí|công việc)[\s:]+([^\n\r]+)'
            company_pattern = r'(?:company|employer|công ty|doanh nghiệp)[\s:]+([^\n\r]+)'
            location_pattern = r'(?:location|city|address|địa điểm|thành phố)[\s:]+([^\n\r]+)'
            
            title_match = re.search(title_pattern, text, re.IGNORECASE)
            company_match = re.search(company_pattern, text, re.IGNORECASE)
            location_match = re.search(location_pattern, text, re.IGNORECASE)
            
            title = title_match.group(1).strip() if title_match else ''
            company = company_match.group(1).strip() if company_match else ''
            location = location_match.group(1).strip() if location_match else ''
            
            if not title:
                return None
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'job_type': 'Full-time',
                'salary': '',
                'posted_date': '',
                'url': '',
                'description': text[:500],  # First 500 characters
                'requirements': '',
                'benefits': ''
            }
            
        except Exception as e:
            print(f"Error extracting job from element data: {str(e)}")
            return None
