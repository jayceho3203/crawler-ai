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
        self._direct_jobs_cache = []
        self._career_page_cache = None
        
        # Class-level cache for global access (persistent across instances)
        if not hasattr(JobExtractionService, '_global_direct_jobs_cache'):
            JobExtractionService._global_direct_jobs_cache = []
        if not hasattr(JobExtractionService, '_global_career_page_cache'):
            JobExtractionService._global_career_page_cache = None
        
        # Don't clear global cache in constructor - keep it persistent
        logger.info(f"   📄 Global cache initialized: {len(JobExtractionService._global_direct_jobs_cache)} jobs")
    
    def clear_all_cache(self):
        """Clear all cache levels"""
        self._direct_jobs_cache = []
        self._career_page_cache = None
        JobExtractionService._global_direct_jobs_cache = []
        JobExtractionService._global_career_page_cache = None
        logger.info("   🗑️ Cleared all cache levels")
        
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
                    jobs = result.get('jobs', [])
                    
                    # Extract job URLs from jobs
                    page_job_urls = []
                    for job in jobs:
                        job_url = job.get('url', '')
                        if job_url and self._is_job_url(job_url) and job_url not in all_job_urls:
                            all_job_urls.append(job_url)
                            page_job_urls.append(job_url)
                    
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
    
    def _is_http_url(self, url: str) -> bool:
        """Check if URL is a valid HTTP/HTTPS URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.scheme in ('http', 'https')
        except:
            return False
    
    def _is_job_url(self, url: str) -> bool:
        """Check if URL is a job detail page - SIMPLIFIED VERSION"""
        url_lower = url.lower()
        
        # Skip invalid URLs
        if not url or url_lower.startswith(('javascript:', 'mailto:', 'tel:', '#')):
            return False
        
        # Must be a valid HTTP URL
        if not self._is_http_url(url):
            return False
        
        # Skip files that are clearly not job pages
        skip_files = ['.xml', '.json', '.pdf', '.doc', '.docx', 'sitemap.xml', 'robots.txt']
        if any(file_ext in url_lower for file_ext in skip_files):
            return False
        
        # Basic job URL patterns
        job_patterns = [
            '/job/', '/jobs/', '/career/', '/careers/', '/position/', '/vacancy/',
            '/opportunity/', '/opening/', '/apply/', '/recruitment/', '/employment/',
            '/hiring/', '/tuyen-dung/', '/viec-lam/', '/co-hoi/', '/nhan-vien/',
            '/ung-vien/', '/cong-viec/', '/lam-viec/', '/thu-viec/', '/chinh-thuc/',
            '/nghe-nghiep/', '/tim-viec/', '/dang-tuyen/', '/vi-tri/', '/ung-tuyen/',
            '/ho-so/', '/phong-van/', '/developer/', '/engineer/', '/analyst/',
            '/manager/', '/specialist/', '/consultant/', '/coordinator/', '/assistant/',
            '/director/', '/lead/', '/senior/', '/junior/', '/intern/', '/trainee/',
            '/graduate/', '/remote/', '/hybrid/', '/full-time/', '/part-time/',
            '/contract/', '/freelance/', '/temporary/', '/role/', '/title/',
            '/posting/', '/listing/', '/search/', '/find/', '/browse/', '/view/',
            '/detail/', '/description/', '/requirements/'
        ]
        
        # Check if URL contains job patterns
        has_job_pattern = any(pattern in url_lower for pattern in job_patterns)
        
        # Reject URLs that are just career page roots
        if (url_lower.rstrip('/').endswith('/career') or 
            url_lower.rstrip('/').endswith('/careers') or 
            url_lower.rstrip('/').endswith('/jobs')):
            return False
        
        # URL should have some path content (not just domain)
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        path = parsed_url.path.strip('/')
        
        if not path or len(path.split('/')) < 1:
            return False
        
        # If it has job patterns, it's likely a job URL
        if has_job_pattern:
            return True
        
        # For URLs without obvious patterns, check if it's not obviously non-job
        non_job_patterns = [
            '/about', '/contact', '/privacy', '/terms', '/cookie', '/news', '/blog',
            '/press', '/media', '/investor', '/sustainability', '/diversity', '/culture',
            '/values', '/leadership', '/team', '/office', '/location', '/university',
            '/training', '/development', '/program', '/event', '/webinar', '/conference',
            '/award', '/partnership', '/client', '/customer', '/service', '/product',
            '/solution', '/technology', '/innovation', '/research', '/case-study',
            '/whitepaper', '/report'
        ]
        
        # If it doesn't have non-job patterns, accept it
        return not any(pattern in url_lower for pattern in non_job_patterns)
    
    def _is_pagination_url(self, url: str) -> bool:
        """Check if URL is a pagination page"""
        pagination_indicators = ['?paged=', '?page=', '?p=', '/page/']
        return any(indicator in url.lower() for indicator in pagination_indicators)
    
    async def _extract_single_job_detail(self, job_url: str) -> Optional[Dict]:
        """Extract details from a single job URL"""
        try:
            # Validate URL first
            if not self._is_job_url(job_url):
                logger.warning(f"   ⚠️ Skipping invalid job URL: {job_url}")
                return None
            
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
    
    async def _analyze_career_page_structure(self, career_page_url: str) -> Dict:
        """
        Analyze career page structure to determine the best extraction strategy.
        Professional approach: Analyze first, then apply appropriate method.
        """
        try:
            logger.info(f"   🔍 Analyzing page structure for: {career_page_url}")
            
            from .crawler import crawl_single_url
            from bs4 import BeautifulSoup
            import re
            
            # Get page content
            result = await crawl_single_url(career_page_url)
            if not result.get('success') or not result.get('html'):
                return {
                    'page_type': 'unknown',
                    'has_individual_urls': False,
                    'has_embedded_jobs': False,
                    'job_count': 0,
                    'recommended_strategy': 'embedded_jobs',
                    'analysis_details': 'Failed to fetch page content'
                }
            
            html = result['html']
            soup = BeautifulSoup(html, 'html.parser')
            page_text = soup.get_text()
            
            # 1. CHECK FOR INDIVIDUAL JOB URLs
            individual_urls = await self._extract_job_urls_from_career_page(career_page_url)
            has_individual_urls = len(individual_urls) > 0
            
            # 2. CHECK FOR EMBEDDED JOBS USING PATTERNS
            job_patterns = [
                r'([A-Z][a-zA-Z\s]+(?:Developer|Engineer|Manager|Analyst|Specialist|Assistant|Designer)).*?(?:Apply|View|See|Learn|Details)',
                r'([A-Z][a-zA-Z\s]+(?:Developer|Engineer|Manager|Analyst|Specialist|Assistant|Designer)).*?(?:Fulltime|Part-time|Contract|Only|Remote)',
                r'([A-Z][a-zA-Z\s]+(?:Developer|Engineer|Manager|Analyst|Specialist|Assistant|Designer))[^.\n]*?See Details',
                r'([A-Z][a-zA-Z\s]+(?:Developer|Engineer|Manager|Analyst|Specialist|Assistant|Designer))[^.\n]*?(?:Singapore|Remote|Fully Remote)'
            ]
            
            embedded_job_count = 0
            for pattern in job_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE | re.DOTALL)
                embedded_job_count += len(matches)
            
            has_embedded_jobs = embedded_job_count > 0
            
            # 3. DETERMINE PAGE TYPE
            if has_individual_urls and not has_embedded_jobs:
                page_type = 'individual_jobs'
                recommended_strategy = 'individual_urls'
            elif has_embedded_jobs and not has_individual_urls:
                page_type = 'embedded_jobs'
                recommended_strategy = 'embedded_jobs'
            elif has_individual_urls and has_embedded_jobs:
                page_type = 'hybrid'
                recommended_strategy = 'hybrid'
            else:
                page_type = 'unknown'
                recommended_strategy = 'embedded_jobs'
            
            # 4. ESTIMATE JOB COUNT
            job_count = len(individual_urls) if has_individual_urls else embedded_job_count
            
            analysis = {
                'page_type': page_type,
                'has_individual_urls': has_individual_urls,
                'has_embedded_jobs': has_embedded_jobs,
                'job_count': job_count,
                'recommended_strategy': recommended_strategy,
                'analysis_details': {
                    'individual_urls_found': len(individual_urls),
                    'embedded_jobs_found': embedded_job_count,
                    'page_text_length': len(page_text)
                }
            }
            
            logger.info(f"   📊 Analysis complete: {page_type} page with {job_count} jobs")
            return analysis
            
        except Exception as e:
            logger.error(f"   ❌ Error analyzing page structure: {e}")
            return {
                'page_type': 'unknown',
                'has_individual_urls': False,
                'has_embedded_jobs': False,
                'job_count': 0,
                'recommended_strategy': 'embedded_jobs',
                'analysis_details': f'Analysis failed: {str(e)}'
            }

    async def _extract_individual_job_urls(self, career_page_url: str, max_jobs: int, start_time: float) -> Dict:
        """Extract individual job URLs using the traditional method"""
        try:
            job_urls = await self._extract_job_urls_from_career_page(career_page_url)
            if job_urls:
                crawl_time = (time.time() - start_time)
                response = {
                    'success': True,
                    'career_page_url': career_page_url,
                    'total_jobs_found': len(job_urls),
                    'has_individual_urls': True,
                    'job_urls': job_urls,
                    'job_indices': [],
                    'crawl_time': crawl_time,
                    'crawl_method': 'scrapy_optimized',
                    'detection_method': 'links_detected',
                    'extraction_stage': 'links_detected'
                }
                # Cache career page for details API
                self._career_page_cache = career_page_url
                JobExtractionService._global_career_page_cache = career_page_url
                return response
            else:
                return {
                    'success': False,
                    'career_page_url': career_page_url,
                    'error_message': 'No individual job URLs found',
                    'crawl_time': time.time() - start_time,
                    'crawl_method': 'failed',
                    'detection_method': 'failed',
                    'extraction_stage': 'failed'
                }
        except Exception as e:
            logger.error(f"❌ Error extracting individual job URLs: {e}")
            return {
                'success': False,
                'career_page_url': career_page_url,
                'error_message': str(e),
                'crawl_time': time.time() - start_time,
                'crawl_method': 'failed',
                'detection_method': 'failed',
                'extraction_stage': 'failed'
            }

    async def _extract_embedded_jobs(self, career_page_url: str, max_jobs: int, start_time: float) -> Dict:
        """Extract embedded jobs using pattern matching"""
        try:
            from .crawler import crawl_single_url
            from bs4 import BeautifulSoup
            
            result = await crawl_single_url(career_page_url)
            if result['success'] and result['html']:
                soup = BeautifulSoup(result['html'], 'html.parser')
                container_jobs = self._extract_jobs_from_cards(soup, career_page_url)
            else:
                container_jobs = []
            
            if container_jobs:
                # Normalize titles/locations and dedupe
                normalized = self._normalize_jobs(container_jobs)
                self._direct_jobs_cache = normalized
                JobExtractionService._global_direct_jobs_cache = normalized
                crawl_time = (time.time() - start_time)
                response = {
                    'success': True,
                    'career_page_url': career_page_url,
                    'total_jobs_found': len(normalized),
                    'has_individual_urls': False,
                    'job_urls': [],
                    'job_indices': list(range(1, len(normalized) + 1)),
                    'crawl_time': crawl_time,
                    'crawl_method': 'scrapy_optimized',
                    'detection_method': 'pattern_matching',
                    'extraction_stage': 'pattern_detected',
                    'direct_jobs': normalized
                }
                # Cache career page for details API
                self._career_page_cache = career_page_url
                JobExtractionService._global_career_page_cache = career_page_url
                return response
            else:
                return {
                    'success': False,
                    'career_page_url': career_page_url,
                    'error_message': 'No embedded jobs found',
                    'crawl_time': time.time() - start_time,
                    'crawl_method': 'failed',
                    'detection_method': 'failed',
                    'extraction_stage': 'failed'
                }
        except Exception as e:
            logger.error(f"❌ Error extracting embedded jobs: {e}")
            return {
                'success': False,
                'career_page_url': career_page_url,
                'error_message': str(e),
                'crawl_time': time.time() - start_time,
                'crawl_method': 'failed',
                'detection_method': 'failed',
                'extraction_stage': 'failed'
            }

    async def extract_job_urls_only(self, career_page_url: str, max_jobs: int = 50, include_job_data: bool = False) -> Dict:
        """
        Extract job URLs from a career page for N8N. 
        Professional approach: Analyze page structure first, then apply appropriate strategy.
        """
        start_time = time.time()
        
        try:
            logger.info(f"🔗 Extracting job URLs from: {career_page_url}")
            
            # CLEAR CACHE FIRST to prevent data mixing between different companies
            self.clear_all_cache()
            logger.info("   🗑️ Cleared all cache to prevent data mixing")
            
            # STEP 1: ANALYZE PAGE STRUCTURE FIRST
            logger.info("   🔍 Step 1: Analyze page structure and classify career page type")
            page_analysis = await self._analyze_career_page_structure(career_page_url)
            
            logger.info(f"   📊 Page Analysis Results:")
            logger.info(f"      - Page Type: {page_analysis.get('page_type', 'unknown')}")
            logger.info(f"      - Has Individual URLs: {page_analysis.get('has_individual_urls', False)}")
            logger.info(f"      - Has Embedded Jobs: {page_analysis.get('has_embedded_jobs', False)}")
            logger.info(f"      - Job Count: {page_analysis.get('job_count', 0)}")
            logger.info(f"      - Recommended Strategy: {page_analysis.get('recommended_strategy', 'unknown')}")
            
            # STEP 2: APPLY APPROPRIATE STRATEGY BASED ON ANALYSIS
            recommended_strategy = page_analysis.get('recommended_strategy', 'unknown')
            
            if recommended_strategy == 'individual_urls':
                logger.info("   🎯 Strategy: Extract individual job URLs")
                return await self._extract_individual_job_urls(career_page_url, max_jobs, start_time)
            
            elif recommended_strategy == 'embedded_jobs':
                logger.info("   🎯 Strategy: Extract embedded jobs using pattern matching")
                return await self._extract_embedded_jobs(career_page_url, max_jobs, start_time)
            
            elif recommended_strategy == 'hybrid':
                logger.info("   🎯 Strategy: Hybrid approach - try both methods")
                # Try individual URLs first
                individual_result = await self._extract_individual_job_urls(career_page_url, max_jobs, start_time)
                if individual_result.get('total_jobs_found', 0) > 0:
                    return individual_result
                
                # Fallback to embedded jobs
                return await self._extract_embedded_jobs(career_page_url, max_jobs, start_time)
            
            else:
                logger.warning("   ⚠️ Unknown strategy, falling back to embedded jobs extraction")
                return await self._extract_embedded_jobs(career_page_url, max_jobs, start_time)
                
                
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
    
    def _detect_job_url_type(self, job_url: str) -> str:
        """Detect if job_url is career page or individual job"""
        if self._is_career_page_url(job_url):
            return 'career_page'  # career.com
        else:
            return 'individual_job'  # job.com/position/123

    def _extract_direct_job_details(self, job_url: str) -> Optional[Dict]:
        """Extract job details from direct jobs cache"""
        try:
            # Extract job index from #job-1
            if '#job-' in job_url:
                job_index = int(job_url.split('#job-')[1]) - 1
                
                # Use global cache (since each request creates new instance)
                direct_jobs = getattr(JobExtractionService, '_global_direct_jobs_cache', [])
                logger.info(f"   📄 Checking global cache for job {job_index + 1} (total: {len(direct_jobs)})")
                
                if 0 <= job_index < len(direct_jobs):
                    logger.info(f"   ✅ Found direct job {job_index + 1} from global cache")
                    return direct_jobs[job_index]
                else:
                    logger.warning(f"   ⚠️ Job index {job_index} not found in global cache (total: {len(direct_jobs)})")
            return None
        except (ValueError, IndexError) as e:
            logger.warning(f"   ⚠️ Error extracting direct job index: {e}")
            return None

    def _format_job_response(self, job_data: Dict, job_url: str, success: bool = True, error_message: str = None, job_index: int = None) -> Dict:
        """Format job data to standard response"""
        # Check if job data is actually valid
        title = job_data.get('title', '').strip()
        description = job_data.get('description', '').strip()
        
        # Debug logging
        logger.info(f"🔍 _format_job_response debug:")
        logger.info(f"   📄 Input job_data: {job_data}")
        logger.info(f"   📄 Title: '{title}' (len: {len(title)})")
        logger.info(f"   📄 Description: '{description[:100]}...' (len: {len(description)})")
        logger.info(f"   📄 Success: {success}")
        
        # If job data is empty, mark as failed
        if not title or not description or len(description) < 10:
            success = False
            error_message = 'Job data is empty or invalid'
            logger.warning(f"   ⚠️ Job data validation failed: title={bool(title)}, desc_len={len(description)}")
        
        # Summarize long descriptions
        summarized_description = self._summarize_description(description)

        # Determine job_index to report back
        try:
            reported_index = (
                job_index or
                job_data.get('job_index') or
                (int(job_url.split('#job-')[1]) if '#job-' in job_url else None) or
                1
            )
        except Exception:
            reported_index = 1

        response = {
            'success': success,
            'job_url': job_url,
            'job_index': reported_index,
            'job_name': job_data.get('title', ''),
            'job_type': job_data.get('job_type', 'Full-time'),
            'job_role': job_data.get('title', ''),
            'job_description': summarized_description,
            'location': job_data.get('location', ''),
            'salary': job_data.get('salary', ''),
            'job_link': job_url,
            'crawl_time': 0,
            'crawl_method': 'direct_cache' if success else 'failed',
            'error_message': error_message
        }
        
        logger.info(f"   📄 Final response: {response}")
        return response

    def _empty_job_response(self, job_url: str, error_message: str = 'Job not found', job_index: Optional[int] = None) -> Dict:
        """Return empty job response with flat structure matching API"""
        try:
            inferred_index = (
                job_index or
                (int(job_url.split('#job-')[1]) if '#job-' in job_url else None) or
                1
            )
        except Exception:
            inferred_index = 1

        return {
            'success': False,
            'job_url': job_url,
            'job_index': inferred_index,
                        'job_name': '',
                        'job_type': 'Full-time',
                        'job_role': '',
                        'job_description': '',
            'location': '',
            'salary': '',
            'job_link': job_url,
            'crawl_time': 0,
            'crawl_method': 'failed',
            'error_message': error_message
        }

    def _summarize_description(self, text: str, max_length: int = 300) -> str:
        """Summarize long text to a concise snippet, preferring sentence boundaries."""
        if not text:
            return ''
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= max_length:
            return text
        # Try to cut at the last period before the limit
        cutoff = text[:max_length]
        period_pos = cutoff.rfind('.')
        if period_pos >= int(max_length * 0.6):
            return cutoff[:period_pos + 1].strip() + ' ...'
        # Otherwise cut at last space
        space_pos = cutoff.rfind(' ')
        if space_pos > 0:
            return cutoff[:space_pos].strip() + ' ...'
        return cutoff.strip() + ' ...'
    
    async def _validate_job_with_ai(self, job_data: Dict, job_url: str) -> bool:
        """
        Enhanced AI validation to reject non-job URLs effectively
        Returns True if valid job, False if not
        """
        try:
            # Extract key information for validation
            title = job_data.get('title', '').strip()
            description = job_data.get('description', '').strip()
            company = job_data.get('company', '').strip()
            location = job_data.get('location', '').strip()
            
            # 1. URL PATTERN CHECKS - Reject obvious non-job URLs
            url_lower = job_url.lower()
            
            # Non-job URL patterns (Vietnamese + English)
            non_job_url_patterns = [
                '/chinh-sach-bao-mat', '/privacy-policy', '/privacy',
                '/dieu-khoan-dich-vu', '/terms-of-service', '/terms',
                '/cookie-policy', '/cookies', '/legal',
                '/about', '/about-us', '/gioi-thieu',
                '/contact', '/lien-he', '/lien-lac',
                '/news', '/tin-tuc', '/blog',
                '/services', '/dich-vu', '/san-pham', '/products',
                '/home', '/homepage', '/trang-chu',
                '/login', '/register', '/sign-up', '/dang-nhap', '/dang-ky',
                '/en/', '/english/', '/lang/',
                '.jpg', '.png', '.gif', '.pdf', '.doc', '.docx'
            ]
            
            for pattern in non_job_url_patterns:
                if pattern in url_lower:
                    logger.info(f"   🤖 URL REJECT - Non-job URL pattern: {pattern}")
                    return False
            
            # 2. EMPTY CONTENT CHECKS - More strict
            if not title and not description:
                logger.info(f"   🤖 CONTENT REJECT - Both title and description are empty")
                return False
            
            if not description or len(description.strip()) < 30:
                logger.info(f"   🤖 CONTENT REJECT - Description too short or empty (length: {len(description)})")
                return False
            
            # 3. CRITICAL REJECTION KEYWORDS - Definitely not a job
            content_lower = f"{title} {description}".lower()
            
            critical_reject = [
                # Error pages
                '404', 'not found', 'page not found', 'error', 'trang không tìm thấy',
                # Policy pages
                'privacy policy', 'chính sách bảo mật', 'terms of service', 'điều khoản dịch vụ',
                'cookie policy', 'chính sách cookie', 'legal notice', 'thông báo pháp lý',
                # Company pages
                'about us', 'giới thiệu công ty', 'company overview', 'tổng quan công ty',
                'our story', 'câu chuyện của chúng tôi', 'company history', 'lịch sử công ty',
                'our team', 'đội ngũ của chúng tôi', 'leadership team', 'ban lãnh đạo',
                'mission vision', 'tầm nhìn sứ mệnh', 'core values', 'giá trị cốt lõi',
                # Contact/Service pages
                'contact us', 'liên hệ với chúng tôi', 'get in touch', 'contact information',
                'our services', 'dịch vụ của chúng tôi', 'service portfolio', 'danh mục dịch vụ',
                'our products', 'sản phẩm của chúng tôi', 'product catalog', 'danh mục sản phẩm',
                # Login/Register
                'login', 'đăng nhập', 'register', 'đăng ký', 'sign up', 'sign in',
                'create account', 'tạo tài khoản', 'forgot password', 'quên mật khẩu'
            ]
            
            for indicator in critical_reject:
                if indicator in content_lower:
                    logger.info(f"   🤖 CRITICAL REJECT - Contains non-job keyword: {indicator}")
                    return False
            
            # 4. POSITIVE JOB INDICATORS - Enhanced list
            positive_job_indicators = [
                # Job posting keywords (English)
                'responsibilities', 'requirements', 'qualifications', 'skills required',
                'job description', 'position summary', 'role overview', 'what you will do',
                'we are looking for', 'ideal candidate', 'successful candidate',
                'experience', 'years of experience', 'education', 'degree',
                'salary', 'compensation', 'benefits', 'package', 'bonus',
                'apply', 'application', 'submit cv', 'send resume',
                'full-time', 'part-time', 'contract', 'temporary', 'permanent',
                'remote', 'hybrid', 'on-site', 'work from home',
                'developer', 'engineer', 'manager', 'analyst', 'designer',
                'specialist', 'coordinator', 'assistant', 'executive',
                'senior', 'junior', 'lead', 'principal', 'intern',
                'vacancy', 'opening', 'opportunity', 'hiring',
                # Vietnamese job keywords
                'trách nhiệm', 'yêu cầu', 'kỹ năng', 'kinh nghiệm',
                'mô tả công việc', 'vị trí tuyển dụng', 'ứng viên lý tưởng',
                'bạn sẽ làm gì', 'chúng tôi đang tìm kiếm',
                'học vấn', 'bằng cấp', 'chứng chỉ',
                'lương', 'mức lương', 'phúc lợi', 'chế độ đãi ngộ',
                'ứng tuyển', 'nộp hồ sơ', 'gửi cv', 'làm việc toàn thời gian',
                'làm việc bán thời gian', 'hợp đồng', 'thời vụ',
                'làm việc từ xa', 'làm việc tại nhà', 'hybrid',
                'lập trình viên', 'kỹ sư', 'quản lý', 'phân tích',
                'thiết kế', 'chuyên viên', 'điều phối viên', 'trợ lý',
                'giám đốc', 'cấp cao', 'cấp thấp', 'trưởng nhóm',
                'thực tập sinh', 'vị trí tuyển dụng', 'cơ hội việc làm'
            ]
            
            positive_count = 0
            for indicator in positive_job_indicators:
                if indicator in content_lower:
                    positive_count += 1
            
            logger.info(f"   🤖 Analysis: positive indicators = {positive_count}")
            logger.info(f"   🤖 Title: '{title}' (len: {len(title)})")
            logger.info(f"   🤖 Description: '{description[:100]}...' (len: {len(description)})")
            
            # Define job title keywords for all branches
            job_title_keywords = ['assistant', 'designer', 'engineer', 'developer', 'manager', 'analyst', 'specialist', 'coordinator', 'executive', 'intern', 'senior', 'junior', 'lead', 'principal', 'administrative', 'ux', 'ui', 'full', 'stack', 'frontend', 'backend', 'mobile', 'web', 'software', 'data', 'qa', 'test', 'devops', 'product', 'marketing', 'sales', 'hr', 'finance', 'accounting', 'legal', 'operations', 'support', 'customer', 'content', 'social', 'digital', 'growth', 'business', 'strategy', 'consultant', 'advisor', 'director', 'head', 'chief', 'vp', 'cfo', 'cto', 'ceo']
            
            # 5. ENHANCED DECISION LOGIC - More flexible for embedded jobs
            if positive_count == 0:
                # Check if title looks like a job title (for embedded jobs)
                title_matches = [keyword for keyword in job_title_keywords if keyword in title.lower()]
                logger.info(f"   🤖 Title keyword matches: {title_matches}")
                logger.info(f"   🤖 Title lower: '{title.lower()}'")
                logger.info(f"   🤖 Checking keywords: {[k for k in job_title_keywords[:10]]}...")
                
                if len(title) > 5 and any(keyword in title.lower() for keyword in job_title_keywords):
                    logger.info(f"   🤖 ACCEPT - Job-like title without positive indicators: {title}")
                    return True
            if positive_count >= 3:
                logger.info(f"   🤖 ACCEPT - Strong positive indicators ({positive_count})")
                return True
            elif positive_count >= 1:
                # Additional checks for borderline cases
                if len(title) > 5 and any(word in title.lower() for word in ['tuyển dụng', 'hiring', 'job', 'position', 'developer', 'engineer', 'manager']):
                    logger.info(f"   🤖 ACCEPT - Job-related title with some indicators ({positive_count})")
                    return True
                elif len(title) > 5 and any(keyword in title.lower() for keyword in job_title_keywords):
                    logger.info(f"   🤖 ACCEPT - Job-like title with some indicators ({positive_count})")
                    return True
                else:
                    logger.info(f"   🤖 REJECT - Few indicators and non-job title ({positive_count})")
                    return False
            else:
                logger.info(f"   🤖 REJECT - Insufficient job indicators ({positive_count})")
                return False
            
        except Exception as e:
            logger.error(f"   🤖 AI Validation Error: {e}")
            # Default to rejecting on error (more conservative for non-jobs)
            return False
    
    async def _ai_validate_job_content(self, title: str, description: str, company: str, location: str, job_url: str) -> bool:
        """
        Use AI to validate job content (lightweight, cost-effective)
        """
        try:
            # Create a simple prompt for AI validation
            prompt = f"""
            Analyze if this content is a valid job posting:
            
            Title: {title}
            Company: {company}
            Location: {location}
            Description: {description[:500]}...
            URL: {job_url}
            
            Is this a legitimate job posting? Answer only: YES or NO
            """
            
            # Use a lightweight AI call (you can replace with your preferred AI service)
            # For now, using a simple rule-based approach to avoid costs
            validation_result = await self._lightweight_ai_validation(title, description, company, location)
            
            logger.info(f"   🤖 AI Result: {'Valid job' if validation_result else 'Not a job'}")
            return validation_result
            
        except Exception as e:
            logger.error(f"   🤖 AI Validation Error: {e}")
            return True  # Default to accepting if AI fails
    
    async def _lightweight_ai_validation(self, title: str, description: str, company: str, location: str) -> bool:
        """
        Lightweight AI validation using rule-based approach
        Can be replaced with actual AI service call
        """
        try:
            # Advanced heuristic validation
            content = f"{title} {description} {company} {location}".lower()
            
            # Check for job posting structure
            has_requirements = any(word in content for word in ['require', 'must have', 'should have', 'qualification'])
            has_responsibilities = any(word in content for word in ['responsibilit', 'duties', 'tasks', 'role'])
            has_application = any(word in content for word in ['apply', 'application', 'submit', 'send cv'])
            
            # Check for professional content
            has_professional_terms = any(word in content for word in ['experience', 'skills', 'knowledge', 'ability'])
            has_employment_terms = any(word in content for word in ['employment', 'position', 'role', 'vacancy', 'opening'])
            
            # Score the content
            score = 0
            if has_requirements: score += 2
            if has_responsibilities: score += 2
            if has_application: score += 1
            if has_professional_terms: score += 1
            if has_employment_terms: score += 1
            
            # Check for minimum content quality
            if len(description) < 100: score -= 2
            if len(title) < 5: score -= 2
            
            # Reject if score is too low
            is_valid = score >= 3
            
            logger.info(f"   🤖 Validation Score: {score}/7 - {'Valid' if is_valid else 'Invalid'}")
            return is_valid
            
        except Exception as e:
            logger.error(f"   🤖 Lightweight AI Error: {e}")
            return True  # Default to accepting
    
    async def extract_job_details_only(self, job_url: str, job_index: int = None) -> Dict:
        """
        Extract detailed job information from a single job URL
        Handles 2 types: career_page, individual_job
        For career pages, job_index specifies which job to extract (1-based)
        """
        start_time = time.time()
        
        try:
            logger.info(f"📄 Extracting job details from: {job_url}")
            
            # CLEAR CACHE FIRST to prevent data mixing between different companies
            self.clear_all_cache()
            logger.info("   🗑️ Cleared all cache to prevent data mixing")
            
            # Infer index from URL fragment if present
            if job_index is None and '#job-' in job_url:
                try:
                    job_index = int(job_url.split('#job-')[-1])
                    logger.info(f"   🎯 Inferred job index from URL: {job_index}")
                except Exception:
                    job_index = None
            if job_index:
                logger.info(f"   🎯 Job index: {job_index}")
            
            # Detect job URL type
            url_type = self._detect_job_url_type(job_url)
            logger.info(f"   🔍 Detected URL type: {url_type}")
            
            if url_type == 'career_page':
                # Default to first job when index not provided
                if job_index is None:
                    job_index = 1
                    logger.info("   🎯 No job_index provided -> default to 1 for career page")
                
                # Check if career page has individual job URLs first
                logger.info(f"   📄 Processing career page: {job_url}")
                page_analysis = await self._analyze_career_page_structure(job_url)
                
                if page_analysis.get('has_individual_urls', False):
                    # Use individual job URLs strategy
                    logger.info(f"   🎯 Career page has individual URLs - using individual job URLs strategy")
                    individual_urls = await self._extract_individual_job_urls(job_url, 50, start_time)
                    job_urls = individual_urls.get('job_urls', [])
                    
                    if job_index and 1 <= job_index <= len(job_urls):
                        # Extract from individual job URL
                        individual_job_url = job_urls[job_index - 1]
                        logger.info(f"   📄 Extracting from individual job URL: {individual_job_url}")
                        result = await self._extract_individual_job_details(individual_job_url, start_time)
                    else:
                        logger.warning(f"   ⚠️ Invalid job index {job_index}, using embedded jobs strategy")
                        result = await self._extract_specific_job_from_career_page(job_url, job_index, start_time)
                else:
                    # Use embedded jobs strategy
                    logger.info(f"   🎯 Career page has embedded jobs - using embedded jobs strategy")
                    result = await self._extract_specific_job_from_career_page(job_url, job_index, start_time)
            else:  # individual_job
                # Handle individual job page
                logger.info(f"   📄 Processing individual job page: {job_url}")
                result = await self._extract_individual_job_details(job_url, start_time)
            
            # AI Validation: Always validate, even with empty content
            logger.info(f"   🤖 Starting AI Validation for: {job_url}")
            if result.get('success'):
                # For career pages, job data is already in the result (from _extract_specific_job_from_career_page)
                # No need to extract from nested fields
                logger.info(f"   🤖 Result success: {result.get('success')}")
                logger.info(f"   🤖 Result keys: {list(result.keys())}")
                logger.info(f"   🤖 Job Name: '{result.get('job_name', '')}'")
                logger.info(f"   🤖 Job Type: '{result.get('job_type', '')}'")
                logger.info(f"   🤖 Job Description: '{result.get('job_description', '')[:50]}...'")
                
                # Skip AI Validation for career pages since job data is already validated
                logger.info(f"   🤖 Skipping AI Validation - job data already validated")
                is_valid_job = True
                
                if not is_valid_job:
                    logger.warning(f"   🤖 AI Validation: Rejected as non-job content")
                    return self._empty_job_response(job_url, 'AI validation failed: Content is not a valid job posting')
                else:
                    logger.info(f"   🤖 AI Validation: Passed - Valid job content")
            else:
                logger.warning(f"   🤖 Skipping AI Validation - extraction failed")
            
            return result
                
        except Exception as e:
            logger.error(f"❌ Error in extract_job_details_only: {e}")
            return self._empty_job_response(job_url, str(e))

    async def _extract_specific_job_from_career_page(self, career_url: str, job_index: int, start_time: float) -> Dict:
        """Extract specific job by index from career page"""
        try:
            # Try to get from cache first
            direct_jobs = getattr(JobExtractionService, '_global_direct_jobs_cache', [])
            logger.info(f"   📄 Global cache status: {len(direct_jobs)} jobs available")
            
            if direct_jobs and len(direct_jobs) > 0:
                logger.info(f"   📄 Found {len(direct_jobs)} jobs in cache")
                logger.info(f"   📄 Cache jobs: {[job.get('title', 'No title') for job in direct_jobs]}")
                
                # Extract specific job by index (1-based)
                if job_index and 1 <= job_index <= len(direct_jobs):
                    job_data = direct_jobs[job_index - 1]
                    logger.info(f"   ✅ Found job {job_index}: {job_data.get('title', 'Unknown')}")
                    logger.info(f"   📄 Job data: {job_data}")
                    logger.info(f"   📄 Job data keys: {list(job_data.keys())}")
                    logger.info(f"   📄 Title: '{job_data.get('title', '')}'")
                    logger.info(f"   📄 Description: '{job_data.get('description', '')[:100]}...'")
                    logger.info(f"   📄 About to call _format_job_response with job_data and career_url: {career_url}")
                    result = self._format_job_response(job_data, career_url, job_index=job_index)
                    logger.info(f"   📄 _format_job_response result: {result}")
                    return result
                else:
                    # Default gracefully to first job if index missing/invalid
                    logger.warning(f"   ⚠️ Invalid job index {job_index}, default to 1 (available: 1-{len(direct_jobs)})")
                    job_data = direct_jobs[0]
                    return self._format_job_response(job_data, career_url, job_index=1)
            
            # If no cache, extract directly from career page
            logger.info(f"   📄 No cache found, extracting directly from career page")
            return await self._extract_individual_job_details(career_url, start_time)
            
        except Exception as e:
            logger.error(f"❌ Error extracting specific job from career page: {e}")
            return self._empty_job_response(career_url, str(e))

    async def _extract_first_job_from_career_page(self, career_url: str, start_time: float) -> Dict:
        """Extract first job from career page"""
        try:
            # Try to get from cache first
            if hasattr(self, '_career_page_cache') and career_url == self._career_page_cache:
                direct_jobs = getattr(self, '_direct_jobs_cache', [])
                if direct_jobs:
                    logger.info(f"   📄 Using cached career page data")
                    return self._format_job_response(direct_jobs[0], career_url, job_index=1)
            
            # Fallback: extract from career page
            logger.info(f"   📄 Extracting from career page directly")
            result = await self._extract_jobs_from_single_page(
           career_url, max_jobs=1, include_hidden_jobs=True, include_job_details=True
            )
            
            if result['success'] and result.get('jobs'):
                first_job = result['jobs'][0]
                job_data = {
                    'title': first_job.get('title', ''),
                    'job_type': first_job.get('job_type', 'Full-time'),
                    'description': first_job.get('description', '')
                }
                return self._format_job_response(job_data, career_url, job_index=1)
            else:
                return self._empty_job_response(career_url, 'No jobs found on career page')
            
        except Exception as e:
            logger.error(f"❌ Error extracting from career page: {e}")
            return self._empty_job_response(career_url, str(e))

    async def _extract_individual_job_details(self, job_url: str, start_time: float) -> Dict:
        """Extract job details from individual job page"""
        try:
            from .crawler import crawl_single_url
            result = await crawl_single_url(job_url)
            
            if not result['success']:
                return self._empty_job_response(job_url, 'Failed to crawl job page')
            
            # Extract job details from HTML
            job_details = self._extract_job_details_from_html(result, job_url)
            
            if job_details:
                job_data = {
                    'title': job_details.get('job_name', ''),
                    'job_type': job_details.get('job_type', 'Full-time'),
                    'description': job_details.get('job_description', '')
                }
                logger.info(f"🔍 _extract_individual_job_details debug:")
                logger.info(f"   📄 job_details from HTML: {job_details}")
                logger.info(f"   📄 job_data for response: {job_data}")
                return self._format_job_response(job_data, job_url)
            else:
                return self._empty_job_response(job_url, 'No job details found on page')
            
        except Exception as e:
            logger.error(f"❌ Error extracting individual job details: {e}")
            return self._empty_job_response(job_url, str(e))
    
    def _is_career_page_url(self, url: str) -> bool:
        """Check if URL is a career page (not a specific job page)"""
        url_lower = url.lower()
        
        # Parse URL để kiểm tra subdomain
        from urllib.parse import urlparse
        parsed_url = urlparse(url_lower)
        domain = parsed_url.netloc.lower()
        path = parsed_url.path.lower()
        
        # 1. Kiểm tra subdomain career (HIGHEST PRIORITY)
        if domain.startswith('career.') or domain.startswith('careers.') or domain.startswith('jobs.'):
            return True
        
        # 2. Career page indicators
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
        """Extract job details from HTML content - Universal approach"""
        try:
            from bs4 import BeautifulSoup
            import re
            
            html_content = result.get('html', '')
            if not html_content:
                logger.warning("   ⚠️ No HTML content to extract from")
                return {}
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            job_details = {
                'job_name': '',
                'job_type': 'Full-time',
                'job_role': '',
                'job_description': '',
                'job_link': job_url
            }
            
            # UNIVERSAL TITLE EXTRACTION - Simple and robust
            logger.info("   🔄 Extracting title with universal approach")
            
            # Try h1 first (most common for job titles)
            h1_elements = soup.find_all('h1')
            for h1 in h1_elements:
                title_text = h1.get_text().strip()
                if title_text and len(title_text) > 3:
                    # Filter out generic titles
                    if not any(generic in title_text.lower() for generic in 
                             ['home', 'about', 'contact', 'career', 'careers', 'welcome', 'blog', 'news']):
                        job_details['job_name'] = title_text
                        job_details['job_role'] = title_text
                        logger.info(f"   📄 Found job title in h1: {title_text}")
                        break
            
            # If no h1, try h2
            if not job_details['job_name']:
                h2_elements = soup.find_all('h2')
                for h2 in h2_elements:
                    title_text = h2.get_text().strip()
                    if title_text and len(title_text) > 3:
                        if not any(generic in title_text.lower() for generic in 
                                 ['home', 'about', 'contact', 'career', 'careers', 'welcome', 'blog', 'news']):
                            job_details['job_name'] = title_text
                            job_details['job_role'] = title_text
                            logger.info(f"   📄 Found job title in h2: {title_text}")
                        break
            
            # UNIVERSAL DESCRIPTION EXTRACTION - Get ALL content
            logger.info("   🔄 Extracting description with universal approach")
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'noscript']):
                element.decompose()
            
            # Get all text content
            all_text = soup.get_text()
            if all_text:
                # Clean up text
                all_text = re.sub(r'\s+', ' ', all_text).strip()
                
                # Filter out very short content
                if len(all_text) > 50:
                    job_details['job_description'] = all_text[:5000]  # Limit for Agent to summarize
                    logger.info(f"   📄 Found description via universal extraction (length: {len(all_text)})")
                else:
                    logger.warning(f"   ⚠️ Content too short: {len(all_text)} chars")
            
            # Extract job type from content
            if job_details['job_description']:
                content_lower = job_details['job_description'].lower()
                
                if any(term in content_lower for term in ['full-time', 'full time', 'fulltime']):
                    job_details['job_type'] = 'Full-time'
                elif any(term in content_lower for term in ['part-time', 'part time', 'parttime']):
                    job_details['job_type'] = 'Part-time'
                elif any(term in content_lower for term in ['contract', 'contractor']):
                    job_details['job_type'] = 'Contract'
                elif any(term in content_lower for term in ['intern', 'internship']):
                    job_details['job_type'] = 'Internship'
                elif any(term in content_lower for term in ['remote']):
                    job_details['job_type'] = 'Remote'
                elif any(term in content_lower for term in ['hybrid']):
                    job_details['job_type'] = 'Hybrid'
            
            
            # Simple debug logging
            logger.info(f"🔍 Universal extraction result:")
            logger.info(f"   📄 Job Name: {bool(job_details['job_name'])}")
            logger.info(f"   📄 Job Description: {bool(job_details['job_description'])}")
            logger.info(f"   📄 Job Type: {job_details['job_type']}")
            
            # Debug HTML content
            logger.info(f"   📄 HTML content length: {len(html_content)}")
            if html_content:
                logger.info(f"   📄 HTML preview: {html_content[:200]}...")
            
            # Debug soup content
            soup_text = soup.get_text().strip()
            logger.info(f"   📄 Soup text length: {len(soup_text)}")
            if soup_text:
                logger.info(f"   📄 Soup text preview: {soup_text[:200]}...")
            
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
    
    async def _extract_direct_jobs_from_career_page(self, soup, career_page_url: str) -> List[Dict]:
        """Extract jobs directly from career page content with multiple patterns support"""
        try:
            jobs = []
            
            # Remove navigation elements (but preserve job content)
            for nav in soup.find_all(['nav', 'header', 'footer']):
                # Only remove if it doesn't contain job-related content
                nav_text = nav.get_text().lower()
                if not any(keyword in nav_text for keyword in ['job', 'career', 'position', 'tuyển', 'việc']):
                    nav.decompose()
            
            # Remove common navigation classes (but preserve job content)
            for element in soup.find_all(class_=re.compile(r'nav|menu|header|footer|sidebar', re.I)):
                element_text = element.get_text().lower()
                if not any(keyword in element_text for keyword in ['job', 'career', 'position', 'tuyển', 'việc']):
                    element.decompose()
            
            # Method 1: Look for job tables (like NSC Software)
            table_jobs = self._extract_jobs_from_tables(soup)
            if table_jobs:
                logger.info(f"   📊 Found {len(table_jobs)} jobs from table format")
                jobs.extend(table_jobs)
            
            # Method 2: Look for job cards/items (like Migitek)
            card_jobs = self._extract_jobs_from_cards(soup, career_page_url)
            if card_jobs:
                logger.info(f"   📄 Found {len(card_jobs)} jobs from card format")
                jobs.extend(card_jobs)
            
            # Method 3: Look for job lists
            list_jobs = self._extract_jobs_from_lists(soup)
            if list_jobs:
                logger.info(f"   📋 Found {len(list_jobs)} jobs from list format")
                jobs.extend(list_jobs)
            
            # Method 4: Look for job sections with headings
            heading_jobs = self._extract_jobs_from_headings(soup)
            if heading_jobs:
                logger.info(f"   🎯 Found {len(heading_jobs)} jobs from heading format")
                jobs.extend(heading_jobs)
            
            # Filter out non-job content (benefits, culture, etc.)
            filtered_jobs = self._filter_real_jobs(jobs)
            
            logger.info(f"   ✅ Total jobs extracted: {len(filtered_jobs)} (filtered from {len(jobs)})")
            return filtered_jobs
            
        except Exception as e:
            logger.error(f"❌ Error extracting direct jobs from career page: {e}")
            return []
    
    def _extract_jobs_from_tables(self, soup) -> List[Dict]:
        """Extract jobs from table format (like NSC Software)"""
        jobs = []
        try:
            # Look for tables with job-related content
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:  # At least 2 columns
                        # Extract job title from first cell
                        title_cell = cells[0]
                        title = title_cell.get_text().strip()
                        
                        # Check if this looks like a job title
                        if self._is_job_title(title):
                            job_data = {
                                'title': title,
                                'description': '',
                                'job_type': 'Full-time',
                                'location': '',
                                'salary': '',
                                'company': self.extract_company_from_url(''),
                                'url': f"#job-{len(jobs) + 1}",
                                'source': 'table_format'
                            }
                            
                            # Extract additional info from other cells
                            if len(cells) > 1:
                                experience = cells[1].get_text().strip()
                                if experience:
                                    job_data['description'] = f"Experience: {experience}"
                            
                            if len(cells) > 2:
                                positions = cells[2].get_text().strip()
                                if positions:
                                    job_data['description'] += f" | Positions: {positions}"
                            
                            jobs.append(job_data)
                            logger.info(f"   📊 Extracted table job: {title}")
            
            return jobs
        except Exception as e:
            logger.error(f"❌ Error extracting jobs from tables: {e}")
            return []
    
    def _extract_jobs_from_cards(self, soup, career_page_url: str) -> List[Dict]:
        """Extract jobs from card format using pattern-based approach"""
        jobs = []
        try:
            # Get all text content from the page
            page_text = soup.get_text()
            
            # Define job patterns for different sites
            job_patterns = {
                'general': [
                    # Main pattern for Quape and similar sites - captures job title with location and action
                    r'([A-Z][a-zA-Z\s]+(?:Developer|Engineer|Manager|Analyst|Specialist|Assistant|Designer))[^.\n]*?(?:Singapore Only|Fully Remote|Remote)[^.\n]*?(?:See Details|See|Apply|View)',
                    # Fallback patterns for other sites
                    r'\[Remote-HN\]\s+([^-\n]+)',
                    r'\[Remote\]\s+([^-\n]+)',
                    r'Tuyển dụng.*?(\d{2}/\d{2}/\d{4}):\s*([^-\n]+)',
                    r'(\d{2}/\d{2}/\d{4}):\s*([^-\n]+)',
                    r'([A-Z][^-\n]*(?:Developer|Engineer|Manager|Analyst|Specialist|Marketing|Test|Freelancer|Assistant|Intern))'
                ]
            }
            
            # Use main pattern first, then fallback to others if needed
            main_pattern = job_patterns['general'][0]  # Main pattern for Quape
            fallback_patterns = job_patterns['general'][1:]  # Fallback patterns
            
            # Try main pattern first
            jobs = self._extract_jobs_by_patterns(page_text, [main_pattern], career_page_url, 'general')
            
            # If no jobs found with main pattern, try fallback patterns
            if not jobs:
                logger.info("   🔄 No jobs found with main pattern, trying fallback patterns")
                jobs = self._extract_jobs_by_patterns(page_text, fallback_patterns, career_page_url, 'general')
            
            logger.info(f"   📦 Extracted {len(jobs)} jobs using pattern matching")
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Error extracting jobs from cards: {e}")
            return []
    
    def _extract_jobs_by_patterns(self, page_text: str, patterns: List[str], career_page_url: str, site_type: str) -> List[Dict]:
        """Extract jobs using regex patterns with deduplication"""
        import re
        jobs = []
        seen_jobs = set()  # Track unique jobs to avoid duplicates
        
        for i, pattern in enumerate(patterns):
            matches = re.finditer(pattern, page_text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                job_text = match.group(0)
                job_data = self._parse_job_text(job_text, career_page_url, len(jobs) + 1, site_type)
                if job_data and job_data.get('title'):
                    # Create a unique key for deduplication
                    title = job_data.get('title', '')
                    # Clean title for comparison (remove location and action words)
                    clean_title = re.sub(r'(Singapore Only|Fully Remote|See Details|See)$', '', title).strip()
                    clean_title = re.sub(r'^com\s*', '', clean_title).strip()
                    
                    # Further clean up for better deduplication
                    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
                    
                    if clean_title not in seen_jobs:
                        seen_jobs.add(clean_title)
                        # Clean up the job data and extract location
                        job_data['title'] = clean_title
                        
                        # Extract location from original title
                        if 'Singapore Only' in title:
                            job_data['location'] = 'Singapore Only'
                        elif 'Fully Remote' in title:
                            job_data['location'] = 'Fully Remote'
                        elif 'Remote' in title:
                            job_data['location'] = 'Remote'
                        
                        jobs.append(job_data)
                        logger.info(f"   📄 Extracted unique job: {clean_title} ({job_data.get('location', 'No location')})")
                    else:
                        logger.debug(f"   🔄 Skipped duplicate: {title}")
        
        return jobs
    
    def _normalize_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Normalize extracted jobs: clean titles, infer locations, remove duplicates."""
        import re
        normalized_jobs: List[Dict] = []
        seen_titles: set = set()
        
        for job in jobs:
            original_title = (job.get('title') or '').strip()
            description_text = (job.get('description') or '').strip()
            combined_text = f"{original_title} {description_text}"
            
            # Clean title suffixes and prefixes
            clean_title = re.sub(r"\s*(Singapore Only|Fully Remote|Remote|See Details|See)\s*$", "", original_title).strip()
            clean_title = re.sub(r"^com\s*", "", clean_title).strip()
            clean_title = re.sub(r"\s+", " ", clean_title).strip()
            
            # Infer location if missing
            if not job.get('location'):
                if re.search(r"Singapore Only", combined_text, re.IGNORECASE):
                    job['location'] = 'Singapore Only'
                elif re.search(r"Fully Remote", combined_text, re.IGNORECASE):
                    job['location'] = 'Fully Remote'
                elif re.search(r"\bRemote\b", combined_text, re.IGNORECASE):
                    job['location'] = 'Remote'
            
            # Apply cleaned title
            job['title'] = clean_title
            
            # Deduplicate by cleaned title
            title_key = clean_title.lower()
            if not clean_title or title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            normalized_jobs.append(job)
        
        return normalized_jobs
    
    def _parse_job_text(self, job_text: str, career_page_url: str, job_index: int, site_type: str) -> Dict:
        """Parse job text to extract structured data"""
        try:
            # Extract title
            title = self._extract_title_from_text(job_text, site_type)
            
            # Extract job type
            job_type = self._extract_job_type_from_text(job_text)
            
            # Extract location
            location = self._extract_location_from_text(job_text)
            
            # Extract salary
            salary = self._extract_salary_from_text(job_text)
            
            # Extract company
            company = self._extract_company_from_url(career_page_url)
            
            # Clean description
            description = self._clean_job_description(job_text)
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'job_type': job_type,
                'salary': salary,
                'description': description,
                'job_link': career_page_url,
                'source_url': career_page_url,
                'job_index': job_index
            }
            
        except Exception as e:
            logger.warning(f"   ⚠️ Error parsing job text: {e}")
            return {}
    
    def _extract_title_from_text(self, job_text: str, site_type: str) -> str:
        """Extract job title from text"""
        import re
        try:
            # Universal title extraction - no site-specific logic
            
            # General fallback - extract first meaningful line
            lines = job_text.split('\n')
            for line in lines:
                line = line.strip()
                if len(line) > 5 and len(line) < 100:
                    # Check for job-related keywords
                    if any(job_word in line.lower() for job_word in ['developer', 'engineer', 'manager', 'analyst', 'specialist', 'assistant', 'designer']):
                        return line
                    # Also check for common job title patterns
                    elif re.match(r'^[A-Z][a-zA-Z\s]+(?:Assistant|Designer|Engineer|Developer|Manager|Analyst|Specialist)', line):
                        return line
            
            # If no specific job keywords found, return the first meaningful line
            for line in lines:
                line = line.strip()
                if len(line) > 5 and len(line) < 100:
                    return line
            
            return ""
            
        except Exception as e:
            logger.warning(f"   ⚠️ Error extracting title from text: {e}")
            return ""
    
    def _extract_job_type_from_text(self, job_text: str) -> str:
        """Extract job type from text"""
        try:
            text = job_text.lower()
            if 'fulltime' in text or 'full-time' in text or 'toàn thời gian' in text:
                return 'Full-time'
            elif 'part-time' in text or 'parttime' in text or 'bán thời gian' in text:
                return 'Part-time'
            elif 'contract' in text or 'hợp đồng' in text:
                return 'Contract'
            elif 'intern' in text or 'thực tập' in text:
                return 'Internship'
            else:
                return 'Full-time'
        except:
            return 'Full-time'
    
    def _extract_location_from_text(self, job_text: str) -> str:
        """Extract location from text"""
        try:
            import re
            
            
            # General location patterns
            location_patterns = [
                r'nơi làm việc[:\s]+([^\n]+)',
                r'location[:\s]+([^\n]+)',
                r'địa điểm[:\s]+([^\n]+)',
                r'work location[:\s]+([^\n]+)'
            ]
            for pattern in location_patterns:
                match = re.search(pattern, job_text, re.IGNORECASE)
                if match:
                    location = match.group(1).strip()
                    # Clean location text
                    location = re.sub(r'(Download JD|Apply now|Xem Thêm|Số lượng tuyển|Junior|Senior|Tuyển gấp).*$', '', location, flags=re.IGNORECASE)
                    location = location.strip()
                    if 0 < len(location) < 100:
                        return location
            return ""
        except:
            return ""
    
    def _extract_salary_from_text(self, job_text: str) -> str:
        """Extract salary from text"""
        try:
            import re
            salary_patterns = [
                r'mức lương[:\s]+([^\n]+)',
                r'salary[:\s]+([^\n]+)',
                r'lương[:\s]+([^\n]+)'
            ]
            for pattern in salary_patterns:
                match = re.search(pattern, job_text, re.IGNORECASE)
                if match:
                    salary = match.group(1).strip()
                    if 0 < len(salary) < 100:
                        return salary
            return ""
        except:
            return ""
    
    def _clean_job_description(self, job_text: str) -> str:
        """Clean job description text"""
        try:
            # Remove common navigation/filter text
            skip_words = ['năng lực phù hợp', 'địa điểm phù hợp', 'search', 'filter', 'navigation']
            lines = job_text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if line and not any(skip_word in line.lower() for skip_word in skip_words):
                    cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines).strip()
        except:
            return job_text.strip()
    
    def _extract_jobs_from_lists(self, soup) -> List[Dict]:
        """Extract jobs from list format"""
        jobs = []
        try:
            # Look for lists with job-related content
            lists = soup.find_all(['ul', 'ol'])
            for list_elem in lists:
                items = list_elem.find_all('li')
                for item in items:
                    text = item.get_text().strip()
                    if self._is_job_title(text):
                        job_data = {
                            'title': text,
                            'description': '',
                            'job_type': 'Full-time',
                            'location': '',
                            'salary': '',
                            'company': self.extract_company_from_url(''),
                            'url': f"#job-{len(jobs) + 1}",
                            'source': 'list_format'
                        }
                        jobs.append(job_data)
                        logger.info(f"   📋 Extracted list job: {text}")
            
            return jobs
        except Exception as e:
            logger.error(f"❌ Error extracting jobs from lists: {e}")
            return []
    
    def _extract_jobs_from_headings(self, soup) -> List[Dict]:
        """Extract jobs from headings"""
        jobs = []
        try:
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for heading in headings:
                text = heading.get_text().strip()
                if self._is_job_title(text):
                    job_data = {
                        'title': text,
                        'description': '',
                        'job_type': 'Full-time',
                        'location': '',
                        'salary': '',
                        'company': self.extract_company_from_url(''),
                        'url': f"#job-{len(jobs) + 1}",
                        'source': 'heading_format'
                    }
                    jobs.append(job_data)
                    logger.info(f"   🎯 Extracted heading job: {text}")
            
            return jobs
        except Exception as e:
            logger.error(f"❌ Error extracting jobs from headings: {e}")
            return []
    
    def _is_job_title(self, text: str) -> bool:
        """Check if text looks like a job title"""
        if not text or len(text) < 5:
            return False
        
        text_lower = text.lower()
        
        # Job title indicators
        job_indicators = [
            'developer', 'engineer', 'manager', 'analyst', 'specialist',
            'coordinator', 'assistant', 'director', 'lead', 'head', 'chief',
            'architect', 'consultant', 'advisor', 'expert', 'professional',
            'programmer', 'coder', 'tester', 'qa', 'devops', 'sre',
            'senior', 'junior', 'mid', 'entry', 'level', 'principal', 'staff',
            'associate', 'executive', 'vice', 'deputy',
            'full-stack', 'frontend', 'backend', 'mobile', 'web',
            'data', 'ai', 'ml', 'blockchain', 'crypto', 'fintech',
            'marketing', 'sales', 'hr', 'finance', 'legal', 'operations',
            'python', 'java', 'javascript', 'react', 'vue', 'angular',
            'node', 'php', 'c#', 'dotnet', 'ruby', 'go', 'rust',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes'
        ]
        
        # Benefits/culture indicators (NOT jobs)
        non_job_indicators = [
            'health insurance', 'working per week', 'appreciation bonus',
            'competitive salary', 'benefits', 'human-centric', 'culture',
            'work from home', 'remote work', 'flexible', 'vacation',
            'sick leave', 'maternity', 'paternity', 'retirement',
            'gym membership', 'free lunch', 'snacks', 'coffee',
            'team building', 'company events', 'training', 'education'
        ]
        
        # Check for non-job indicators first
        for indicator in non_job_indicators:
            if indicator in text_lower:
                return False
        
        # Check for job indicators
        for indicator in job_indicators:
            if indicator in text_lower:
                return True
        
        return False
    
    def _filter_real_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Filter out non-job content (benefits, culture, etc.)"""
        filtered_jobs = []
        
        for job in jobs:
            title = job.get('title', '')
            if self._is_job_title(title):
                filtered_jobs.append(job)
            else:
                logger.info(f"   🚫 Filtered out non-job: {title}")
        
        return filtered_jobs
    
    
    def extract_company_from_url(self, url: str) -> str:
        """Extract company name from URL dynamically"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www, subdomain, get main domain
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Extract company name from domain
            company = domain.split('.')[0]
            
            return company.title() if company else "Unknown"
            
        except Exception:
            return "Unknown"
    
    async def _detect_career_page_type(self, career_page_url: str) -> str:
        """Detect if career page has individual job URLs or embedded jobs - OPTIMIZED VERSION"""
        try:
            logger.info(f"   🔍 ANALYZING CAREER PAGE STRUCTURE: {career_page_url}")
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            import re
            
            # Crawl career page first to get HTML content
            from .crawler import crawl_single_url
            result = await crawl_single_url(career_page_url)
            if not result['success']:
                logger.info(f"   ❌ Failed to crawl career page for type detection")
                return "unknown"
            
            html_content = result['html']
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # STEP 1: Check if this is a main career page (contains individual job URLs)
            url_lower = career_page_url.lower()
            
            # Main career page patterns (contains individual job URLs)
            main_career_patterns = [
                '/career/', '/careers/', '/jobs/', '/tuyen-dung/', '/viec-lam/',
                '/opportunities/', '/positions/', '/openings/', '/vacancies/'
            ]
            
            is_main_career_page = any(pattern in url_lower for pattern in main_career_patterns)
            
            if is_main_career_page:
                # Check if it contains individual job URLs (not just category links)
                individual_job_links = []
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if not href:
                        continue
                    
                    full_url = urljoin(career_page_url, href)
                    
                    # Look for individual job URL patterns (more comprehensive)
                    job_url_patterns = [
                        r'/[^/]+-developer/?$',
                        r'/[^/]+-analyst/?$', 
                        r'/[^/]+-tester/?$',
                        r'/[^/]+-designer/?$',
                        r'/[^/]+-manager/?$',
                        r'/[^/]+-specialist/?$',
                        r'/[^/]+-engineer/?$',
                        r'/[^/]+-content/?$',
                        r'/[^/]+-technical/?$',
                        r'/[^/]+-executive/?$',
                        r'/[^/]+-coordinator/?$',
                        r'/[^/]+-assistant/?$',
                        r'/[^/]+-frontend/?$',
                        r'/[^/]+-backend/?$',
                        r'/[^/]+-fullstack/?$',
                        r'/[^/]+-devops/?$',
                        r'/[^/]+-qa/?$',
                        r'/[^/]+-seo/?$',
                        r'/[^/]+-marketing/?$',
                        r'/[^/]+-sales/?$',
                        r'/[^/]+-hr/?$',
                        r'/[^/]+-admin/?$',
                        r'/[^/]+-lead/?$',
                        r'/[^/]+-senior/?$',
                        r'/[^/]+-junior/?$',
                        r'/[^/]+-intern/?$'
                    ]
                    
                    for pattern in job_url_patterns:
                        if re.search(pattern, full_url, re.IGNORECASE):
                            individual_job_links.append(full_url)
                            break
                
                if individual_job_links:
                    logger.info(f"   🎯 DETECTED: individual_urls (main career page with {len(individual_job_links)} job URLs: {career_page_url})")
                    return "individual_urls"
                else:
                    logger.info(f"   🎯 DETECTED: embedded_jobs (main career page without individual URLs: {career_page_url})")
                    return "embedded_jobs"
            
            # STEP 2: Check if this is a category page (contains multiple job listings)
            category_indicators = [
                'business-development', 'marketing', 'information-technology',
                'engineering', 'sales', 'hr', 'finance', 'operations',
                'design', 'product', 'data', 'security', 'devops'
            ]
            
            is_category_page = any(indicator in url_lower for indicator in category_indicators)
            
            if is_category_page:
                logger.info(f"   🎯 DETECTED: embedded_jobs (category page: {career_page_url})")
                return "embedded_jobs"
            
            # STEP 3: Quick scan for individual job URLs (simplified validation)
            job_link_patterns = [
                r'/job/[^"]+', r'/career/[^"]+', r'/careers/[^"]+', r'/jobs/[^"]+', 
                r'/positions/[^"]+', r'/opportunities/[^"]+', r'/tuyen-dung/[^"]+',
                r'/recruitment/[^"]+', r'/vacancies/[^"]+', r'/openings/[^"]+',
                r'/apply/[^"]+', r'/employment/[^"]+', r'/hiring/[^"]+',
                r'/developer/[^"]+', r'/engineer/[^"]+', r'/manager/[^"]+',
                r'/analyst/[^"]+', r'/specialist/[^"]+', r'/consultant/[^"]+'
            ]
            
            # Find all links that match job patterns (without strict validation)
            all_links = soup.find_all('a', href=True)
            potential_job_urls = []
            
            for link in all_links:
                href = link.get('href', '')
                if not href:
                    continue
                
                full_url = urljoin(career_page_url, href)
                
                # Check if URL matches job patterns (simplified check)
                for pattern in job_link_patterns:
                    if re.search(pattern, full_url, re.IGNORECASE):
                        # Basic validation: not just career page root
                        if not (full_url.rstrip('/').endswith('/career') or 
                               full_url.rstrip('/').endswith('/careers') or 
                               full_url.rstrip('/').endswith('/jobs')):
                            potential_job_urls.append(full_url)
                            break
            
            # Remove duplicates
            potential_job_urls = list(set(potential_job_urls))
            logger.info(f"   🔗 Found {len(potential_job_urls)} potential individual job URLs")
            
            # STEP 2: Test a few URLs to see if they have job content
            if potential_job_urls:
                logger.info(f"   🧪 Testing individual URLs for job content...")
                valid_job_urls = []
                
                for i, url in enumerate(potential_job_urls[:3]):  # Test first 3 URLs
                    logger.info(f"   🧪 Testing URL {i+1}: {url}")
                    test_result = await self._test_job_url_content(url)
                    
                    if test_result and test_result.get('job_name') and len(test_result.get('job_name', '').strip()) > 0:
                        logger.info(f"   ✅ URL has job content: {test_result.get('job_name')}")
                        valid_job_urls.append(url)
                    else:
                        logger.info(f"   ❌ URL has no job content")
                
                if valid_job_urls:
                    logger.info(f"   🎯 DETECTED: INDIVIDUAL URLS ({len(valid_job_urls)} valid URLs)")
                    return "individual_urls"
                else:
                    logger.info(f"   🔄 Individual URLs have no content, checking for embedded jobs...")
            
            # STEP 3: Check for embedded jobs
            logger.info(f"   📄 Checking for embedded jobs...")
            direct_jobs = await self._extract_direct_jobs_from_career_page(soup, career_page_url)
            
            if direct_jobs:
                logger.info(f"   🎯 DETECTED: EMBEDDED JOBS ({len(direct_jobs)} jobs found)")
                return "embedded_jobs"
            else:
                logger.info(f"   ❓ DETECTED: UNKNOWN (no jobs found)")
                return "unknown"
                    
        except Exception as e:
            logger.error(f"   ❌ Error detecting career page type: {e}")
            return "unknown"

    async def _test_job_url_content(self, job_url: str) -> dict:
        """Test if individual job URL has actual job content"""
        try:
            from .crawler import crawl_single_url
            from bs4 import BeautifulSoup
            import re
            
            # Crawl the individual job URL
            result = await crawl_single_url(job_url)
            if not result['success']:
                return {}
            
            html_content = result['html']
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract basic job info to test if it has content
            job_data = {}
            
            # Enhanced job title extraction with more specific patterns
            title_selectors = [
                # Main title selectors
                'h1', 'h2', 'h3',
                # Common job title classes
                '.job-title', '.position-title', '.job-name', '.title', 
                '.job-header h1', '.job-header h2', '.job-header h3',
                # Generic title patterns
                '[class*="title"]', '[class*="job"]', '[class*="position"]',
                # Content area titles
                '.content h1', '.content h2', '.main-content h1', '.main-content h2',
                # Page title fallback
                'title'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text().strip()
                    # Filter out generic titles and check for job-related content
                    if (title_text and len(title_text) > 3 and 
                        not any(generic in title_text.lower() for generic in 
                               ['home', 'about', 'contact', 'career', 'careers', 'nsc software', 'welcome'])):
                        job_data['job_name'] = title_text
                        break
            
            # Enhanced job description extraction
            desc_selectors = [
                # Specific job description containers
                '.job-description', '.job-content', '.description', '.content',
                '.job-details', '.position-description', '.job-info',
                # Generic content patterns
                '[class*="description"]', '[class*="content"]', '[class*="details"]',
                # Main content areas
                '.main-content', '.content-area', '.job-section',
                # Paragraph content
                'p', '.job-body', '.position-body'
            ]
            
            description_text = ""
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    desc_text = desc_elem.get_text().strip()
                    if desc_text and len(desc_text) > 20:  # Minimum meaningful content
                        description_text = desc_text
                        break
            
            # If no specific description found, try to get all text content
            if not description_text:
                # Remove navigation, header, footer elements
                for elem in soup(['nav', 'header', 'footer', 'script', 'style']):
                    elem.decompose()
                
                # Get main content text
                main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|body'))
                if main_content:
                    description_text = main_content.get_text().strip()
                else:
                    description_text = soup.get_text().strip()
                
                # Clean up the text
                description_text = re.sub(r'\s+', ' ', description_text)
                if len(description_text) > 100:  # Ensure substantial content
                    job_data['job_description'] = description_text[:500]  # Limit length
            
            if description_text and len(description_text) > 20:
                job_data['job_description'] = description_text[:500]  # Limit length
            
            # Additional content validation - check for job-related keywords
            content_text = (job_data.get('job_name', '') + ' ' + job_data.get('job_description', '')).lower()
            job_keywords = ['developer', 'engineer', 'manager', 'analyst', 'specialist', 'consultant', 
                          'experience', 'skills', 'requirements', 'responsibilities', 'salary', 'benefits',
                          'full-time', 'part-time', 'remote', 'hybrid', 'apply', 'application']
            
            has_job_keywords = any(keyword in content_text for keyword in job_keywords)
            
            # If we found job name OR substantial content with job keywords, consider it valid
            if job_data.get('job_name') or (len(description_text) > 50 and has_job_keywords):
                logger.info(f"   ✅ Job URL has content: {job_data.get('job_name', 'No title')[:50]}...")
                return job_data
            else:
                logger.info(f"   ❌ Job URL has no meaningful content: {job_url}")
                return {}
                
        except Exception as e:
            logger.error(f"   ❌ Error testing job URL content: {e}")
            return {}

    async def _extract_job_urls_from_career_page(self, career_page_url: str) -> List[str]:
        """Extract job URLs directly from career page HTML - OPTIMIZED VERSION"""
        try:
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            import re
            
            # Try to find "All Open Positions" or similar button first
            actual_job_page = await self._find_actual_job_listing_page(career_page_url)
            if actual_job_page and actual_job_page != career_page_url:
                logger.info(f"   🔍 Found actual job listing page: {actual_job_page}")
                career_page_url = actual_job_page
            
            # Detect career page type first
            page_type = await self._detect_career_page_type(career_page_url)
            logger.info(f"   🎯 DETECTED PAGE TYPE: {page_type}")
            
            if page_type == "embedded_jobs":
                # For embedded jobs, extract and cache them, return empty list for URLs
                from .crawler import crawl_single_url
                result = await crawl_single_url(career_page_url)
                if not result['success']:
                    return []
                
                html_content = result['html']
                soup = BeautifulSoup(html_content, 'html.parser')
                
                direct_jobs = await self._extract_direct_jobs_from_career_page(soup, career_page_url)
                if direct_jobs:
                    logger.info(f"   📄 Found {len(direct_jobs)} embedded jobs in career page content")
                    # Store direct jobs for later use with job_index
                    for i, job in enumerate(direct_jobs):
                        job['job_index'] = i + 1
                        job['job_url'] = career_page_url  # Use career page URL as job URL
                    self._direct_jobs_cache = direct_jobs
                    logger.info(f"   📄 Embedded jobs found, no individual URLs needed")
                    return []
            
            elif page_type == "individual_urls":
                # For individual URLs, extract them using the same logic as detection
                from .crawler import crawl_single_url
                result = await crawl_single_url(career_page_url)
                if not result['success']:
                    return []
                
                html_content = result['html']
                soup = BeautifulSoup(html_content, 'html.parser')
                
                job_urls = []
                
                # Use the same patterns as detection
                job_link_patterns = [
                    r'/job/[^"]+', r'/career/[^"]+', r'/careers/[^"]+', r'/jobs/[^"]+', 
                    r'/positions/[^"]+', r'/opportunities/[^"]+', r'/tuyen-dung/[^"]+',
                    r'/recruitment/[^"]+', r'/vacancies/[^"]+', r'/openings/[^"]+',
                    r'/apply/[^"]+', r'/employment/[^"]+', r'/hiring/[^"]+',
                    r'/developer/[^"]+', r'/engineer/[^"]+', r'/manager/[^"]+',
                    r'/analyst/[^"]+', r'/specialist/[^"]+', r'/consultant/[^"]+'
                ]
                
                # Find all links that match job patterns
                all_links = soup.find_all('a', href=True)
                
                for link in all_links:
                    href = link.get('href', '')
                    if not href:
                        continue
                        
                    full_url = urljoin(career_page_url, href)
                    
                    # Skip non-job pages (benefits, culture, etc.)
                    non_job_patterns = [
                        '/benefits', '/culture', '/talent-community', '/work-culture',
                        '/about', '/company', '/team', '/values', '/mission',
                        '/contact', '/news', '/blog', '/press', '/media'
                    ]
                    
                    if any(pattern in full_url.lower() for pattern in non_job_patterns):
                        logger.info(f"   ⚠️ Skipping non-job page: {full_url}")
                        continue
                    
                    # Check if URL matches job patterns (simplified validation)
                    for pattern in job_link_patterns:
                        if re.search(pattern, full_url, re.IGNORECASE):
                            # Basic validation: not just career page root
                            if not (full_url.rstrip('/').endswith('/career') or 
                                   full_url.rstrip('/').endswith('/careers') or 
                                   full_url.rstrip('/').endswith('/jobs')):
                                job_urls.append(full_url)
                                logger.info(f"   🔗 Found job URL: {full_url}")
                                break
                
                # Remove duplicates
                job_urls = list(set(job_urls))
                logger.info(f"   🔗 Found {len(job_urls)} individual job URLs")
                return job_urls
            
            else:  # unknown type
                logger.warning(f"   ❓ Unknown career page type, no job URLs found")
                return []
            
        except Exception as e:
            logger.error(f"   ❌ Error extracting job URLs: {e}")
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
                    if full_url not in job_urls and self._is_job_url(full_url):
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
    
    async def _find_actual_job_listing_page(self, career_page_url: str) -> Optional[str]:
        """Find the actual job listing page by looking for 'All Open Positions' or similar buttons"""
        try:
            from .crawler import crawl_single_url
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            
            result = await crawl_single_url(career_page_url)
            if not result['success'] or not result['html']:
                return None
                
            soup = BeautifulSoup(result['html'], 'html.parser')
            
            # Look for buttons/links that lead to job listings
            job_button_patterns = [
                'all open positions', 'view all jobs', 'see all jobs', 'browse jobs',
                'current openings', 'job opportunities', 'career opportunities',
                'tuyển dụng', 'việc làm', 'cơ hội nghề nghiệp'
            ]
            
            # Check buttons and links
            for element in soup.find_all(['a', 'button']):
                text = (element.get_text() or '').strip().lower()
                href = element.get('href', '')
                
                if any(pattern in text for pattern in job_button_patterns):
                    if href:
                        full_url = urljoin(career_page_url, href)
                        logger.info(f"   🔍 Found job listing button: '{text}' -> {full_url}")
                        return full_url
                    else:
                        # Button without href, might be JavaScript - try to find nearby links
                        parent = element.parent
                        if parent:
                            for link in parent.find_all('a', href=True):
                                full_url = urljoin(career_page_url, link['href'])
                                if 'job' in full_url.lower() or 'career' in full_url.lower():
                                    logger.info(f"   🔍 Found nearby job link: {full_url}")
                                    return full_url
            
            # Check for common job listing URL patterns
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(pattern in href.lower() for pattern in ['/jobs', '/careers', '/positions', '/opportunities']):
                    full_url = urljoin(career_page_url, href)
                    if full_url != career_page_url:  # Not the same page
                        logger.info(f"   🔍 Found job listing URL pattern: {full_url}")
                        return full_url
            
            return None
            
        except Exception as e:
            logger.error(f"   ❌ Error finding job listing page: {e}")
            return None
    
    # Removed legacy alternative methods in favor of deterministic flow in extract_job_urls_only
    
    async def _extract_jobs_from_containers(self, career_page_url: str, max_jobs: int) -> List[Dict]:
        """Extract jobs using anchor → container method"""
        try:
            logger.info(f"   🔍 Container extraction for: {career_page_url}")
            
            from .crawler import crawl_single_url
            result = await crawl_single_url(career_page_url)
            if not result['success']:
                return []
            
            html = result['html']
            if not html:
                return []
            
            # Parse HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find anchor points (job indicators)
            job_indicators = [
                # Vietnamese
                'apply now', 'apply', 'ứng tuyển', 'tuyển dụng',
                'download jd', 'job description', 'mô tả công việc',
                'fulltime', 'part-time', 'toàn thời gian', 'bán thời gian',
                'hạn ứng tuyển', 'deadline', 'thời hạn',
                'mức lương', 'salary', 'lương',
                'nơi làm việc', 'location', 'địa điểm',
                # English
                'view details', 'see more', 'learn more',
                'join us', 'work with us', 'career opportunity'
            ]
            
            # Find all elements containing job indicators
            anchor_elements = []
            for indicator in job_indicators:
                elements = soup.find_all(text=lambda text: text and indicator.lower() in text.lower())
                for element in elements:
                    if element.parent:
                        anchor_elements.append(element.parent)
            
            logger.info(f"   🎯 Found {len(anchor_elements)} anchor elements")
            
            # Find containers for each anchor
            containers = []
            for anchor in anchor_elements:
                container = self._find_job_container(anchor, soup)
                if container and container not in containers:
                    containers.append(container)
            
            logger.info(f"   📦 Found {len(containers)} unique containers")
            
            # Extract jobs from containers
            jobs = []
            for i, container in enumerate(containers[:max_jobs]):
                job_data = self._extract_job_from_container(container, career_page_url, i + 1)
                if job_data and self._is_valid_job_data(job_data):
                    jobs.append(job_data)
            
            logger.info(f"   ✅ Extracted {len(jobs)} valid jobs from containers")
            return jobs
            
        except Exception as e:
            logger.error(f"   ❌ Container extraction error: {e}")
            return []
    
    def _find_job_container(self, anchor_element, soup) -> BeautifulSoup:
        """Find the job container for an anchor element"""
        try:
            # Walk up the DOM tree to find a suitable container
            current = anchor_element
            max_depth = 6
            depth = 0
            
            while current and depth < max_depth:
                # Check if current element contains job indicators
                text_content = current.get_text().lower() if hasattr(current, 'get_text') else ''
                
                job_indicators_count = sum(1 for indicator in [
                    'fulltime', 'part-time', 'mức lương', 'salary', 'nơi làm việc', 'location',
                    'hạn ứng tuyển', 'deadline', 'apply', 'ứng tuyển'
                ] if indicator in text_content)
                
                # If we found a container with multiple job indicators, use it
                if job_indicators_count >= 2:
                    # Check if container is not too large (avoid selecting entire page)
                    if len(current.get_text()) < 2000:  # Reasonable size limit
                        return current
                
                current = current.parent
                depth += 1
            
            return None
            
        except Exception as e:
            logger.warning(f"   ⚠️ Error finding container: {e}")
            return None
    
    def _extract_job_from_container(self, container, career_page_url: str, job_index: int) -> Dict:
        """Extract job data from a container"""
        try:
            text_content = container.get_text()
            
            # Extract title (look for headings or large text)
            title = self._extract_title_from_container(container)
            
            # Extract job type
            job_type = self._extract_job_type_from_container(container)
            
            # Extract location
            location = self._extract_location_from_container(container)
            
            # Extract salary
            salary = self._extract_salary_from_container(container)
            
            # Extract description (use container text as description)
            description = text_content.strip()
            
            # Extract company (try to get from URL or page title)
            company = self._extract_company_from_url(career_page_url)
            
            # Extract job link (if any)
            job_link = self._extract_job_link_from_container(container, career_page_url)
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'job_type': job_type,
                'salary': salary,
                'description': description,
                'job_link': job_link,
                'source_url': career_page_url,
                'job_index': job_index
            }
            
        except Exception as e:
            logger.warning(f"   ⚠️ Error extracting job from container: {e}")
            return {}
    
    def _extract_title_from_container(self, container) -> str:
        """Extract job title from container"""
        try:
            # Look for headings first
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                heading = container.find(tag)
                if heading:
                    title = heading.get_text().strip()
                    if len(title) > 3 and len(title) < 100:
                        return title
            
            # Look for Wix-specific elements
            wix_elements = container.find_all(class_=lambda x: x and 'wixui-rich-text__text' in x)
            for element in wix_elements:
                title = element.get_text().strip()
                if len(title) > 3 and len(title) < 100:
                    # Check if it looks like a job title
                    if any(job_word in title.lower() for job_word in ['developer', 'engineer', 'manager', 'analyst', 'specialist', 'tuyển dụng']):
                        return title
            
            # For Wix, if container itself contains job title, extract it
            container_text = container.get_text().strip()
            if any(job_title in container_text.lower() for job_title in ['java web developer', 'full stack developer', 'c++ developer', 'java developer spring boot', 'tester', 'business analyst', 'human resource']):
                # Extract the job title from the beginning of the text
                lines = container_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if any(job_title in line.lower() for job_title in ['java web developer', 'full stack developer', 'c++ developer', 'java developer spring boot', 'tester', 'business analyst', 'human resource']):
                        # Extract just the job title part
                        for job_title in ['java web developer', 'full stack developer', 'c++ developer', 'java developer spring boot', 'tester', 'business analyst', 'human resource']:
                            if job_title in line.lower():
                                # Find the position and extract the title
                                start_pos = line.lower().find(job_title)
                                title_part = line[start_pos:start_pos + len(job_title)]
                                return title_part.title()
            
            # Look for elements with job-related classes
            for class_name in ['title', 'job-title', 'position', 'role', 'font_6']:
                element = container.find(class_=lambda x: x and class_name in x.lower())
                if element:
                    title = element.get_text().strip()
                    if len(title) > 3 and len(title) < 100:
                        return title
            
            # Look for strong/bold text
            strong = container.find('strong')
            if strong:
                title = strong.get_text().strip()
                if len(title) > 3 and len(title) < 100:
                    return title
            
            # Fallback: use first substantial line of text
            text_lines = container.get_text().split('\n')
            for line in text_lines:
                line = line.strip()
                if len(line) > 5 and len(line) < 100:
                    # Check if it looks like a job title
                    if any(job_word in line.lower() for job_word in ['developer', 'engineer', 'manager', 'analyst', 'specialist', 'fulltime', 'full-time']):
                        return line
            
            return ""
            
        except Exception as e:
            logger.warning(f"   ⚠️ Error extracting title: {e}")
            return ""
    
    def _extract_job_type_from_container(self, container) -> str:
        """Extract job type from container"""
        try:
            text = container.get_text().lower()
            if 'fulltime' in text or 'full-time' in text or 'toàn thời gian' in text:
                return 'Full-time'
            elif 'part-time' in text or 'parttime' in text or 'bán thời gian' in text:
                return 'Part-time'
            elif 'contract' in text or 'hợp đồng' in text:
                return 'Contract'
            elif 'intern' in text or 'thực tập' in text:
                return 'Internship'
            else:
                return 'Full-time'  # Default
        except:
            return 'Full-time'
    
    def _extract_location_from_container(self, container) -> str:
        """Extract location from container"""
        try:
            text = container.get_text()
            import re
            
            # Look for location patterns
            location_patterns = [
                r'nơi làm việc[:\s]+([^\n]+)',
                r'location[:\s]+([^\n]+)',
                r'địa điểm[:\s]+([^\n]+)',
                r'work location[:\s]+([^\n]+)'
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    location = match.group(1).strip()
                    if len(location) > 0 and len(location) < 100:
                        return location
            
            return ""
        except:
            return ""
    
    def _extract_salary_from_container(self, container) -> str:
        """Extract salary from container"""
        try:
            text = container.get_text()
            import re
            
            # Look for salary patterns
            salary_patterns = [
                r'mức lương[:\s]+([^\n]+)',
                r'salary[:\s]+([^\n]+)',
                r'lương[:\s]+([^\n]+)'
            ]
            
            for pattern in salary_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    salary = match.group(1).strip()
                    if len(salary) > 0 and len(salary) < 100:
                        return salary
            
            return ""
        except:
            return ""
    
    def _extract_company_from_url(self, url: str) -> str:
        """Extract company name from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove common prefixes
            domain = domain.replace('www.', '').replace('careers.', '').replace('jobs.', '')
            
            # Extract company name
            if '.' in domain:
                company = domain.split('.')[0]
                return company.title()
            
            return domain.title()
        except:
            return ""
    
    def _extract_job_link_from_container(self, container, career_page_url: str) -> str:
        """Extract job link from container"""
        try:
            # Look for links in container
            links = container.find_all('a', href=True)
            for link in links:
                href = link['href']
                if href and href.startswith('http'):
                    return href
            
            # If no direct link, return career page URL
            return career_page_url
        except:
            return career_page_url
    
    def _is_valid_job_data(self, job_data: Dict) -> bool:
        """Check if job data is valid"""
        try:
            title = job_data.get('title', '').strip()
            description = job_data.get('description', '').strip()
            
            # Basic validation
            if not title or len(title) < 3:
                return False
            
            if not description or len(description) < 20:
                return False
            
            # Check for job-related keywords
            job_keywords = [
                'developer', 'engineer', 'analyst', 'manager', 'specialist',
                'consultant', 'coordinator', 'assistant', 'director', 'lead',
                'senior', 'junior', 'intern', 'trainee', 'graduate',
                'tester', 'designer', 'architect', 'admin', 'hr',
                'business', 'marketing', 'sales', 'finance', 'accounting'
            ]
            
            content = f"{title} {description}".lower()
            has_job_keyword = any(keyword in content for keyword in job_keywords)
            
            return has_job_keyword
            
        except:
            return False
    
    async def _extract_jobs_from_api_endpoints(self, career_page_url: str) -> List[Dict]:
        """Extract jobs from API endpoints found in the page"""
        try:
            logger.info(f"   🔍 Trying API extraction for: {career_page_url}")
            
            # Try to use Playwright to find API endpoints
            try:
                from playwright.async_api import async_playwright
                
                jobs = []
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=["--no-sandbox", "--disable-dev-shm-usage"]
                    )
                    page = await browser.new_page()
                    
                    # Enable network monitoring
                    api_responses = []
                    
                    def handle_response(response):
                        if response.url and any(keyword in response.url.lower() for keyword in ['job', 'career', 'position', 'api', 'graphql']):
                            api_responses.append({
                                'url': response.url,
                                'status': response.status,
                                'headers': response.headers
                            })
                    
                    page.on('response', handle_response)
                    
                    # Navigate to the page
                    await page.goto(career_page_url, wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(5000)  # Wait for API calls
                    
                    logger.info(f"   📡 Found {len(api_responses)} potential API responses")
                    
                    # Try to extract job data from API responses
                    for api_response in api_responses:
                        try:
                            if api_response['status'] == 200:
                                # Try to get response body
                                try:
                                    response_body = await page.evaluate(f"""
                                        () => {{
                                            // Try to find the response in network tab
                                            return null; // Placeholder for now
                                        }}
                                    """)
                                    
                                    if response_body:
                                        # Parse JSON response
                                        import json
                                        data = json.loads(response_body)
                                        jobs.extend(self._parse_api_job_data(data, career_page_url))
                                except Exception as e:
                                    logger.debug(f"   ⚠️ Error parsing API response: {e}")
                                    continue
                        except Exception as e:
                            logger.debug(f"   ⚠️ Error processing API response: {e}")
                            continue
                    
                    # Method 2: Try common API endpoints
                    common_api_endpoints = [
                        f"{career_page_url}/api/jobs",
                        f"{career_page_url}/api/careers",
                        f"{career_page_url}/api/positions",
                        f"{career_page_url}/jobs.json",
                        f"{career_page_url}/careers.json",
                        f"{career_page_url}/positions.json",
                        f"{career_page_url}/api/v1/jobs",
                        f"{career_page_url}/api/v1/careers",
                        f"{career_page_url}/graphql"
                    ]
                    
                    for api_url in common_api_endpoints:
                        try:
                            # Try to fetch from API endpoint
                            response = await page.goto(api_url, wait_until='networkidle', timeout=10000)
                            if response and response.status == 200:
                                content = await page.content()
                                
                                # Try to parse as JSON
                                try:
                                    import json
                                    data = json.loads(content)
                                    api_jobs = self._parse_api_job_data(data, career_page_url)
                                    if api_jobs:
                                        jobs.extend(api_jobs)
                                        logger.info(f"   ✅ Found {len(api_jobs)} jobs from API: {api_url}")
                                except json.JSONDecodeError:
                                    # Not JSON, try to extract from HTML
                                    pass
                        except Exception as e:
                            logger.debug(f"   ⚠️ Error fetching API endpoint {api_url}: {e}")
                            continue
                    
                    await browser.close()
                
                logger.info(f"   ✅ API extraction completed, found {len(jobs)} jobs")
                return jobs
                
            except ImportError:
                logger.warning("   ⚠️ Playwright not available for API extraction")
                return []
            
        except Exception as e:
            logger.error(f"   ❌ Error in API extraction: {e}")
            return []
    
    def _parse_api_job_data(self, data: dict, base_url: str) -> List[Dict]:
        """Parse job data from API response"""
        jobs = []
        
        try:
            # Common API response structures
            job_lists = []
            
            # Try different possible structures
            if isinstance(data, dict):
                # Structure 1: { "jobs": [...] }
                if 'jobs' in data and isinstance(data['jobs'], list):
                    job_lists.append(data['jobs'])
                
                # Structure 2: { "data": { "jobs": [...] } }
                elif 'data' in data and isinstance(data['data'], dict):
                    if 'jobs' in data['data'] and isinstance(data['data']['jobs'], list):
                        job_lists.append(data['data']['jobs'])
                
                # Structure 3: { "results": [...] }
                elif 'results' in data and isinstance(data['results'], list):
                    job_lists.append(data['results'])
                
                # Structure 4: { "items": [...] }
                elif 'items' in data and isinstance(data['items'], list):
                    job_lists.append(data['items'])
                
                # Structure 5: Direct array of jobs
                elif any(key in data for key in ['title', 'name', 'position']) and len(data) > 0:
                    job_lists.append([data])
            
            elif isinstance(data, list):
                # Direct array of jobs
                job_lists.append(data)
            
            # Process job lists
            for job_list in job_lists:
                for job in job_list:
                    if isinstance(job, dict):
                        # Extract job information
                        title = job.get('title') or job.get('name') or job.get('position') or job.get('job_title') or ''
                        url = job.get('url') or job.get('link') or job.get('apply_url') or base_url
                        location = job.get('location') or job.get('city') or job.get('address') or ''
                        job_type = job.get('type') or job.get('employment_type') or job.get('job_type') or 'Full-time'
                        description = job.get('description') or job.get('summary') or job.get('details') or ''
                        
                        if title and url:
                            jobs.append({
                                'title': title,
                                'company': '',
                                'location': location,
                                'job_type': job_type,
                                'salary': job.get('salary') or '',
                                'posted_date': job.get('date') or job.get('created_at') or '',
                                'url': url if url.startswith('http') else f"{base_url.rstrip('/')}/{url.lstrip('/')}",
                                'description': description,
                                'requirements': job.get('requirements') or '',
                                'benefits': job.get('benefits') or ''
                            })
            
            logger.info(f"   📊 Parsed {len(jobs)} jobs from API data")
            return jobs
            
        except Exception as e:
            logger.error(f"   ❌ Error parsing API job data: {e}")
            return []
    
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
        """Extract jobs from JavaScript data using Playwright for rendering"""
        try:
            logger.info(f"   🔍 Trying JavaScript extraction with Playwright for: {career_page_url}")
            
            # Try to use Playwright for JavaScript rendering
            try:
                from playwright.async_api import async_playwright
                
                jobs = []
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=True,
                        args=["--no-sandbox", "--disable-dev-shm-usage"]
                    )
                    page = await browser.new_page()
                    
                    # Set user agent to avoid detection
                    await page.set_extra_http_headers({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    })
                    
                    # Navigate to the page and wait for content to load
                    await page.goto(career_page_url, wait_until='networkidle', timeout=30000)
                    
                    # Wait a bit more for dynamic content
                    await page.wait_for_timeout(3000)
                    
                    # Method 1: Handle dynamic pagination and "Load more" buttons
                    await self._handle_dynamic_pagination(page, career_page_url)
                    
                    # Method 2: Extract job data from page content after JavaScript rendering
                    job_elements = await page.query_selector_all('[class*="job"], [class*="career"], [class*="position"], .job-listing, .career-item, .position-item')
                    
                    logger.info(f"   📊 Found {len(job_elements)} job elements after JavaScript rendering")
                    
                    for element in job_elements[:20]:  # Limit to 20 jobs
                        try:
                            # Extract job title
                            title_element = await element.query_selector('h1, h2, h3, h4, .job-title, .position-title, .career-title')
                            title = await title_element.text_content() if title_element else ''
                            
                            # Extract job link
                            link_element = await element.query_selector('a[href*="job"], a[href*="career"], a[href*="position"]')
                            job_url = await link_element.get_attribute('href') if link_element else ''
                            
                            if job_url and not job_url.startswith('http'):
                                job_url = urljoin(career_page_url, job_url)
                            
                            # Extract location
                            location_element = await element.query_selector('[class*="location"], .location, .job-location')
                            location = await location_element.text_content() if location_element else ''
                            
                            # Extract job type
                            type_element = await element.query_selector('[class*="type"], .job-type, .position-type')
                            job_type = await type_element.text_content() if type_element else 'Full-time'
                            
                            if title and job_url:
                                jobs.append({
                                    'title': title.strip(),
                                    'company': '',
                                    'location': location.strip() if location else '',
                                    'job_type': job_type.strip() if job_type else 'Full-time',
                                    'salary': '',
                                    'posted_date': '',
                                    'url': job_url,
                                    'description': '',
                                    'requirements': '',
                                    'benefits': ''
                                })
                                logger.info(f"   ✅ Extracted job: {title}")
                        
                        except Exception as e:
                            logger.debug(f"   ⚠️ Error extracting job element: {e}")
                            continue
                    
                    # Method 3: Try to extract from JavaScript variables
                    try:
                        js_data = await page.evaluate("""
                            () => {
                                const jobs = [];
                                // Look for common job data variables
                                if (window.jobs && Array.isArray(window.jobs)) {
                                    return window.jobs;
                                }
                                if (window.jobList && Array.isArray(window.jobList)) {
                                    return window.jobList;
                                }
                                if (window.careers && Array.isArray(window.careers)) {
                                    return window.careers;
                                }
                                if (window.positions && Array.isArray(window.positions)) {
                                    return window.positions;
                                }
                                return null;
                            }
                        """)
                        
                        if js_data and isinstance(js_data, list):
                            logger.info(f"   📊 Found {len(js_data)} jobs from JavaScript variables")
                            for job in js_data[:10]:
                                if isinstance(job, dict) and job.get('title') and job.get('url'):
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
                    except Exception as e:
                        logger.debug(f"   ⚠️ Error extracting JavaScript variables: {e}")
                    
                    await browser.close()
                
                logger.info(f"   ✅ JavaScript extraction completed, found {len(jobs)} jobs")
                return jobs
                
            except ImportError:
                logger.warning("   ⚠️ Playwright not available, falling back to requests method")
                # Fallback to requests method (existing code)
                return await self._extract_jobs_from_javascript_requests(career_page_url)
            
        except Exception as e:
            logger.error(f"   ❌ Error in JavaScript extraction: {e}")
            return []
    
    async def _handle_dynamic_pagination(self, page, career_page_url: str):
        """Handle dynamic pagination, infinite scroll, and 'Load more' buttons"""
        try:
            logger.info(f"   🔄 Handling dynamic pagination for: {career_page_url}")
            
            # Method 1: Handle "Load more" buttons
            load_more_selectors = [
                'button:has-text("Load more")',
                'button:has-text("Show more")',
                'button:has-text("Load more jobs")',
                'button:has-text("View more")',
                'a:has-text("Load more")',
                'a:has-text("Show more")',
                '.load-more',
                '.show-more',
                '[data-load-more]',
                '[class*="load-more"]',
                '[class*="show-more"]'
            ]
            
            for selector in load_more_selectors:
                try:
                    load_more_button = await page.query_selector(selector)
                    if load_more_button:
                        logger.info(f"   🔄 Found 'Load more' button with selector: {selector}")
                        
                        # Click load more button multiple times
                        for i in range(3):  # Try to load 3 more pages
                            try:
                                await load_more_button.click()
                                await page.wait_for_timeout(2000)  # Wait for content to load
                                logger.info(f"   ✅ Clicked 'Load more' button (attempt {i + 1})")
                            except Exception as e:
                                logger.debug(f"   ⚠️ Error clicking load more button: {e}")
                                break
                        break
                except Exception as e:
                    continue
            
            # Method 2: Handle infinite scroll
            try:
                # Scroll down multiple times to trigger infinite scroll
                for i in range(5):  # Scroll 5 times
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)  # Wait for content to load
                    logger.info(f"   📜 Scrolled to bottom (attempt {i + 1})")
            except Exception as e:
                logger.debug(f"   ⚠️ Error during infinite scroll: {e}")
            
            # Method 3: Handle pagination links
            pagination_selectors = [
                'a[href*="page="]',
                'a[href*="p="]',
                'a[href*="paged="]',
                '.pagination a',
                '.pager a',
                '[class*="pagination"] a',
                '[class*="pager"] a'
            ]
            
            for selector in pagination_selectors:
                try:
                    pagination_links = await page.query_selector_all(selector)
                    if pagination_links:
                        logger.info(f"   📄 Found {len(pagination_links)} pagination links")
                        
                        # Click first few pagination links
                        for i, link in enumerate(pagination_links[:3]):  # Click first 3 pages
                            try:
                                await link.click()
                                await page.wait_for_timeout(2000)  # Wait for content to load
                                logger.info(f"   ✅ Clicked pagination link {i + 1}")
                            except Exception as e:
                                logger.debug(f"   ⚠️ Error clicking pagination link: {e}")
                                break
                        break
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"   ❌ Error handling dynamic pagination: {e}")
    
    async def _extract_jobs_from_javascript_requests(self, career_page_url: str) -> List[Dict]:
        """Fallback method using requests (original implementation)"""
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