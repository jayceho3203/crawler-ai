# app/services/job_extraction_service.py
"""
Enhanced job extraction service
"""

import logging
import asyncio
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

from .crawler import crawl_single_url
from .hidden_job_extractor import HiddenJobExtractor
from .job_analyzer import JobAnalyzer
from .simple_job_formatter import SimpleJobFormatter
from .job_extractor import extract_jobs_from_page

logger = logging.getLogger(__name__)

class JobExtractionService:
    """Enhanced service for extracting jobs from career pages"""
    
    def __init__(self):
        self.hidden_job_extractor = HiddenJobExtractor()
        self.job_analyzer = JobAnalyzer()
        self.simple_formatter = SimpleJobFormatter()
        
        # Job type mappings
        self.job_type_mappings = {
            'full-time': ['full time', 'fulltime', 'toàn thời gian', 'chính thức'],
            'part-time': ['part time', 'parttime', 'bán thời gian', 'thời vụ'],
            'contract': ['contract', 'hợp đồng', 'temporary', 'tạm thời'],
            'internship': ['intern', 'internship', 'thực tập', 'trainee'],
            'remote': ['remote', 'work from home', 'làm việc từ xa', 'online'],
            'hybrid': ['hybrid', 'kết hợp', 'flexible', 'linh hoạt']
        }
        
        # Location patterns
        self.location_patterns = {
            'hanoi': ['hà nội', 'hanoi', 'hn', 'thăng long'],
            'ho_chi_minh': ['hồ chí minh', 'ho chi minh', 'hcm', 'tp.hcm', 'saigon'],
            'da_nang': ['đà nẵng', 'da nang', 'danang'],
            'can_tho': ['cần thơ', 'can tho', 'cantho'],
            'hai_phong': ['hải phòng', 'hai phong', 'haiphong']
        }
    
    async def extract_jobs(self, career_page_urls: List[str], max_jobs_per_page: int = 50,
                          include_hidden_jobs: bool = True, include_job_details: bool = True,
                          job_types_filter: Optional[List[str]] = None,
                          location_filter: Optional[List[str]] = None,
                          salary_range: Optional[Dict] = None,
                          posted_date_filter: Optional[str] = None) -> Dict:
        """
        Extract jobs from multiple career pages with advanced filtering
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🔍 Starting job extraction from {len(career_page_urls)} career pages")
            
            all_jobs = []
            page_results = []
            hidden_jobs_count = 0
            visible_jobs_count = 0
            
            # Process each career page
            for career_url in career_page_urls:
                try:
                    logger.info(f"   🔍 Processing career page: {career_url}")
                    
                    page_result = await self._extract_jobs_from_single_page(
                        career_url, max_jobs_per_page, include_hidden_jobs, include_job_details
                    )
                    
                    if page_result['success']:
                        page_jobs = page_result['jobs']
                        page_hidden_count = page_result['hidden_jobs_count']
                        page_visible_count = page_result['visible_jobs_count']
                        
                        # Apply filters
                        filtered_jobs = await self._apply_job_filters(
                            page_jobs, job_types_filter, location_filter, 
                            salary_range, posted_date_filter
                        )
                        
                        all_jobs.extend(filtered_jobs)
                        hidden_jobs_count += page_hidden_count
                        visible_jobs_count += page_visible_count
                        
                        page_results.append({
                            'url': career_url,
                            'success': True,
                            'total_jobs_found': len(page_jobs),
                            'filtered_jobs_count': len(filtered_jobs),
                            'hidden_jobs_count': page_hidden_count,
                            'visible_jobs_count': page_visible_count,
                            'jobs': filtered_jobs
                        })
                        
                        logger.info(f"   ✅ Found {len(filtered_jobs)} jobs (filtered from {len(page_jobs)})")
                    else:
                        page_results.append({
                            'url': career_url,
                            'success': False,
                            'error': page_result['error_message']
                        })
                        logger.warning(f"   ❌ Failed to extract jobs from {career_url}")
                        
                except Exception as e:
                    logger.error(f"   ❌ Error processing {career_url}: {e}")
                    page_results.append({
                        'url': career_url,
                        'success': False,
                        'error': str(e)
                    })
            
            # Analyze all jobs
            job_analysis = []
            for job in all_jobs:
                analysis = self.job_analyzer.analyze_job(job)
                job_analysis.append(analysis)
            
            # Format jobs for n8n
            formatted_jobs = self.simple_formatter.format_jobs_list(all_jobs)
            job_summary = self.simple_formatter.get_job_summary(all_jobs)
            
            crawl_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'requested_urls': career_page_urls,
                'crawl_time': crawl_time,
                'total_jobs_found': len(all_jobs),
                'jobs': all_jobs,
                'formatted_jobs': formatted_jobs,
                'job_summary': job_summary,
                'job_analysis': job_analysis,
                'page_results': page_results,
                'hidden_jobs_count': hidden_jobs_count,
                'visible_jobs_count': visible_jobs_count
            }
            
        except Exception as e:
            logger.error(f"Error in job extraction: {e}")
            return {
                'success': False,
                'error_message': str(e),
                'requested_urls': career_page_urls,
                'crawl_time': (datetime.now() - start_time).total_seconds()
            }
    
    async def _extract_jobs_from_single_page(self, career_url: str, max_jobs: int,
                                           include_hidden_jobs: bool, include_job_details: bool) -> Dict:
        """Extract jobs from a single career page"""
        try:
            # Step 1: Basic job extraction
            basic_result = extract_jobs_from_page(career_url, max_jobs)
            visible_jobs = basic_result.get('jobs', [])
            visible_jobs_count = len(visible_jobs)
            
            # Step 2: Hidden job extraction (if enabled)
            hidden_jobs = []
            hidden_jobs_count = 0
            
            if include_hidden_jobs:
                hidden_result = await self.hidden_job_extractor.extract_hidden_jobs_from_page(career_url)
                hidden_jobs = hidden_result.get('jobs', [])
                hidden_jobs_count = len(hidden_jobs)
            
            # Step 3: Combine and deduplicate jobs
            all_jobs = visible_jobs + hidden_jobs
            unique_jobs = self._deduplicate_jobs(all_jobs)
            
            # Step 4: Enhance job details (if enabled)
            if include_job_details:
                enhanced_jobs = []
                for job in unique_jobs:
                    enhanced_job = await self._enhance_job_details(job, career_url)
                    enhanced_jobs.append(enhanced_job)
                unique_jobs = enhanced_jobs
            
            return {
                'success': True,
                'jobs': unique_jobs,
                'visible_jobs_count': visible_jobs_count,
                'hidden_jobs_count': hidden_jobs_count,
                'total_jobs': len(unique_jobs)
            }
            
        except Exception as e:
            logger.error(f"Error extracting jobs from {career_url}: {e}")
            return {
                'success': False,
                'error_message': str(e),
                'jobs': [],
                'visible_jobs_count': 0,
                'hidden_jobs_count': 0,
                'total_jobs': 0
            }
    
    async def _apply_job_filters(self, jobs: List[Dict], job_types_filter: Optional[List[str]] = None,
                               location_filter: Optional[List[str]] = None,
                               salary_range: Optional[Dict] = None,
                               posted_date_filter: Optional[str] = None) -> List[Dict]:
        """Apply various filters to job list"""
        filtered_jobs = jobs.copy()
        
        # Filter by job type
        if job_types_filter:
            filtered_jobs = [job for job in filtered_jobs 
                           if self._matches_job_type(job, job_types_filter)]
        
        # Filter by location
        if location_filter:
            filtered_jobs = [job for job in filtered_jobs 
                           if self._matches_location(job, location_filter)]
        
        # Filter by salary range
        if salary_range:
            filtered_jobs = [job for job in filtered_jobs 
                           if self._matches_salary_range(job, salary_range)]
        
        # Filter by posted date
        if posted_date_filter:
            filtered_jobs = [job for job in filtered_jobs 
                           if self._matches_posted_date(job, posted_date_filter)]
        
        return filtered_jobs
    
    def _matches_job_type(self, job: Dict, job_types_filter: List[str]) -> bool:
        """Check if job matches the job type filter"""
        job_type = job.get('job_type', '').lower()
        job_title = job.get('title', '').lower()
        job_description = job.get('description', '').lower()
        
        for filter_type in job_types_filter:
            filter_type_lower = filter_type.lower()
            
            # Direct match
            if filter_type_lower in job_type:
                return True
            
            # Check in title
            if filter_type_lower in job_title:
                return True
            
            # Check in description
            if filter_type_lower in job_description:
                return True
            
            # Check mapped keywords
            if filter_type_lower in self.job_type_mappings:
                for keyword in self.job_type_mappings[filter_type_lower]:
                    if keyword in job_type or keyword in job_title or keyword in job_description:
                        return True
        
        return False
    
    def _matches_location(self, job: Dict, location_filter: List[str]) -> bool:
        """Check if job matches the location filter"""
        location = job.get('location', '').lower()
        
        for filter_location in location_filter:
            filter_location_lower = filter_location.lower()
            
            # Direct match
            if filter_location_lower in location:
                return True
            
            # Check mapped patterns
            if filter_location_lower in self.location_patterns:
                for pattern in self.location_patterns[filter_location_lower]:
                    if pattern in location:
                        return True
        
        return False
    
    def _matches_salary_range(self, job: Dict, salary_range: Dict) -> bool:
        """Check if job matches the salary range filter"""
        salary = job.get('salary', '')
        if not salary:
            return True  # Include jobs without salary info
        
        # Extract numeric values from salary string
        import re
        numbers = re.findall(r'\d+', salary.replace(',', ''))
        if not numbers:
            return True
        
        # Assume the first number is the salary value
        try:
            salary_value = int(numbers[0])
            min_salary = salary_range.get('min', 0)
            max_salary = salary_range.get('max', float('inf'))
            
            return min_salary <= salary_value <= max_salary
        except (ValueError, TypeError):
            return True
    
    def _matches_posted_date(self, job: Dict, posted_date_filter: str) -> bool:
        """Check if job matches the posted date filter"""
        posted_date = job.get('posted_date', '')
        if not posted_date:
            return True  # Include jobs without date info
        
        try:
            # Parse the posted date (assuming various formats)
            from datetime import datetime
            
            # Try different date formats
            date_formats = [
                '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y',
                '%Y/%m/%d', '%d.%m.%Y', '%Y.%m.%d'
            ]
            
            job_date = None
            for fmt in date_formats:
                try:
                    job_date = datetime.strptime(posted_date, fmt)
                    break
                except ValueError:
                    continue
            
            if not job_date:
                return True  # Include if we can't parse the date
            
            # Calculate the filter date
            now = datetime.now()
            if posted_date_filter == 'last_week':
                filter_date = now - timedelta(days=7)
            elif posted_date_filter == 'last_month':
                filter_date = now - timedelta(days=30)
            elif posted_date_filter == 'last_3_months':
                filter_date = now - timedelta(days=90)
            else:
                return True  # Include if filter is not recognized
            
            return job_date >= filter_date
            
        except Exception:
            return True  # Include if there's any error
    
    async def _enhance_job_details(self, job: Dict, career_url: str) -> Dict:
        """Enhance job details with additional information"""
        enhanced_job = job.copy()
        
        # Extract company name from career URL if not present
        if not enhanced_job.get('company'):
            parsed = urlparse(career_url)
            company_name = parsed.netloc.split('.')[0]
            enhanced_job['company'] = company_name.title()
        
        # Normalize job type
        enhanced_job['job_type'] = self._normalize_job_type(enhanced_job.get('job_type', ''))
        
        # Extract location from description if not present
        if not enhanced_job.get('location'):
            location = self._extract_location_from_description(enhanced_job.get('description', ''))
            if location:
                enhanced_job['location'] = location
        
        # Extract salary information
        if not enhanced_job.get('salary'):
            salary = self._extract_salary_from_description(enhanced_job.get('description', ''))
            if salary:
                enhanced_job['salary'] = salary
        
        return enhanced_job
    
    def _normalize_job_type(self, job_type: str) -> str:
        """Normalize job type to standard format"""
        job_type_lower = job_type.lower()
        
        for standard_type, keywords in self.job_type_mappings.items():
            for keyword in keywords:
                if keyword in job_type_lower:
                    return standard_type
        
        return job_type or 'Full-time'  # Default to full-time
    
    def _extract_location_from_description(self, description: str) -> Optional[str]:
        """Extract location from job description"""
        description_lower = description.lower()
        
        for location_name, patterns in self.location_patterns.items():
            for pattern in patterns:
                if pattern in description_lower:
                    return location_name.replace('_', ' ').title()
        
        return None
    
    def _extract_salary_from_description(self, description: str) -> Optional[str]:
        """Extract salary information from job description"""
        import re
        
        # Common salary patterns
        salary_patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|VND|đồng|dollar)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:triệu|million)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|K)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|VND)'
        ]
        
        for pattern in salary_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            if matches:
                return f"{matches[0]} VND"  # Default to VND
        
        return None
    
    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on title and company"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Create a unique key based on title and company
            title = job.get('title', '').lower().strip()
            company = job.get('company', '').lower().strip()
            key = f"{title}|{company}"
            
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    async def extract_jobs_scrapy(self, career_page_urls: List[str], max_jobs_per_page: int = 50,
                                include_hidden_jobs: bool = True, include_job_details: bool = True,
                                job_types_filter: Optional[List[str]] = None,
                                location_filter: Optional[List[str]] = None,
                                salary_range: Optional[Dict] = None,
                                posted_date_filter: Optional[str] = None) -> Dict:
        """
        Extract jobs using optimized Scrapy spider
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🚀 Starting Scrapy job extraction from {len(career_page_urls)} career pages")
            
            # For now, use regular extraction but mark as Scrapy
            # TODO: Implement actual Scrapy job spider
            result = await self.extract_jobs(
                career_page_urls=career_page_urls,
                max_jobs_per_page=max_jobs_per_page,
                include_hidden_jobs=include_hidden_jobs,
                include_job_details=include_job_details,
                job_types_filter=job_types_filter,
                location_filter=location_filter,
                salary_range=salary_range,
                posted_date_filter=posted_date_filter
            )
            
            # Mark as Scrapy method
            result['crawl_method'] = 'scrapy_optimized'
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in Scrapy job extraction: {e}")
            return {
                'success': False,
                'requested_urls': career_page_urls,
                'error_message': str(e),
                'jobs': [],
                'total_jobs_found': 0,
                'crawl_time': (datetime.now() - start_time).total_seconds(),
                'crawl_method': 'scrapy_optimized'
            }
    
    async def extract_job_urls_only(self, career_page_url: str, max_jobs: int = 50) -> Dict:
        """
        Extract only job URLs from a career page (no details)
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🔗 Extracting job URLs from: {career_page_url}")
            
            # Use existing job extraction but only get URLs
            result = await self._extract_jobs_from_single_page(
                career_page_url, max_jobs, include_hidden_jobs=True, include_job_details=False
            )
            
            if result['success']:
                # Extract only URLs from jobs
                job_urls = []
                for job in result.get('jobs', []):
                    if job.get('url'):
                        job_urls.append(job['url'])
                
                crawl_time = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"✅ Found {len(job_urls)} job URLs from {career_page_url}")
                
                return {
                    'success': True,
                    'career_page_url': career_page_url,
                    'job_urls': job_urls,
                    'total_job_urls_found': len(job_urls),
                    'crawl_time': crawl_time,
                    'crawl_method': 'scrapy_optimized'
                }
            else:
                return {
                    'success': False,
                    'career_page_url': career_page_url,
                    'error_message': result.get('error_message', 'Failed to extract job URLs'),
                    'job_urls': [],
                    'total_job_urls_found': 0,
                    'crawl_time': (datetime.now() - start_time).total_seconds(),
                    'crawl_method': 'scrapy_optimized'
                }
                
        except Exception as e:
            logger.error(f"❌ Error extracting job URLs: {e}")
            return {
                'success': False,
                'career_page_url': career_page_url,
                'error_message': str(e),
                'job_urls': [],
                'total_job_urls_found': 0,
                'crawl_time': (datetime.now() - start_time).total_seconds(),
                'crawl_method': 'scrapy_optimized'
            }
    
    async def extract_job_details_only(self, job_url: str) -> Dict:
        """
        Extract detailed job information from a single job URL
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"📄 Extracting job details from: {job_url}")
            
            # Crawl the job page
            result = await crawl_single_url(job_url)
            
            if not result['success']:
                return {
                    'success': False,
                    'job_url': job_url,
                    'error_message': 'Failed to crawl job page',
                    'job_details': {},
                    'crawl_time': (datetime.now() - start_time).total_seconds(),
                    'crawl_method': 'scrapy_optimized'
                }
            
            # Extract job details from HTML
            job_details = await self._extract_job_details_from_html(result, job_url)
            
            crawl_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Extracted job details from {job_url}")
            
            return {
                'success': True,
                'job_url': job_url,
                'job_details': job_details,
                'crawl_time': crawl_time,
                'crawl_method': 'scrapy_optimized'
            }
            
        except Exception as e:
            logger.error(f"❌ Error extracting job details: {e}")
            return {
                'success': False,
                'job_url': job_url,
                'error_message': str(e),
                'job_details': {},
                'crawl_time': (datetime.now() - start_time).total_seconds(),
                'crawl_method': 'scrapy_optimized'
            }
    
    async def _extract_job_details_from_html(self, result: Dict, job_url: str) -> Dict:
        """Extract job details from HTML content"""
        try:
            from bs4 import BeautifulSoup
            
            html_content = result.get('html', '')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            job_details = {
                'title': '',
                'company': '',
                'location': '',
                'job_type': 'Full-time',
                'salary': '',
                'posted_date': '',
                'url': job_url,
                'description': '',
                'requirements': '',
                'benefits': ''
            }
            
            # Extract title
            title_selectors = ['h1', '.job-title', '.position-title', '.title']
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    job_details['title'] = title_element.get_text().strip()
                    break
            
            # Extract description
            desc_selectors = ['.job-description', '.description', '.content', 'p']
            for selector in desc_selectors:
                desc_element = soup.select_one(selector)
                if desc_element:
                    job_details['description'] = desc_element.get_text().strip()[:2000]
                    break
            
            # Extract company name from URL if not found
            if not job_details['company']:
                parsed = urlparse(job_url)
                company_name = parsed.netloc.split('.')[0]
                job_details['company'] = company_name.title()
            
            # Extract location from description
            if not job_details['location']:
                location = self._extract_location_from_description(job_details['description'])
                if location:
                    job_details['location'] = location
            
            # Extract salary from description
            if not job_details['salary']:
                salary = self._extract_salary_from_description(job_details['description'])
                if salary:
                    job_details['salary'] = salary
            
            return job_details
            
        except Exception as e:
            logger.error(f"Error extracting job details from HTML: {e}")
            return {
                'title': '',
                'company': '',
                'location': '',
                'job_type': 'Full-time',
                'salary': '',
                'posted_date': '',
                'url': job_url,
                'description': '',
                'requirements': '',
                'benefits': ''
            }