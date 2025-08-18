# app/services/career_pages_service.py
"""
Enhanced career page detection service
"""

import logging
import asyncio
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime

from ..utils.constants import CAREER_KEYWORDS_VI, CAREER_SELECTORS, JOB_BOARD_DOMAINS
from ..services.career_detector import filter_career_urls
from .crawler import crawl_single_url
from .scrapy_runner import run_spider

logger = logging.getLogger(__name__)

class CareerPagesService:
    """Enhanced service for detecting career pages"""
    
    def __init__(self):
        self.career_keywords = CAREER_KEYWORDS_VI + [
            'career', 'careers', 'jobs', 'employment', 'work-with-us',
            'join-us', 'opportunities', 'vacancies', 'positions',
            'tuyen-dung', 'viec-lam', 'co-hoi', 'tuyen-nhan-vien'
        ]
        
        self.job_board_domains = list(JOB_BOARD_DOMAINS) + [
            'jobs.vn', 'careerlink.vn', 'topcv.vn', 'mywork.vn',
            'indeed.com', 'linkedin.com/jobs', 'glassdoor.com'
        ]
    
    async def detect_career_pages(self, url: str, include_subdomain_search: bool = False,
                                max_pages_to_scan: int = 100, strict_filtering: bool = False,  # Default to False
                                include_job_boards: bool = False, use_scrapy: bool = True) -> Dict:
        """
        Detect career pages with enhanced capabilities
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🔍 Starting career page detection for: {url}")
            
            # Temporarily disable Scrapy due to project settings issues
            if use_scrapy:
                logger.info("⚠️ Scrapy temporarily disabled, using requests fallback")
                use_scrapy = False
            
            # Use requests-based method
            logger.info("🔄 Using requests-based crawling method")
            
            # Step 1: Crawl the main page
            result = await crawl_single_url(url)
            
            if not result or not result.get('success'):
                return {
                    'success': False,
                    'error_message': 'Failed to crawl the website',
                    'requested_url': url,
                    'crawl_time': (datetime.now() - start_time).total_seconds()
                }
            
            # Step 2: Extract all URLs from the page
            all_urls = result.get('urls', [])
            logger.info(f"   📋 Found {len(all_urls)} URLs to analyze")
            
            # Step 3: Filter and analyze URLs
            career_pages = []
            potential_career_pages = []
            rejected_urls = []
            career_page_analysis = []
            
            # Step 4: Analyze each URL
            for url_found in all_urls[:max_pages_to_scan]:
                analysis = await self._analyze_url_for_career(url_found, url, strict_filtering)
                
                if analysis['is_career_page']:
                    career_pages.append(url_found)
                    career_page_analysis.append(analysis)
                    logger.info(f"   ✅ Career page found: {url_found}")
                elif analysis['is_potential']:
                    potential_career_pages.append(url_found)
                    career_page_analysis.append(analysis)
                    logger.info(f"   ⚠️ Potential career page: {url_found}")
                else:
                    rejected_urls.append({
                        'url': url_found,
                        'reason': analysis['rejection_reason']
                    })
            
            # Step 5: Subdomain search (if enabled)
            if include_subdomain_search:
                subdomain_results = await self._search_subdomains(url, strict_filtering)
                career_pages.extend(subdomain_results['career_pages'])
                potential_career_pages.extend(subdomain_results['potential_pages'])
                career_page_analysis.extend(subdomain_results['analysis'])
            
            # Step 6: Job board integration (if enabled)
            if include_job_boards:
                job_board_results = await self._search_job_boards(url)
                career_pages.extend(job_board_results['career_pages'])
                career_page_analysis.extend(job_board_results['analysis'])
            
            # Step 7: Remove duplicates and validate
            career_pages = list(set(career_pages))
            potential_career_pages = list(set(potential_career_pages))
            
            # Step 8: Apply strict filtering if requested
            if strict_filtering:
                filtered_career_pages = []
                for page in career_pages:
                    # Check if this page has high confidence in analysis
                    page_analysis = next((a for a in career_page_analysis if a['url'] == page), None)
                    
                    if page_analysis and page_analysis.get('confidence', 0) >= 0.5:  # Giảm từ 0.8 xuống 0.5
                        # Medium confidence career pages should pass validation
                        filtered_career_pages.append(page)
                        logger.info(f"✅ Career page passed validation: {page} (score: {page_analysis['confidence']})")
                    else:
                        # Apply strict validation only for lower confidence pages
                        validation = filter_career_urls([page])
                        if validation and validation[0]['is_accepted']:
                            filtered_career_pages.append(page)
                        else:
                            potential_career_pages.append(page)
                            rejected_urls.append({
                                'url': page,
                                'reason': 'Failed strict validation'
                            })
                career_pages = filtered_career_pages
            
            # Step 9: Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                len(career_pages), len(potential_career_pages), len(all_urls)
            )
            
            crawl_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'requested_url': url,
                'crawl_time': crawl_time,
                'career_pages': career_pages,
                'potential_career_pages': potential_career_pages,
                'rejected_urls': rejected_urls,
                'career_page_analysis': career_page_analysis,
                'total_urls_scanned': len(all_urls),
                'valid_career_pages': len(career_pages),
                'confidence_score': confidence_score
            }
            
        except Exception as e:
            logger.error(f"Error in career page detection: {e}")
            return {
                'success': False,
                'error_message': str(e),
                'requested_url': url,
                'crawl_time': (datetime.now() - start_time).total_seconds()
            }
    
    async def _analyze_url_for_career(self, url: str, base_url: str, strict_filtering: bool) -> Dict:
        """Analyze a single URL for career page indicators with improved scoring and validation"""
        analysis = {
            'url': url,
            'is_career_page': False,
            'is_potential': False,
            'confidence': 0.0,
            'rejection_reason': None,
            'indicators': []
        }
        
        try:
            # Skip non-HTTP URLs
            if not url.startswith(('http://', 'https://')):
                analysis['rejection_reason'] = 'Non-HTTP URL'
                return analysis
            
            # Parse URL
            parsed = urlparse(url)
            path = parsed.path.lower()
            domain = parsed.netloc.lower()
            
            # IMPROVED SCORING SYSTEM (Cách 1)
            career_indicators = []
            
            # 1. Exact career keywords (HIGHEST WEIGHT)
            exact_career_keywords = ['career', 'careers', 'jobs', 'employment', 'tuyen-dung', 'viec-lam', 'co-hoi-nghe-nghiep', 'tuyen-nhan-vien']
            for keyword in exact_career_keywords:
                if keyword in path:
                    career_indicators.append(f"Exact career keyword: '{keyword}'")
                    analysis['confidence'] += 1.0  # Tăng từ 0.6 lên 1.0
            
            # 2. Generic keywords (MEDIUM WEIGHT) - Tăng weight để dễ đạt 0.5
            generic_keywords = ['dev', 'software', 'tech', 'ml', 'ai', 'testing', 'it', 'digital']
            for keyword in generic_keywords:
                if keyword in path:
                    career_indicators.append(f"Path contains '{keyword}'")
                    analysis['confidence'] += 0.3  # Tăng từ 0.1 lên 0.3
            
            # 3. Career patterns (HIGH WEIGHT) - EASIER TO REACH 0.5
            career_patterns = ['/career', '/careers', '/jobs', '/employment', '/tuyen-dung', '/viec-lam', '/co-hoi-nghe-nghiep', '/tuyen-nhan-vien']
            for pattern in career_patterns:
                if pattern in path:
                    career_indicators.append(f"Career pattern: {pattern}")
                    analysis['confidence'] += 0.8  # Giữ nguyên 0.8
            
            # 4. Domain keywords (LOW WEIGHT)
            for keyword in self.career_keywords:
                if keyword in domain:
                    career_indicators.append(f"Domain contains '{keyword}'")
                    analysis['confidence'] += 0.05  # Giảm từ 0.1 xuống 0.05
            
            # 5. Job board domains
            for job_board in self.job_board_domains:
                if job_board in domain:
                    career_indicators.append(f"Job board domain: {job_board}")
                    analysis['confidence'] += 0.5
            
            # 6. Path depth - BONUS FOR SHALLOW PATHS
            path_depth = len([p for p in path.split('/') if p])
            if path_depth <= 2:
                career_indicators.append("Shallow path depth")
                analysis['confidence'] += 0.2  # Tăng từ 0.1 lên 0.2
            elif path_depth > 4:
                analysis['rejection_reason'] = 'Path too deep'
                return analysis
            
            # IMPROVED NON-CAREER PENALTIES
            non_career_patterns = {
                '/product': -0.5,      # Tăng penalty
                '/service': -0.5,      # Tăng penalty
                '/news': -0.4,         # Tăng penalty
                '/blog': -0.4,         # Tăng penalty
                '/article': -0.4,      # Tăng penalty
                '/about': -0.3,        # Giữ nguyên
                '/contact': -0.3,      # Giữ nguyên
                '/admin': -0.8,        # Tăng penalty
                '/login': -0.8,        # Tăng penalty
            }
            
            for pattern, penalty in non_career_patterns.items():
                if pattern in path:
                    analysis['confidence'] += penalty
                    if penalty <= -0.5:  # Strong penalty
                        analysis['rejection_reason'] = f'Strong non-career pattern: {pattern}'
            
            # IMPROVED VALIDATION LOGIC (Cách 2)
            # Nếu confidence rất cao, luôn accept (bỏ qua strict validation)
            if analysis['confidence'] >= 1.5:
                analysis['is_career_page'] = True
                analysis['is_potential'] = False
                analysis['rejection_reason'] = None  # Clear rejection reason
            elif analysis['confidence'] >= 1.0:
                analysis['is_career_page'] = True
                analysis['is_potential'] = False
            elif analysis['confidence'] >= 0.6:
                analysis['is_potential'] = True
            elif analysis['confidence'] < 0.0:
                # Nếu confidence âm, reject
                if not analysis['rejection_reason']:
                    analysis['rejection_reason'] = 'Low confidence score'
            
            analysis['indicators'] = career_indicators
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing URL {url}: {e}")
            analysis['rejection_reason'] = f'Analysis error: {str(e)}'
            return analysis
    
    async def _search_subdomains(self, base_url: str, strict_filtering: bool) -> Dict:
        """Search for career pages in subdomains"""
        subdomain_results = {
            'career_pages': [],
            'potential_pages': [],
            'analysis': []
        }
        
        try:
            parsed = urlparse(base_url)
            domain = parsed.netloc
            
            # Common subdomain patterns for career pages
            subdomain_patterns = [
                'career', 'careers', 'jobs', 'employment',
                'tuyen-dung', 'viec-lam', 'hr', 'recruitment'
            ]
            
            # Generate subdomain URLs
            subdomain_urls = []
            for pattern in subdomain_patterns:
                subdomain_urls.append(f"https://{pattern}.{domain}")
                # Add common career page patterns
                for career_pattern in ['/career', '/careers', '/jobs', '/tuyen-dung', '/viec-lam']:
                    subdomain_urls.append(f"https://{pattern}.{domain}{career_pattern}")
            
            # Test subdomain URLs
            tasks = []
            for subdomain_url in subdomain_urls:
                task = self._test_subdomain_url(subdomain_url, strict_filtering)
                tasks.append(task)
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, dict) and result.get('success'):
                        if result.get('is_career_page'):
                            subdomain_results['career_pages'].append(result['url'])
                        elif result.get('is_potential'):
                            subdomain_results['potential_pages'].append(result['url'])
                        subdomain_results['analysis'].append(result)
            
        except Exception as e:
            logger.error(f"Error in subdomain search: {e}")
        
        return subdomain_results
    
    async def _test_subdomain_url(self, url: str, strict_filtering: bool) -> Dict:
        """Test if a subdomain URL is accessible and contains career content"""
        try:
            result = await crawl_single_url(url)
            
            if result['success']:
                analysis = await self._analyze_url_for_career(url, url, strict_filtering)
                analysis['success'] = True
                return analysis
            else:
                return {
                    'url': url,
                    'success': False,
                    'is_career_page': False,
                    'is_potential': False,
                    'rejection_reason': 'Failed to crawl'
                }
                
        except Exception as e:
            return {
                'url': url,
                'success': False,
                'is_career_page': False,
                'is_potential': False,
                'rejection_reason': f'Crawl error: {str(e)}'
            }
    
    async def _search_job_boards(self, base_url: str) -> Dict:
        """Search for company presence on job boards"""
        job_board_results = {
            'career_pages': [],
            'analysis': []
        }
        
        try:
            parsed = urlparse(base_url)
            domain = parsed.netloc
            
            # Extract company name from domain
            company_name = domain.split('.')[0]
            
            # Search on common job boards
            job_board_urls = [
                f"https://jobs.vn/company/{company_name}",
                f"https://careerlink.vn/company/{company_name}",
                f"https://topcv.vn/company/{company_name}",
                f"https://mywork.vn/company/{company_name}"
            ]
            
            # Test job board URLs
            tasks = []
            for job_board_url in job_board_urls:
                task = self._test_job_board_url(job_board_url, company_name)
                tasks.append(task)
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, dict) and result.get('success'):
                        if result.get('has_jobs'):
                            job_board_results['career_pages'].append(result['url'])
                        job_board_results['analysis'].append(result)
            
        except Exception as e:
            logger.error(f"Error in job board search: {e}")
        
        return job_board_results
    
    async def _test_job_board_url(self, url: str, company_name: str) -> Dict:
        """Test if a job board URL has jobs for the company"""
        try:
            result = await crawl_single_url(url)
            
            if result['success']:
                html_content = result.get('html', '').lower()
                
                # Check for job indicators
                job_indicators = [
                    'job', 'position', 'vacancy', 'opening',
                    'tuyen-dung', 'viec-lam', 'co-hoi'
                ]
                
                has_jobs = any(indicator in html_content for indicator in job_indicators)
                
                return {
                    'url': url,
                    'success': True,
                    'has_jobs': has_jobs,
                    'company_name': company_name,
                    'job_count_estimate': html_content.count('job') + html_content.count('position')
                }
            else:
                return {
                    'url': url,
                    'success': False,
                    'has_jobs': False,
                    'company_name': company_name
                }
                
        except Exception as e:
            return {
                'url': url,
                'success': False,
                'has_jobs': False,
                'company_name': company_name,
                'error': str(e)
            }
    
    async def _detect_career_pages_scrapy(self, url: str, max_pages: int) -> Dict:
        """
        Detect career pages using optimized Scrapy spider
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🚀 Running optimized Scrapy spider for: {url}")
            
            # Run Scrapy spider using new runner
            result = await run_spider(url, max_pages)
            
            # Debug log
            logger.info(f"🔍 Scrapy result type: {type(result)}")
            logger.info(f"🔍 Scrapy result value: {result}")
            
            # Handle error cases first
            if not isinstance(result, dict):
                return {
                    'success': False,
                    'error_message': f'Invalid result format: {type(result)} - Expected dict, got {type(result)}',
                    'requested_url': url,
                    'crawl_time': (datetime.now() - start_time).total_seconds(),
                    'crawl_method': 'scrapy_optimized'
                }
            
            if not result.get('success', False):
                return {
                    'success': False,
                    'error_message': result.get('error_message', 'Scrapy spider failed'),
                    'requested_url': url,
                    'crawl_time': (datetime.now() - start_time).total_seconds(),
                    'crawl_method': 'scrapy_optimized'
                }
            
            # Format result to match API response
            # Handle both dict and list formats
            if isinstance(result, dict):
                career_pages_raw = result.get('career_pages', [])
                total_pages_crawled = result.get('total_pages_crawled', 0)
                career_pages_found = result.get('career_pages_found', 0)
            else:
                # If result is a list, assume it's career_pages
                career_pages_raw = result if isinstance(result, list) else []
                total_pages_crawled = 0
                career_pages_found = len(career_pages_raw)
            
            # Convert career_pages to URL list for API compatibility
            career_pages = []
            career_page_analysis = []
            
            for page_data in career_pages_raw:
                if isinstance(page_data, dict):
                    # Extract URL from dict format
                    page_url = page_data.get('url', '')
                    if page_url:
                        career_pages.append(page_url)
                        
                        # Create analysis from dict data
                        analysis = {
                            'url': page_url,
                            'is_career_page': True,
                            'is_potential': False,
                            'confidence': page_data.get('confidence', 0.8),
                            'rejection_reason': None,
                            'indicators': page_data.get('indicators', ['Scrapy spider detected'])
                        }
                        career_page_analysis.append(analysis)
                elif isinstance(page_data, str):
                    # Direct URL string
                    career_pages.append(page_data)
                    analysis = {
                        'url': page_data,
                        'is_career_page': True,
                        'is_potential': False,
                        'confidence': 0.8,
                        'rejection_reason': None,
                        'indicators': ['Scrapy spider detected']
                    }
                    career_page_analysis.append(analysis)
            
            potential_career_pages = []
            rejected_urls = []
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                len(career_pages), 
                len(potential_career_pages), 
                total_pages_crawled
            )
            
            return {
                'success': True,
                'requested_url': url,
                'career_pages': career_pages,
                'potential_career_pages': potential_career_pages,
                'rejected_urls': rejected_urls,
                'career_page_analysis': career_page_analysis,
                'total_urls_scanned': total_pages_crawled,
                'valid_career_pages': len(career_pages),
                'confidence_score': confidence_score,
                'crawl_time': (datetime.now() - start_time).total_seconds(),
                'crawl_method': 'scrapy_optimized'
            }
            
        except Exception as e:
            logger.error(f"Error in Scrapy career detection: {e}")
            return {
                'success': False,
                'error_message': str(e),
                'requested_url': url,
                'crawl_time': (datetime.now() - start_time).total_seconds(),
                'crawl_method': 'scrapy_optimized'
            }

    def _calculate_confidence_score(self, career_pages: int, potential_pages: int, total_urls: int) -> float:
        """Calculate confidence score for career page detection"""
        if total_urls == 0:
            return 0.0
        
        # Base score from career pages found
        base_score = min(career_pages * 0.3, 1.0)
        
        # Bonus for potential pages
        potential_bonus = min(potential_pages * 0.1, 0.3)
        
        # Coverage score (how many URLs were analyzed)
        coverage_score = min(total_urls / 100, 0.2)
        
        total_score = base_score + potential_bonus + coverage_score
        return min(total_score, 1.0) 