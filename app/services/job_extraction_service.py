# app/services/job_extraction_service.py
"""
Enhanced job extraction service with conditional Playwright support
"""

import re
import json
import logging
import time
import os
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import aiohttp

# Conditional import based on environment variable
USE_PLAYWRIGHT = os.getenv("USE_PLAYWRIGHT", "0").lower() in ("1", "true", "yes")

# Always use requests-only extractor for Render compatibility
from .hidden_job_extractor_requests import HiddenJobExtractor

from .job_analyzer import JobAnalyzer
from .simple_job_formatter import SimpleJobFormatter
from .job_extractor import extract_jobs_from_page

logger = logging.getLogger(__name__)

class JobExtractionService:
    """Enhanced service for extracting job information from career pages"""
    
    def __init__(self):
        self.extractor = HiddenJobExtractor()
        self.job_analyzer = JobAnalyzer()
        self.simple_formatter = SimpleJobFormatter()
        
        # Log which extractor is being used
        if USE_PLAYWRIGHT:
            logger.info("🚀 Using Playwright-based job extractor")
        else:
            logger.info("📡 Using requests-based job extractor (Render compatible)")
        
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
        start_time = time.time() # Changed from datetime.now() to time.time()
        
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
                    import traceback
                    logger.exception(f"   ❌ Error processing {career_url}")  # tự động in traceback
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
            
            crawl_time = (time.time() - start_time) # Changed from datetime.now() to time.time()
            
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
            import traceback
            logger.exception("Error in job extraction")  # tự động in traceback
            return {
                'success': False,
                'error_message': str(e),
                'requested_urls': career_page_urls,
                'crawl_time': (time.time() - start_time) # Changed from datetime.now() to time.time()
            }
    
    async def _extract_jobs_from_single_page(self, career_url: str, max_jobs: int,
                                           include_hidden_jobs: bool, include_job_details: bool) -> Dict:
        """Extract jobs from a single career page with pagination support"""
        try:
            # Step 1: Get all job URLs including pagination
            all_job_urls = await self._get_all_job_urls_with_pagination(career_url, max_jobs)
            logger.info(f"   🔍 Found {len(all_job_urls)} total job URLs across all pages")
            
            # Step 2: Extract job details from each URL
            all_jobs = []
            for job_url in all_job_urls:
                try:
                    job_detail = await self._extract_single_job_detail(job_url)
                    if job_detail:
                        all_jobs.append(job_detail)
                except Exception as e:
                    logger.warning(f"   ⚠️ Failed to extract job from {job_url}: {e}")
            
            visible_jobs_count = len(all_jobs)
            hidden_jobs_count = 0  # Hidden jobs are now included in the main extraction
            
            # Step 3: Deduplicate jobs
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
    
    async def _detect_pagination_urls(self, career_url: str) -> List[str]:
        """Detect pagination URLs from career page"""
        pagination_urls = []
        
        try:
            # Common pagination patterns
            pagination_patterns = [
                '?paged=', '?page=', '?p=', '?pg=',
                '/page/', '/p/', '/pg/',
                '&paged=', '&page=', '&p=', '&pg='
            ]
            
            # Get the base URL and current page number
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            
            parsed = urlparse(career_url)
            query_params = parse_qs(parsed.query)
            
            # Check if current URL has pagination
            current_page = 1
            for pattern in pagination_patterns:
                param_name = pattern.replace('?', '').replace('&', '').replace('=', '')
                if param_name in query_params:
                    try:
                        current_page = int(query_params[param_name][0])
                        break
                    except (ValueError, IndexError):
                        pass
            
            # Generate pagination URLs (try pages 2-10)
            for page_num in range(2, 11):
                # Try different pagination patterns
                for pattern in pagination_patterns:
                    param_name = pattern.replace('?', '').replace('&', '').replace('=', '')
                    
                    # Create new query params
                    new_query_params = query_params.copy()
                    new_query_params[param_name] = [str(page_num)]
                    
                    # Build new URL
                    new_query = urlencode(new_query_params, doseq=True)
                    new_url = urlunparse((
                        parsed.scheme, parsed.netloc, parsed.path,
                        parsed.params, new_query, parsed.fragment
                    ))
                    
                    pagination_urls.append(new_url)
                    break  # Use first pattern that works
            
            logger.info(f"   📄 Generated {len(pagination_urls)} pagination URLs")
            return pagination_urls
            
        except Exception as e:
            logger.warning(f"   ⚠️ Pagination detection failed: {e}")
            return []
    
    async def _get_all_job_urls_with_pagination(self, career_url: str, max_jobs: int) -> List[str]:
        """Get all job URLs from career page including pagination"""
        all_job_urls = []
        visited_urls = set()
        
        try:
            # Start with the main career page
            urls_to_crawl = [career_url]
            
            while urls_to_crawl and len(all_job_urls) < max_jobs:
                current_url = urls_to_crawl.pop(0)
                
                if current_url in visited_urls:
                    continue
                    
                visited_urls.add(current_url)
                logger.info(f"   🔍 Crawling: {current_url}")
                
                # Extract job URLs from current page
                try:
                    result = await extract_jobs_from_page(current_url, max_jobs)
                    page_job_urls = result.get('job_urls', [])
                    
                    # Add job URLs (filter out pagination URLs)
                    for job_url in page_job_urls:
                        if self._is_job_url(job_url) and job_url not in all_job_urls:
                            all_job_urls.append(job_url)
                    
                    # Add pagination URLs to crawl queue
                    for url in page_job_urls:
                        if self._is_pagination_url(url) and url not in visited_urls:
                            urls_to_crawl.append(url)
                            
                except Exception as e:
                    logger.warning(f"   ⚠️ Failed to crawl {current_url}: {e}")
            
            logger.info(f"   📄 Total job URLs found: {len(all_job_urls)}")
            return all_job_urls
            
        except Exception as e:
            logger.error(f"   ❌ Error in pagination crawl: {e}")
            return all_job_urls
    
    def _is_job_url(self, url: str) -> bool:
        """Check if URL is a job detail page"""
        job_indicators = ['/career/', '/job/', '/position/', '/vacancy/']
        return any(indicator in url.lower() for indicator in job_indicators)
    
    def _is_pagination_url(self, url: str) -> bool:
        """Check if URL is a pagination page"""
        pagination_indicators = ['?paged=', '?page=', '?p=', '/page/']
        return any(indicator in url.lower() for indicator in pagination_indicators)
    
    async def _extract_single_job_detail(self, job_url: str) -> Optional[Dict]:
        """Extract details from a single job URL"""
        try:
            # Use the existing job detail extraction logic
            from .job_extractor import extract_job_details_from_url
            return await extract_job_details_from_url(job_url)
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to extract job details from {job_url}: {e}")
            return None
    
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
                filter_date = now - datetime.timedelta(days=7)
            elif posted_date_filter == 'last_month':
                filter_date = now - datetime.timedelta(days=30)
            elif posted_date_filter == 'last_3_months':
                filter_date = now - datetime.timedelta(days=90)
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
        
        # Enhanced salary patterns for Vietnamese job postings
        salary_patterns = [
            r'lương\s*up\s*to[:\s]*([^,\n]+)',
            r'lương[:\s]*([^,\n]+)',
            r'salary[:\s]*([^,\n]+)',
            r'up\s*to[:\s]*([^,\n]+)',
            r'(\d+[kKmM])',
            r'(\$\d+[kKmM]?)',
            r'(\d+\s*[tT]r[iỉ][eệ][uú])',
            r'(\d+\s*[mM]illion)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|VND|đồng|dollar)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:triệu|million)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|K)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|VND)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                salary = match.group(1).strip()
                # Clean up the salary text
                if salary and len(salary) > 0:
                    return salary
        
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
        start_time = time.time() # Changed from datetime.now() to time.time()
        
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
                'crawl_time': (time.time() - start_time), # Changed from datetime.now() to time.time()
                'crawl_method': 'scrapy_optimized'
            }
    
    async def extract_job_urls_only(self, career_page_url: str, max_jobs: int = 50, include_job_data: bool = False) -> Dict:
        """
        Extract job URLs from career page - simplified output for N8N workflow
        """
        start_time = time.time() # Changed from datetime.now() to time.time()
        
        try:
            logger.info(f"🔗 Extracting job URLs from: {career_page_url}")
            
            # Step 1: Try to extract job URLs directly from career page (PRIORITY)
            logger.info(f"   🔍 Step 1: Extracting job URLs directly from career page")
            job_urls = await self._extract_job_urls_from_career_page(career_page_url)
            
            if job_urls:
                # Found job URLs - this is the preferred approach
                has_individual_urls = True
                total_jobs_found = len(job_urls)
                logger.info(f"   ✅ Found {len(job_urls)} job URLs - using individual job pages")
                
                crawl_time = (time.time() - start_time) # Changed from datetime.now() to time.time()
                
                logger.info(f"✅ Job URL extraction completed:")
                logger.info(f"   📊 Total jobs found: {total_jobs_found}")
                logger.info(f"   📊 Has individual URLs: {has_individual_urls}")
                logger.info(f"   📊 Job URLs found: {len(job_urls)}")
                
                # Simplified response format for N8N workflow
                response = {
                    'success': True,
                    'career_page_url': career_page_url,
                    'total_jobs_found': total_jobs_found,
                    'has_individual_urls': has_individual_urls,
                    'job_urls': job_urls,
                    'crawl_time': crawl_time,
                    'crawl_method': 'scrapy_optimized'
                }
                
                return response
            else:
                # No job URLs found, fallback to extracting jobs from career page
                logger.info(f"   ⚠️ No job URLs found, falling back to career page extraction")
                result = await self._extract_jobs_from_single_page(
                    career_page_url, max_jobs, include_hidden_jobs=True, include_job_details=False
                )
                
                if result['success']:
                    jobs = result.get('jobs', [])
                    
                    # Analyze job structure
                    analysis = self._analyze_job_structure(jobs, career_page_url)
                    
                    # Determine if jobs have individual URLs
                    has_individual_urls = analysis['has_individual_urls']
                    job_urls = analysis['job_urls']
                    total_jobs_found = len(jobs)
                else:
                    has_individual_urls = False
                    job_urls = []
                    total_jobs_found = 0
                
                # Step 4: If no jobs found, try alternative methods
                if total_jobs_found == 0:
                    logger.info(f"   📊 No jobs found, trying alternative methods")
                    alternative_result = await self._try_alternative_extraction_methods(career_page_url, max_jobs)
                    
                    if alternative_result['success']:
                        jobs = alternative_result['jobs']
                        has_individual_urls = alternative_result['has_individual_urls']
                        job_urls = alternative_result.get('job_urls', [])
                        total_jobs_found = len(jobs)
                        logger.info(f"   📊 Alternative method successful: {alternative_result['extraction_type']}")
                    else:
                        logger.warning(f"   📊 No jobs found with any method")
                
                crawl_time = (time.time() - start_time) # Changed from datetime.now() to time.time()
                
                logger.info(f"✅ Job URL extraction completed:")
                logger.info(f"   📊 Total jobs found: {total_jobs_found}")
                logger.info(f"   📊 Has individual URLs: {has_individual_urls}")
                logger.info(f"   📊 Job URLs found: {len(job_urls)}")
                
                # Simplified response format for N8N workflow
                response = {
                    'success': True,
                    'career_page_url': career_page_url,
                    'total_jobs_found': total_jobs_found,
                    'has_individual_urls': has_individual_urls,
                    'crawl_time': crawl_time,
                    'crawl_method': 'scrapy_optimized'
                }
                
                # Always include job_urls for N8N workflow
                if has_individual_urls and job_urls:
                    # Jobs have individual URLs
                    response['job_urls'] = job_urls
                else:
                    # Jobs don't have individual URLs, return empty array instead of career page URL
                    response['job_urls'] = []
                    logger.warning(f"   ⚠️ No individual job URLs found, returning empty array")
                
                return response
                
        except Exception as e:
            logger.error(f"❌ Error in job URL extraction: {e}")
            return {
                'success': False,
                'career_page_url': career_page_url,
                'error_message': str(e),
                'total_jobs_found': 0,
                'has_individual_urls': False,
                'crawl_time': (time.time() - start_time), # Changed from datetime.now() to time.time()
                'crawl_method': 'scrapy_optimized'
            }
    
    async def extract_job_details_only(self, job_url: str) -> Dict:
        """
        Extract detailed job information from a single job URL
        """
        start_time = time.time() # Changed from datetime.now() to time.time()
        
        try:
            logger.info(f"📄 Extracting job details from: {job_url}")
            
            # Check if the URL is actually a career page (not a specific job page)
            is_career_page = self._is_career_page_url(job_url)
            
            if is_career_page:
                logger.info(f"   ⚠️ URL appears to be a career page, extracting jobs from career page")
                # Extract jobs from career page instead
                result = await self._extract_jobs_from_single_page(
                    job_url, max_jobs=10, include_hidden_jobs=True, include_job_details=True
                )
                
                if result['success'] and result.get('jobs'):
                    # Take the first job as the main job
                    first_job = result['jobs'][0]
                    job_details = {
                        'job_name': first_job.get('title', ''),
                        'job_type': first_job.get('job_type', 'Full-time'),
                        'job_role': first_job.get('title', ''),
                        'job_description': first_job.get('description', ''),
                        'job_link': job_url
                    }
                else:
                    # No jobs found, return empty details
                    job_details = {
                        'job_name': '',
                        'job_type': 'Full-time',
                        'job_role': '',
                        'job_description': '',
                        'job_link': job_url
                    }
            else:
                # Normal job detail page extraction
                from .crawler import crawl_single_url
                result = await crawl_single_url(job_url)
                
                if not result['success']:
                    return {
                        'success': False,
                        'job_url': job_url,
                        'error_message': 'Failed to crawl job page',
                        'job_details': {},
                        'crawl_time': (time.time() - start_time), # Changed from datetime.now() to time.time()
                        'crawl_method': 'scrapy_optimized'
                    }
                
                # Extract job details from HTML
                job_details = self._extract_job_details_from_html(result, job_url)
            
            crawl_time = (time.time() - start_time) # Changed from datetime.now() to time.time()
            
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
                'crawl_time': (time.time() - start_time), # Changed from datetime.now() to time.time()
                'crawl_method': 'scrapy_optimized'
            }
    
    def _is_career_page_url(self, url: str) -> bool:
        """Check if URL is a career page (not a specific job page)"""
        url_lower = url.lower()
        
        # Career page indicators
        career_indicators = [
            '/career', '/careers', '/jobs', '/positions', '/tuyen-dung',
            '/recruitment', '/vacancies', '/openings', '/opportunities'
        ]
        
        # Check if URL ends with career page patterns
        for indicator in career_indicators:
            if url_lower.endswith(indicator) or url_lower.endswith(indicator + '/'):
                return True
        
        # Check if URL contains career page patterns without job-specific keywords
        for indicator in career_indicators:
            if indicator in url_lower:
                # If it's just the career page without specific job info
                if not any(keyword in url_lower for keyword in ['developer', 'engineer', 'designer', 'manager', 'analyst', 'senior', 'junior']):
                    return True
        
        return False
    
    def _extract_job_details_from_html(self, result: Dict, job_url: str) -> Dict:
        """Extract job details from HTML content"""
        try:
            from bs4 import BeautifulSoup
            from urllib.parse import urlparse
            
            html_content = result.get('html', '')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            job_details = {
                'job_name': '',        # Job Name (thay vì title)
                'job_type': 'Full-time', # Job Type
                'job_role': '',        # Job Role
                'job_description': '', # Job Description (thay vì description)
                'job_link': job_url    # Job Link (thay vì url)
            }
            
            # Enhanced title extraction for Cole.vn and similar sites
            title_selectors = [
                'h1', 'h2', 'h3', '.job-title', '.position-title', '.title',
                '.career-title', '.vacancy-title', '.opening-title',
                '[data-job-title]', '[data-position-title]',
                '.entry-title', '.post-title', '.page-title',
                'h1.entry-title', 'h1.post-title', 'h1.page-title'
            ]
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    title_text = title_element.get_text().strip()
                    if title_text and len(title_text) > 3:
                        job_details['job_name'] = title_text
                        job_details['job_role'] = title_text  # Set job_role same as job_name
                        logger.info(f"   📄 Found job title: {title_text}")
                        break
            
            # Enhanced description extraction for Cole.vn and similar sites
            desc_selectors = [
                '.job-description', '.description', '.content', '.job-content',
                '.position-description', '.career-description', '.vacancy-description',
                'article', '.main-content', '.job-details', '.position-details',
                '.entry-content', '.post-content', '.page-content',
                '.job-body', '.position-body', '.career-body',
                '.job-info', '.position-info', '.career-info',
                # CO-WELL specific selectors
                '.job-detail', '.position-detail', '.career-detail',
                '.job-requirements', '.position-requirements', '.career-requirements',
                '.job-benefits', '.position-benefits', '.career-benefits',
                '.job-responsibilities', '.position-responsibilities', '.career-responsibilities',
                # Generic content selectors
                '.content-area', '.main', '#main', '.container', '.wrapper',
                '.text-content', '.body-content', '.page-body'
            ]
            for selector in desc_selectors:
                desc_element = soup.select_one(selector)
                if desc_element:
                    desc_text = desc_element.get_text().strip()
                    if desc_text and len(desc_text) > 50:
                        job_details['job_description'] = desc_text[:2000]
                        logger.info(f"   📄 Found job description with selector '{selector}' (length: {len(desc_text)})")
                        break
                    else:
                        logger.info(f"   🔍 Found element with selector '{selector}' but text too short: {len(desc_text)} chars")
                else:
                    logger.debug(f"   🔍 Selector '{selector}' not found")
            
            # Company info is already in Wehappi company details, so we skip it here
            
            # Set job_role same as job_name for Wehappi
            if job_details['job_name']:
                job_details['job_role'] = job_details['job_name']
            
            # Debug logging for Wehappi fields
            logger.info(f"🔍 Job extraction debug (Wehappi fields):")
            logger.info(f"   📄 Job Name (title): {bool(job_details['job_name'])}")
            logger.info(f"   📄 Job Type: {bool(job_details['job_type'])}")
            logger.info(f"   📄 Job Role: {bool(job_details['job_role'])}")
            logger.info(f"   📄 Job Description: {bool(job_details['job_description'])}")
            logger.info(f"   📄 Job Link (url): {bool(job_details['job_link'])}")
            
            # Debug HTML content
            html_content = result.get('html', '')
            logger.info(f"   📄 HTML content length: {len(html_content)}")
            if html_content:
                logger.info(f"   📄 HTML preview: {html_content[:500]}...")
            else:
                logger.warning(f"   ⚠️ No HTML content found!")
            
            # If no job details found, try alternative extraction
            if not job_details['job_name'] and not job_details['job_description']:
                logger.info(f"   🔄 No job details found, trying alternative extraction")
                alternative_job = self._extract_job_alternative_methods(soup, job_url)
                if alternative_job:
                    job_details.update(alternative_job)
            
            # If still no job details, try extracting from main content area
            if not job_details['job_name'] and not job_details['job_description']:
                logger.info(f"   🔄 Trying main content extraction")
                main_content_job = self._extract_job_from_main_content(soup, job_url)
                if main_content_job:
                    job_details.update(main_content_job)
            
            return job_details
            
        except Exception as e:
            logger.error(f"Error extracting job details from HTML: {e}")
            return {
                'job_name': '',
                'company': '',
                'location': '',
                'job_type': 'Full-time',
                'salary': '',
                'posted_date': '',
                'job_link': job_url,
                'job_description': '',
                'requirements': '',
                'benefits': ''
            }
    
    def _extract_job_from_main_content(self, soup, job_url: str) -> Dict:
        """Extract job details from main content area when standard selectors fail"""
        try:
            job_details = {}
            
            # Try to find main content area
            main_content_selectors = [
                'main', '.main', '#main', '.content', '#content',
                '.container', '.wrapper', '.page-content', '.post-content'
            ]
            
            main_content = None
            for selector in main_content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                # If no main content found, use body
                main_content = soup.find('body')
            
            if main_content:
                # Extract all text from main content
                content_text = main_content.get_text(separator=' ', strip=True)
                
                # Find job title from URL or content
                job_title = self._extract_job_title_from_url_or_content(job_url, content_text)
                if job_title:
                    job_details['job_name'] = job_title
                    job_details['job_role'] = job_title
                
                # Extract job description from content
                job_description = self._extract_job_description_from_content(content_text)
                if job_description:
                    job_details['job_description'] = job_description
                
                logger.info(f"   📄 Main content extraction: title={bool(job_details.get('job_name'))}, desc={bool(job_details.get('job_description'))}")
            
            return job_details
            
        except Exception as e:
            logger.error(f"Error in main content extraction: {e}")
            return {}
    
    def _extract_job_title_from_url_or_content(self, job_url: str, content_text: str) -> str:
        """Extract job title from URL or content"""
        try:
            # Try to extract from URL first
            from urllib.parse import urlparse, unquote
            parsed = urlparse(job_url)
            path = unquote(parsed.path)
            
            # Extract title from URL path
            if '/tuyen-dung/' in path:
                # For Cole.vn format: /tuyen-dung/hn---tro-giang-python-for-data-analysis
                title_part = path.split('/tuyen-dung/')[-1]
                if title_part:
                    # Clean up the title
                    title = title_part.replace('-', ' ').replace('_', ' ')
                    # Capitalize words
                    title = ' '.join(word.capitalize() for word in title.split())
                    return title
            
            # If no title from URL, try to find in content
            import re
            # Look for patterns like [HN] - Job Title or similar
            title_patterns = [
                r'\[([^\]]+)\]\s*-\s*([^\[\]]+)',  # [HN] - Job Title
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,})',  # Multiple capitalized words
                r'(Senior|Junior|Lead|Manager|Developer|Engineer|Designer|Analyst|Trợ giảng|Chuyên viên)\s+[A-Za-zÀ-ỹ]+'
            ]
            
            for pattern in title_patterns:
                matches = re.findall(pattern, content_text[:1000])  # Search in first 1000 chars
                if matches:
                    if isinstance(matches[0], tuple):
                        return ' '.join(matches[0])
                    else:
                        return matches[0]
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting job title: {e}")
            return ""
    
    def _extract_job_description_from_content(self, content_text: str) -> str:
        """Extract job description from content text"""
        try:
            # Look for job description sections
            desc_keywords = [
                'mô tả công việc', 'job description', 'mô tả', 'description',
                'yêu cầu', 'requirements', 'quyền lợi', 'benefits',
                'phạm vi', 'scope', 'hình thức', 'form'
            ]
            
            # Find the start of job description
            start_pos = -1
            for keyword in desc_keywords:
                pos = content_text.lower().find(keyword.lower())
                if pos != -1 and (start_pos == -1 or pos < start_pos):
                    start_pos = pos
            
            if start_pos != -1:
                # Extract description from start_pos to end or next section
                description = content_text[start_pos:start_pos + 2000]  # Limit to 2000 chars
                return description.strip()
            
            # If no keywords found, take first 1000 characters as description
            return content_text[:1000].strip()
            
        except Exception as e:
            logger.error(f"Error extracting job description: {e}")
            return ""
    
    def _extract_job_alternative_methods(self, soup, job_url: str) -> Dict:
        """Alternative methods to extract job details when standard methods fail"""
        try:
            # Method 1: Look for any text that might be job-related
            all_text = soup.get_text()
            
            # Find potential job titles (capitalized phrases)
            import re
            title_patterns = [
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,})',  # Multiple capitalized words
                r'(Senior|Junior|Lead|Manager|Developer|Engineer|Designer|Analyst)\s+[A-Za-z]+',
                r'([A-Za-z]+\s+(?:Developer|Engineer|Designer|Manager|Analyst|Specialist))'
            ]
            
            for pattern in title_patterns:
                matches = re.findall(pattern, all_text)
                if matches:
                    potential_title = matches[0]
                    if len(potential_title) > 5:
                        return {
                            'job_name': potential_title,
                            'job_type': 'Full-time',
                            'job_role': potential_title,
                            'job_description': all_text[:1000] if len(all_text) > 100 else all_text,
                            'job_link': job_url
                        }
            
            # Method 2: Look for any content in main areas
            main_content = soup.find('main') or soup.find('article') or soup.find('.content')
            if main_content:
                main_text = main_content.get_text().strip()
                if len(main_text) > 100:
                    return {
                        'job_name': 'Job Opportunity',  # Generic title
                        'job_type': 'Full-time',
                        'job_role': 'Job Opportunity',
                        'job_description': main_text[:1000],
                        'job_link': job_url
                    }
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Error in alternative job extraction: {e}")
            return {}
    
    def _extract_posted_date_from_description(self, description: str) -> Optional[str]:
        """Extract posted date from job description"""
        try:
            import re
            
            # Common date patterns
            date_patterns = [
                r'ngày đăng[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
                r'posted[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
                r'date[:\s]*(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{1,2}/\d{1,2}/\d{4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extracting posted date: {e}")
            return None
    
    def _extract_requirements_and_benefits(self, description: str) -> tuple[Optional[str], Optional[str]]:
        """Extract requirements and benefits from job description"""
        try:
            requirements = ""
            benefits = ""
            
            # Split description into sections
            lines = description.split('\n')
            current_section = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect section headers
                if any(keyword in line.lower() for keyword in ['yêu cầu', 'requirements', 'điều kiện']):
                    current_section = "requirements"
                    continue
                elif any(keyword in line.lower() for keyword in ['quyền lợi', 'benefits', 'phúc lợi', 'lợi ích']):
                    current_section = "benefits"
                    continue
                elif any(keyword in line.lower() for keyword in ['mô tả', 'description', 'công việc']):
                    current_section = "description"
                    continue
                
                # Add content to appropriate section
                if current_section == "requirements" and line.startswith('-'):
                    requirements += line + "\n"
                elif current_section == "benefits" and line.startswith('-'):
                    benefits += line + "\n"
            
            return requirements.strip(), benefits.strip()
            
        except Exception as e:
            logger.error(f"❌ Error extracting requirements and benefits: {e}")
            return None, None
    
    async def _extract_job_urls_from_career_page(self, career_page_url: str) -> List[str]:
        """Extract job URLs directly from career page HTML"""
        try:
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            import re
            
            # Crawl career page first to get HTML content
            from .crawler import crawl_single_url
            result = await crawl_single_url(career_page_url)
            if not result['success']:
                return []
            
            html_content = result['html']
            soup = BeautifulSoup(html_content, 'html.parser')
            
            job_urls = []
            
            # Method 1: Look for job links with common patterns (less restrictive)
            job_link_patterns = [
                r'/career/[^"]+',
                r'/careers/[^"]+',
                r'/jobs/[^"]+', 
                r'/positions/[^"]+',
                r'/opportunities/[^"]+',
                r'/tuyen-dung/[^"]+',
                r'/recruitment/[^"]+',
                r'/vacancies/[^"]+',
                r'/openings/[^"]+',
                r'/job/[^"]+',
                r'/position/[^"]+',
                r'/vacancy/[^"]+',
                r'/opening/[^"]+'
            ]
            
            # Find all links
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                
                # Check if href matches job patterns
                for pattern in job_link_patterns:
                    if re.search(pattern, href, re.IGNORECASE):
                        full_url = urljoin(career_page_url, href)
                        # Filter out the career page itself and ensure it's a job detail page
                        if (full_url not in job_urls and 
                            full_url != career_page_url and 
                            not full_url.endswith('/career') and
                            not full_url.endswith('/careers') and
                            not full_url.endswith('/jobs') and
                            not full_url.endswith('/positions') and
                            # Filter out AJAX load URLs
                            not '/load/' in full_url and
                            # Filter out product pages
                            not '/product' in full_url and
                            # Filter out hash fragments
                            not '#' in full_url):
                            job_urls.append(full_url)
                            logger.info(f"   🔗 Found job URL: {full_url}")
                
                # Check if link text contains job-related keywords (more flexible)
                link_text = link.get_text().strip().lower()
                job_keywords = [
                    # Job roles
                    'developer', 'engineer', 'designer', 'manager', 'analyst', 'specialist',
                    'coordinator', 'assistant', 'director', 'lead', 'head', 'chief',
                    'architect', 'consultant', 'advisor', 'expert', 'professional',
                    
                    # Seniority levels
                    'senior', 'junior', 'mid', 'entry', 'level', 'principal', 'staff',
                    'associate', 'executive', 'vice', 'deputy',
                    
                    # Job types
                    'full-time', 'part-time', 'contract', 'temporary', 'permanent',
                    'remote', 'hybrid', 'onsite', 'freelance', 'internship',
                    
                    # Departments
                    'software', 'frontend', 'backend', 'fullstack', 'mobile', 'web',
                    'data', 'ai', 'ml', 'devops', 'qa', 'testing', 'product',
                    'marketing', 'sales', 'hr', 'finance', 'legal', 'operations',
                    
                    # Technologies
                    'python', 'java', 'javascript', 'react', 'vue', 'angular',
                    'node', 'php', 'c#', 'dotnet', 'ruby', 'go', 'rust',
                    'aws', 'azure', 'gcp', 'docker', 'kubernetes',
                    
                    # Vietnamese keywords
                    'lập trình', 'phát triển', 'thiết kế', 'quản lý', 'phân tích',
                    'chuyên viên', 'trưởng nhóm', 'giám đốc', 'thực tập', 'cộng tác viên',
                    'tuyển dụng', 'việc làm', 'cơ hội', 'vị trí'
                ]
                if any(keyword in link_text for keyword in job_keywords):
                    full_url = urljoin(career_page_url, href)
                    if (full_url not in job_urls and 
                        full_url != career_page_url and
                        not full_url.endswith('/career') and
                        not full_url.endswith('/careers') and
                        not full_url.endswith('/jobs') and
                        not full_url.endswith('/positions')):
                        job_urls.append(full_url)
                        logger.info(f"   🔗 Found job URL by keyword: {full_url}")
            
            # Method 2: Look for job cards/sections
            job_card_patterns = [
                r'job', r'career', r'position', r'vacancy', r'opening', r'opportunity',
                r'listing', r'posting', r'role', r'employment', r'work', r'hire',
                r'candidate', r'applicant', r'resume', r'cv', r'application'
            ]
            job_cards = soup.find_all(['div', 'article', 'section', 'li'], 
                                     class_=re.compile('|'.join(job_card_patterns), re.IGNORECASE))
            for card in job_cards:
                link = card.find('a', href=True)
                if link:
                    href = link.get('href')
                    full_url = urljoin(career_page_url, href)
                    if (full_url not in job_urls and 
                        full_url != career_page_url and
                        not full_url.endswith('/career') and
                        not full_url.endswith('/careers') and
                        not full_url.endswith('/jobs') and
                        not full_url.endswith('/positions')):
                        job_urls.append(full_url)
                        logger.info(f"   🔗 Found job URL from card: {full_url}")
            
            # Method 3: Content-based job URL detection
            if not job_urls:
                logger.info(f"   🔍 No job URLs found with patterns, trying content analysis")
                content_job_urls = self._detect_job_urls_by_content(soup, career_page_url)
                job_urls.extend(content_job_urls)
            
            # Filter and validate job URLs
            validated_job_urls = self._validate_job_urls(job_urls, career_page_url)
            
            return validated_job_urls
            
        except Exception as e:
            logger.error(f"❌ Error extracting job URLs from career page: {e}")
            return []
    
    def _validate_job_urls(self, job_urls: List[str], career_page_url: str) -> List[str]:
        """Validate and filter job URLs to ensure they are actual job detail pages"""
        try:
            validated_urls = []
            
            for url in job_urls:
                # Skip if it's the career page itself
                if url == career_page_url:
                    continue
                
                # Skip AJAX load URLs
                if '/load/' in url:
                    logger.info(f"   ⚠️ Skipping AJAX load URL: {url}")
                    continue
                
                # Skip product pages
                if '/product' in url:
                    logger.info(f"   ⚠️ Skipping product page: {url}")
                    continue
                
                # Skip hash fragments
                if '#' in url:
                    logger.info(f"   ⚠️ Skipping hash fragment URL: {url}")
                    continue
                
                # Skip generic career pages
                if any(url.endswith(suffix) for suffix in ['/career', '/careers', '/jobs', '/positions']):
                    logger.info(f"   ⚠️ Skipping generic career page: {url}")
                    continue
                
                # Accept the URL if it passes basic filters (no keyword requirement)
                validated_urls.append(url)
                logger.info(f"   ✅ Validated job URL: {url}")
            
            return validated_urls
            
        except Exception as e:
            logger.error(f"❌ Error validating job URLs: {e}")
            return job_urls  # Return original if validation fails
    
    def _detect_job_urls_by_content(self, soup, career_page_url: str) -> List[str]:
        """Detect job URLs by analyzing link content and context"""
        try:
            from urllib.parse import urljoin
            
            job_urls = []
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                link_text = link.get_text().strip().lower()
                
                # Skip if it's the career page itself
                full_url = urljoin(career_page_url, href)
                if full_url == career_page_url:
                    continue
                
                # Check if link text suggests it's a job
                job_indicators = [
                    # Action words
                    'view', 'apply', 'details', 'read more', 'learn more', 'see more',
                    'view job', 'apply now', 'view position', 'apply for', 'view details',
                    'read full', 'learn about', 'see position', 'view opening',
                    
                    # Job roles (comprehensive)
                    'developer', 'engineer', 'designer', 'manager', 'analyst', 'specialist',
                    'coordinator', 'assistant', 'director', 'lead', 'head', 'chief',
                    'architect', 'consultant', 'advisor', 'expert', 'professional',
                    'programmer', 'coder', 'tester', 'qa', 'devops', 'sre',
                    
                    # Seniority levels
                    'senior', 'junior', 'mid', 'entry', 'level', 'principal', 'staff',
                    'associate', 'executive', 'vice', 'deputy', 'lead', 'head',
                    
                    # Job types
                    'full-time', 'part-time', 'contract', 'temporary', 'permanent',
                    'remote', 'hybrid', 'onsite', 'freelance', 'internship',
                    
                    # Departments
                    'software', 'frontend', 'backend', 'fullstack', 'mobile', 'web',
                    'data', 'ai', 'ml', 'devops', 'qa', 'testing', 'product',
                    'marketing', 'sales', 'hr', 'finance', 'legal', 'operations',
                    'research', 'development', 'engineering', 'technology',
                    
                    # Technologies
                    'python', 'java', 'javascript', 'react', 'vue', 'angular',
                    'node', 'php', 'c#', 'dotnet', 'ruby', 'go', 'rust',
                    'aws', 'azure', 'gcp', 'docker', 'kubernetes',
                    
                    # Vietnamese keywords
                    'lập trình', 'phát triển', 'thiết kế', 'quản lý', 'phân tích',
                    'chuyên viên', 'trưởng nhóm', 'giám đốc', 'thực tập', 'cộng tác viên',
                    'xem chi tiết', 'ứng tuyển', 'tìm hiểu thêm', 'xem thêm'
                ]
                
                if any(indicator in link_text for indicator in job_indicators):
                    if full_url not in job_urls:
                        job_urls.append(full_url)
                        logger.info(f"   🔗 Found job URL by content: {full_url} (text: {link_text})")
            
            return job_urls
            
        except Exception as e:
            logger.error(f"❌ Error in content-based job URL detection: {e}")
            return []
    
    def _analyze_job_structure(self, jobs: List[Dict], career_page_url: str) -> Dict:
        """Analyze job structure to determine extraction type"""
        analysis = {
            'has_individual_urls': False,
            'has_job_data': False,
            'job_urls': [],
            'job_count': len(jobs),
            'url_count': 0,
            'data_count': 0
        }
        
        for job in jobs:
            # Check if job has individual URL
            if job.get('url') and job['url'] != career_page_url:
                analysis['job_urls'].append(job['url'])
                analysis['url_count'] += 1
            
            # Check if job has data
            if job.get('title') or job.get('description'):
                analysis['data_count'] += 1
        
        analysis['has_individual_urls'] = analysis['url_count'] > 0
        analysis['has_job_data'] = analysis['data_count'] > 0
        
        return analysis
    
    async def _try_alternative_extraction_methods(self, career_page_url: str, max_jobs: int) -> Dict:
        """Try alternative extraction methods when standard method fails"""
        try:
            logger.info(f"   🔍 Trying alternative extraction methods for: {career_page_url}")
            
            # Method 1: Try to extract from HTML directly
            from .crawler import crawl_single_url
            result = await crawl_single_url(career_page_url)
            if result['success']:
                html_jobs = self._extract_jobs_from_html_directly(result['html'], career_page_url)
                if html_jobs:
                    logger.info(f"   ✅ HTML direct extraction found {len(html_jobs)} jobs")
                    return {
                        'success': True,
                        'jobs': html_jobs,
                        'extraction_type': 'html_direct',
                        'has_individual_urls': False
                    }
            
            # Method 2: Try to find job listings in common patterns
            pattern_jobs = await self._extract_jobs_from_patterns(career_page_url)
            if pattern_jobs:
                logger.info(f"   ✅ Pattern extraction found {len(pattern_jobs)} jobs")
                return {
                    'success': True,
                    'jobs': pattern_jobs,
                    'extraction_type': 'pattern_based',
                    'has_individual_urls': False
                }
            
            # Method 3: Try to extract from JavaScript data
            js_jobs = await self._extract_jobs_from_javascript(career_page_url)
            if js_jobs:
                logger.info(f"   ✅ JavaScript extraction found {len(js_jobs)} jobs")
                return {
                    'success': True,
                    'jobs': js_jobs,
                    'extraction_type': 'javascript',
                    'has_individual_urls': False
                }
            
            logger.warning(f"   ❌ All alternative methods failed")
            return {
                'success': False,
                'jobs': [],
                'extraction_type': 'failed',
                'has_individual_urls': False
            }
            
        except Exception as e:
            import traceback
            logger.exception("   ❌ Error in alternative extraction")  # tự động in traceback
            return {
                'success': False,
                'jobs': [],
                'extraction_type': 'error',
                'has_individual_urls': False
            }
    
    def _extract_jobs_from_html_directly(self, html_content: str, base_url: str) -> List[Dict]:
        """Extract jobs directly from HTML content"""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            jobs = []
            
            # Common job listing selectors
            job_selectors = [
                '.job-listing', '.job-item', '.career-item', '.position-item',
                '.job-card', '.career-card', '.position-card',
                '[class*="job"]', '[class*="career"]', '[class*="position"]'
            ]
            
            for selector in job_selectors:
                job_elements = soup.select(selector)
                if job_elements:
                    logger.info(f"   📊 Found {len(job_elements)} job elements with selector: {selector}")
                    
                    for element in job_elements[:50]:  # Limit to 50 jobs
                        job = self._extract_job_from_element(element, base_url)
                        if job and job.get('title'):
                            jobs.append(job)
                    
                    if jobs:
                        break
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error extracting jobs from HTML: {e}")
            return []
    
    async def _extract_jobs_from_patterns(self, career_page_url: str) -> List[Dict]:
        """Extract jobs using common patterns"""
        try:
            # Common career page patterns
            patterns = [
                f"{career_page_url}/jobs",
                f"{career_page_url}/careers", 
                f"{career_page_url}/positions",
                f"{career_page_url}/opportunities"
            ]
            
            for pattern_url in patterns:
                try:
                    from .crawler import crawl_single_url
                    result = await crawl_single_url(pattern_url)
                    if result['success']:
                        jobs = self._extract_jobs_from_html_directly(result['html'], pattern_url)
                        if jobs:
                            return jobs
                except:
                    continue
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting jobs from patterns: {e}")
            return []
    
    async def _extract_jobs_from_javascript(self, career_page_url: str) -> List[Dict]:
        """Extract jobs from JavaScript data using HTML parsing (requests-only mode)"""
        try:
            # Use requests to get HTML content instead of Playwright
            import aiohttp
            
            jobs = []
            
            async with aiohttp.ClientSession() as session:
                async with session.get(career_page_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # Parse HTML with BeautifulSoup
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Method 1: Extract from JavaScript variables in script tags
                        scripts = soup.find_all('script')
                        for script in scripts[:5]:  # Limit to first 5 scripts
                            content = script.string or script.get_text()
                            if content:
                                # Look for common job data variables
                                patterns = [
                                    r'jobs\s*:\s*(\[.*?\])',
                                    r'jobList\s*:\s*(\[.*?\])',
                                    r'careers\s*:\s*(\[.*?\])',
                                    r'positions\s*:\s*(\[.*?\])',
                                    r'openings\s*:\s*(\[.*?\])',
                                    r'jobData\s*:\s*(\[.*?\])',
                                    r'careerData\s*:\s*(\[.*?\])',
                                    r'positionData\s*:\s*(\[.*?\])'
                                ]
                                
                                for pattern in patterns:
                                    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                                    for match in matches:
                                        try:
                                            js_jobs = json.loads(match)
                                            if isinstance(js_jobs, list) and len(js_jobs) > 0:
                                                logger.info(f"   📊 Found {len(js_jobs)} jobs from JavaScript variables")
                                                for job in js_jobs[:10]:  # Limit to 10 jobs
                                                    if isinstance(job, dict):
                                                        jobs.append({
                                                            'title': job.get('title', ''),
                                                            'company': job.get('company', ''),
                                                            'location': job.get('location', ''),
                                                            'job_type': job.get('job_type', 'Full-time'),
                                                            'salary': job.get('salary', ''),
                                                            'posted_date': job.get('posted_date', ''),
                                                            'url': job.get('url', career_page_url),
                                                            'description': job.get('description', ''),
                                                            'requirements': job.get('requirements', ''),
                                                            'benefits': job.get('benefits', '')
                                                        })
                                                break  # Found jobs, no need to check other patterns
                                        except json.JSONDecodeError:
                                            continue
                        
                        # Method 2: Extract from data attributes
                        data_elements = soup.find_all(attrs={'data-job': True})
                        for element in data_elements[:10]:  # Limit to 10 elements
                            try:
                                job_data = element.get('data-job')
                                if job_data:
                                    if isinstance(job_data, str):
                                        job_json = json.loads(job_data)
                                    else:
                                        job_json = job_data
                                    
                                    if isinstance(job_json, dict):
                                        jobs.append({
                                            'title': job_json.get('title', ''),
                                            'company': job_json.get('company', ''),
                                            'location': job_json.get('location', ''),
                                            'job_type': job_json.get('job_type', 'Full-time'),
                                            'salary': job_json.get('salary', ''),
                                            'posted_date': job_json.get('posted_date', ''),
                                            'url': job_json.get('url', career_page_url),
                                            'description': job_json.get('description', ''),
                                            'requirements': job_json.get('requirements', ''),
                                            'benefits': job_json.get('benefits', '')
                                        })
                            except (json.JSONDecodeError, AttributeError):
                                continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error extracting jobs from JavaScript: {e}")
            return []
    
    def _extract_job_from_element(self, element, base_url: str) -> Dict:
        """Extract job data from a single HTML element"""
        try:
            from bs4 import BeautifulSoup
            
            # Common selectors for job data
            selectors = {
                'title': [
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    '.job-title', '.position-title', '.career-title',
                    '[class*="title"]', '[class*="name"]'
                ],
                'company': [
                    '.company', '.company-name', '.employer',
                    '[class*="company"]', '[class*="employer"]'
                ],
                'location': [
                    '.location', '.job-location', '.position-location',
                    '[class*="location"]', '[class*="place"]'
                ],
                'salary': [
                    '.salary', '.compensation', '.pay',
                    '[class*="salary"]', '[class*="pay"]'
                ],
                'description': [
                    '.description', '.job-description', '.position-description',
                    '.summary', '.details', '[class*="description"]'
                ],
                'job_type': [
                    '.job-type', '.employment-type', '.position-type',
                    '[class*="type"]', '[class*="employment"]'
                ],
                'posted_date': [
                    '.posted-date', '.date-posted', '.published-date',
                    '[class*="date"]', '[class*="posted"]'
                ]
            }
            
            job_data = {
                'title': '',
                'company': '',
                'location': '',
                'job_type': 'Full-time',
                'salary': '',
                'posted_date': '',
                'url': base_url,  # Use base URL since no individual URL
                'description': '',
                'requirements': '',
                'benefits': ''
            }
            
            # Extract data using selectors
            for field, field_selectors in selectors.items():
                for selector in field_selectors:
                    found_element = element.select_one(selector)
                    if found_element:
                        text = found_element.get_text(strip=True)
                        if text:
                            job_data[field] = text
                            break
            
            # If no title found, try to get text from the element itself
            if not job_data['title']:
                # Look for any heading or strong text
                title_element = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b'])
                if title_element:
                    job_data['title'] = title_element.get_text(strip=True)
                else:
                    # Use first line of text as title
                    text_lines = element.get_text().split('\n')
                    for line in text_lines:
                        line = line.strip()
                        if line and len(line) > 10:  # Reasonable title length
                            job_data['title'] = line
                            break
            
            # Extract description from remaining text
            if not job_data['description']:
                full_text = element.get_text()
                if full_text and len(full_text) > 50:  # Reasonable description length
                    job_data['description'] = full_text[:500]  # Limit to 500 chars
            
            return job_data
            
        except Exception as e:
            logger.error(f"Error extracting job from element: {e}")
            return {
                'title': '',
                'company': '',
                'location': '',
                'job_type': 'Full-time',
                'salary': '',
                'posted_date': '',
                'url': base_url,
                'description': '',
                'requirements': '',
                'benefits': ''
            }
    
    async def _extract_jobs_from_accordions(self, page) -> List[Dict]:
        """Extract jobs from accordions/tabs by clicking to expand"""
        try:
            jobs = []
            
            # Common accordion selectors
            accordion_selectors = [
                '.accordion', '.accordion-item', '.collapsible', '.expandable',
                '.tab-content', '.tab-pane', '.collapse', '.panel',
                '[class*="accordion"]', '[class*="collapse"]', '[class*="expand"]'
            ]
            
            for selector in accordion_selectors:
                accordion_elements = await page.query_selector_all(selector)
                if accordion_elements:
                    logger.info(f"   📊 Found {len(accordion_elements)} accordion elements with selector: {selector}")
                    
                    for element in accordion_elements[:10]:  # Limit to 10 accordions
                        try:
                            # Click to expand
                            await element.click()
                            await page.wait_for_timeout(1000)  # Wait for content to load
                            
                            # Extract job data from expanded content
                            job_data = await page.evaluate("""
                                (element) => {
                                    const job = {
                                        title: '',
                                        company: '',
                                        location: '',
                                        description: '',
                                        url: window.location.href
                                    };
                                    
                                    // Look for job title
                                    const titleEl = element.querySelector('h1, h2, h3, h4, h5, h6, .title, .job-title');
                                    if (titleEl) job.title = titleEl.textContent.trim();
                                    
                                    // Look for company
                                    const companyEl = element.querySelector('.company, .employer, [class*="company"]');
                                    if (companyEl) job.company = companyEl.textContent.trim();
                                    
                                    // Look for location
                                    const locationEl = element.querySelector('.location, .place, [class*="location"]');
                                    if (locationEl) job.location = locationEl.textContent.trim();
                                    
                                    // Look for description
                                    const descEl = element.querySelector('.description, .content, .details, p');
                                    if (descEl) job.description = descEl.textContent.trim();
                                    
                                    return job;
                                }
                            """, element)
                            
                            if job_data.get('title'):
                                jobs.append({
                                    'title': job_data.get('title', ''),
                                    'company': job_data.get('company', ''),
                                    'location': job_data.get('location', ''),
                                    'job_type': 'Full-time',
                                    'salary': '',
                                    'posted_date': '',
                                    'url': job_data.get('url', ''),
                                    'description': job_data.get('description', ''),
                                    'requirements': '',
                                    'benefits': ''
                                })
                            
                            # Close accordion
                            await element.click()
                            await page.wait_for_timeout(500)
                            
                        except Exception as e:
                            logger.error(f"Error processing accordion element: {e}")
                            continue
                    
                    if jobs:
                        break
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error extracting jobs from accordions: {e}")
            return []
    
    async def _extract_jobs_from_modals(self, page) -> List[Dict]:
        """Extract jobs from modals/popups"""
        try:
            jobs = []
            
            # Common modal selectors
            modal_selectors = [
                '.modal', '.popup', '.dialog', '.overlay',
                '[class*="modal"]', '[class*="popup"]', '[class*="dialog"]'
            ]
            
            # Find modal triggers
            trigger_selectors = [
                '.job-card', '.career-card', '.position-card',
                '[class*="job"]', '[class*="career"]', '[class*="position"]'
            ]
            
            for trigger_selector in trigger_selectors:
                triggers = await page.query_selector_all(trigger_selector)
                if triggers:
                    logger.info(f"   📊 Found {len(triggers)} modal triggers with selector: {trigger_selector}")
                    
                    for trigger in triggers[:5]:  # Limit to 5 modals
                        try:
                            # Click to open modal
                            await trigger.click()
                            await page.wait_for_timeout(2000)  # Wait for modal to open
                            
                            # Extract from modal content
                            modal_job = await page.evaluate("""
                                () => {
                                    const modal = document.querySelector('.modal, .popup, .dialog, [class*="modal"]');
                                    if (!modal) return null;
                                    
                                    const job = {
                                        title: '',
                                        company: '',
                                        location: '',
                                        description: '',
                                        url: window.location.href
                                    };
                                    
                                    // Extract job data from modal
                                    const titleEl = modal.querySelector('h1, h2, h3, .title, .job-title');
                                    if (titleEl) job.title = titleEl.textContent.trim();
                                    
                                    const companyEl = modal.querySelector('.company, .employer');
                                    if (companyEl) job.company = companyEl.textContent.trim();
                                    
                                    const locationEl = modal.querySelector('.location, .place');
                                    if (locationEl) job.location = locationEl.textContent.trim();
                                    
                                    const descEl = modal.querySelector('.description, .content, .details');
                                    if (descEl) job.description = descEl.textContent.trim();
                                    
                                    return job;
                                }
                            """)
                            
                            if modal_job and modal_job.get('title'):
                                jobs.append({
                                    'title': modal_job.get('title', ''),
                                    'company': modal_job.get('company', ''),
                                    'location': modal_job.get('location', ''),
                                    'job_type': 'Full-time',
                                    'salary': '',
                                    'posted_date': '',
                                    'url': modal_job.get('url', ''),
                                    'description': modal_job.get('description', ''),
                                    'requirements': '',
                                    'benefits': ''
                                })
                            
                            # Close modal
                            close_button = await page.query_selector('.close, .modal-close, [aria-label="Close"]')
                            if close_button:
                                await close_button.click()
                            else:
                                # Press Escape key
                                await page.keyboard.press('Escape')
                            
                            await page.wait_for_timeout(1000)
                            
                        except Exception as e:
                            logger.error(f"Error processing modal: {e}")
                            continue
                    
                    if jobs:
                        break
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error extracting jobs from modals: {e}")
            return []
    
    async def _extract_jobs_from_ajax(self, page) -> List[Dict]:
        """Extract jobs from AJAX-loaded content"""
        try:
            jobs = []
            
            # Look for "Load More" buttons
            load_more_selectors = [
                '.load-more', '.load-more-btn', '.show-more',
                '[class*="load"]', '[class*="more"]', 'button:contains("Load More")'
            ]
            
            for selector in load_more_selectors:
                load_more_btn = await page.query_selector(selector)
                if load_more_btn:
                    logger.info(f"   📊 Found Load More button: {selector}")
                    
                    # Click Load More multiple times
                    for i in range(3):  # Try to load 3 more pages
                        try:
                            await load_more_btn.click()
                            await page.wait_for_timeout(2000)  # Wait for content to load
                            
                            # Extract newly loaded jobs
                            new_jobs = await page.evaluate("""
                                () => {
                                    const jobs = [];
                                    const jobElements = document.querySelectorAll('.job-card, .career-card, .position-card, [class*="job"]');
                                    
                                    for (const element of jobElements) {
                                        const job = {
                                            title: '',
                                            company: '',
                                            location: '',
                                            description: '',
                                            url: window.location.href
                                        };
                                        
                                        const titleEl = element.querySelector('h1, h2, h3, .title, .job-title');
                                        if (titleEl) job.title = titleEl.textContent.trim();
                                        
                                        const companyEl = element.querySelector('.company, .employer');
                                        if (companyEl) job.company = companyEl.textContent.trim();
                                        
                                        const locationEl = element.querySelector('.location, .place');
                                        if (locationEl) job.location = locationEl.textContent.trim();
                                        
                                        const descEl = element.querySelector('.description, .content');
                                        if (descEl) job.description = descEl.textContent.trim();
                                        
                                        if (job.title) jobs.push(job);
                                    }
                                    
                                    return jobs;
                                }
                            """)
                            
                            for job_data in new_jobs:
                                if job_data.get('title') and not any(j.get('title') == job_data.get('title') for j in jobs):
                                    jobs.append({
                                        'title': job_data.get('title', ''),
                                        'company': job_data.get('company', ''),
                                        'location': job_data.get('location', ''),
                                        'job_type': 'Full-time',
                                        'salary': '',
                                        'posted_date': '',
                                        'url': job_data.get('url', ''),
                                        'description': job_data.get('description', ''),
                                        'requirements': '',
                                        'benefits': ''
                                    })
                            
                        except Exception as e:
                            logger.error(f"Error loading more content: {e}")
                            break
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error extracting jobs from AJAX: {e}")
            return []
    
    async def _extract_jobs_from_iframes(self, page) -> List[Dict]:
        """Extract jobs from iframes"""
        try:
            jobs = []
            
            # Find all iframes
            iframes = await page.query_selector_all('iframe')
            
            for iframe in iframes:
                try:
                    # Get iframe content
                    iframe_content = await page.evaluate("""
                        (iframe) => {
                            try {
                                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                                if (!iframeDoc) return null;
                                
                                const jobs = [];
                                const jobElements = iframeDoc.querySelectorAll('.job-card, .career-card, .position-card, [class*="job"]');
                                
                                for (const element of jobElements) {
                                    const job = {
                                        title: '',
                                        company: '',
                                        location: '',
                                        description: '',
                                        url: iframe.src || window.location.href
                                    };
                                    
                                    const titleEl = element.querySelector('h1, h2, h3, .title, .job-title');
                                    if (titleEl) job.title = titleEl.textContent.trim();
                                    
                                    const companyEl = element.querySelector('.company, .employer');
                                    if (companyEl) job.company = companyEl.textContent.trim();
                                    
                                    const locationEl = element.querySelector('.location, .place');
                                    if (locationEl) job.location = locationEl.textContent.trim();
                                    
                                    const descEl = element.querySelector('.description, .content');
                                    if (descEl) job.description = descEl.textContent.trim();
                                    
                                    if (job.title) jobs.push(job);
                                }
                                
                                return jobs;
                            } catch (e) {
                                return null;
                            }
                        }
                    """, iframe)
                    
                    if iframe_content:
                        for job_data in iframe_content:
                            jobs.append({
                                'title': job_data.get('title', ''),
                                'company': job_data.get('company', ''),
                                'location': job_data.get('location', ''),
                                'job_type': 'Full-time',
                                'salary': '',
                                'posted_date': '',
                                'url': job_data.get('url', ''),
                                'description': job_data.get('description', ''),
                                'requirements': '',
                                'benefits': ''
                            })
                
                except Exception as e:
                    logger.error(f"Error processing iframe: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error extracting jobs from iframes: {e}")
            return []
    
    async def _extract_jobs_from_shadow_dom(self, page) -> List[Dict]:
        """Extract jobs from Shadow DOM"""
        try:
            jobs = []
            
            # Find elements with shadow roots
            shadow_jobs = await page.evaluate("""
                () => {
                    const jobs = [];
                    
                    // Find all elements that might have shadow roots
                    const elements = document.querySelectorAll('*');
                    
                    for (const element of elements) {
                        if (element.shadowRoot) {
                            const shadowJobs = element.shadowRoot.querySelectorAll('.job-card, .career-card, .position-card, [class*="job"]');
                            
                            for (const jobElement of shadowJobs) {
                                const job = {
                                    title: '',
                                    company: '',
                                    location: '',
                                    description: '',
                                    url: window.location.href
                                };
                                
                                const titleEl = jobElement.querySelector('h1, h2, h3, .title, .job-title');
                                if (titleEl) job.title = titleEl.textContent.trim();
                                
                                const companyEl = jobElement.querySelector('.company, .employer');
                                if (companyEl) job.company = companyEl.textContent.trim();
                                
                                const locationEl = jobElement.querySelector('.location, .place');
                                if (locationEl) job.location = locationEl.textContent.trim();
                                
                                const descEl = jobElement.querySelector('.description, .content');
                                if (descEl) job.description = descEl.textContent.trim();
                                
                                if (job.title) jobs.push(job);
                            }
                        }
                    }
                    
                    return jobs;
                }
            """)
            
            for job_data in shadow_jobs:
                jobs.append({
                    'title': job_data.get('title', ''),
                    'company': job_data.get('company', ''),
                    'location': job_data.get('location', ''),
                    'job_type': 'Full-time',
                    'salary': '',
                    'posted_date': '',
                    'url': job_data.get('url', ''),
                    'description': job_data.get('description', ''),
                    'requirements': '',
                    'benefits': ''
                })
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error extracting jobs from shadow DOM: {e}")
            return []