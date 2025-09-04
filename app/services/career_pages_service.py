# app/services/career_pages_service.py
"""
Enhanced career page detection service
"""

import logging
import asyncio
from typing import List, Dict, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime
import re
import os
import json
import socket

from ..utils.constants import CAREER_KEYWORDS_VI, CAREER_SELECTORS, JOB_BOARD_DOMAINS
from ..services.career_detector import filter_career_urls
from .crawler import crawl_single_url
from .scrapy_runner import run_spider
from bs4 import BeautifulSoup

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
        
        # Performance configuration
        self.GLOBAL_TIMEOUT = 60
        self.PER_TASK_TIMEOUT = 12
        self.MAX_CONCURRENCY = 20
        self.HTTP_TIMEOUT = 8.0
        
        # Career keywords for content analysis (NOT for subdomain generation)
        self.CAREER_KEYWORDS = [
            # EN
            r"\bcareers?\b", r"\bjobs?\b", r"\bemployment\b", r"\bjoin\s+us\b",
            r"\bwork\s+with\s+us\b", r"\bopenings?\b", r"\bvacanc(?:y|ies)\b",
            # VI
            r"\btuyển\s*dụng\b", r"\bviệc\s*làm\b", r"\bcơ\s*hội\s*nghề\s*nghiệp\b",
            r"\bgia nhập\b", r"\bứng tuyển\b", r"\btin tuyển\b",
        ]
        self.career_re = re.compile("|".join(self.CAREER_KEYWORDS), flags=re.IGNORECASE)
    
    def _safe_domain(self, base_url: str) -> Tuple[str, str]:
        """Extract root domain and netloc safely"""
        parsed = urlparse(base_url if '://' in base_url else f"https://{base_url}")
        netloc = parsed.netloc or parsed.path
        netloc = netloc.lower().strip().rstrip('/')
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        
        # Simple root domain extraction
        parts = netloc.split('.')
        root = netloc
        if len(parts) >= 3:
            # Keep last 2-3 parts as TLD + SLD
            root = '.'.join(parts[-3:]) if len(parts[-1]) <= 2 else '.'.join(parts[-2:])
        
        return root, netloc
    
    def _is_subdomain_of(self, candidate_host: str, root_domain: str) -> bool:
        """Check if candidate is subdomain of root domain"""
        c = candidate_host.lower().strip('.')
        r = root_domain.lower().strip('.')
        return c.endswith('.' + r) and c != r
    
    def _normalize_url(self, url: str, base: str) -> str:
        """Normalize URL with base"""
        try:
            return urljoin(base, url)
        except Exception:
            return url
    
    def _collect_hosts_from_html(self, html: str, base_url: str) -> Set[str]:
        """Extract all hostnames from HTML content"""
        hosts: Set[str] = set()
        soup = BeautifulSoup(html, 'html.parser')
        
        def _push(u: str):
            if not u:
                return
            absu = self._normalize_url(u, base_url)
            p = urlparse(absu)
            if p.netloc:
                hosts.add(p.netloc.lower())
        
        # Extract from common URL attributes
        for tag, attr in [('a', 'href'), ('link', 'href'), ('script', 'src'),
                          ('img', 'src'), ('form', 'action'), ('source', 'src'),
                          ('iframe', 'src')]:
            for el in soup.find_all(tag):
                _push(el.get(attr))
        
        # Extract from inline scripts/styles
        inline_texts = []
        for el in soup.find_all(['script', 'style']):
            if el.string:
                inline_texts.append(el.string)
        
        blob = '\n'.join(inline_texts)
        for m in re.finditer(r'https?://([A-Za-z0-9\-\._~%]+)(?:[:/][^\s\'"]*)?', blob):
            hosts.add(m.group(1).lower())
        
        return hosts
    
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
            
            # Step 3: Analyze HTML content for career indicators
            html_content = result.get('html', '')
            career_indicators = self._find_career_indicators_in_html(html_content, url)
            
            # Step 4: Filter and analyze URLs
            career_pages = []
            potential_career_pages = []
            rejected_urls = []
            career_page_analysis = []
            
            # Step 5: Add career pages found from HTML analysis
            if career_indicators['career_pages']:
                career_pages.extend(career_indicators['career_pages'])
                logger.info(f"   ✅ Found career pages from HTML analysis: {career_indicators['career_pages']}")
            
            # Step 6: Analyze each URL
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
                logger.info(f"   🔍 Starting subdomain search for: {url}")
                subdomain_results = await self._search_subdomains(url, strict_filtering)
                logger.info(f"   📊 Subdomain search results: {len(subdomain_results['career_pages'])} career pages, {len(subdomain_results['potential_pages'])} potential pages")
                career_pages.extend(subdomain_results['career_pages'])
                potential_career_pages.extend(subdomain_results['potential_pages'])
                career_page_analysis.extend(subdomain_results['analysis'])
            else:
                # 🔍 Enable dynamic subdomain search
                logger.info(f"   🔍 Starting dynamic subdomain search for: {url}")
                subdomain_results = await self._search_subdomains(url, strict_filtering)
                if subdomain_results['career_pages']:
                    logger.info(f"   ✅ Found {len(subdomain_results['career_pages'])} career pages from subdomains")
                    career_pages.extend(subdomain_results['career_pages'])
                if subdomain_results['potential_pages']:
                    logger.info(f"   ⚠️ Found {len(subdomain_results['potential_pages'])} potential pages from subdomains")
                    potential_career_pages.extend(subdomain_results['potential_pages'])
            
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
    
    def _is_xml_response(self, url: str, html_content: str = None) -> bool:
        """Check if response is XML content"""
        if url.lower().endswith(('.xml', '.rss', '.atom')):
            return True
        if html_content and html_content.strip().startswith('<?xml'):
            return True
        return False
    
    async def _parse_sitemap(self, xml_text: str, base_url: str) -> List[str]:
        """Parse sitemap XML and extract job/career URLs"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(xml_text, "xml")
            
            # Extract all <loc> elements
            locs = [loc.get_text(strip=True) for loc in soup.find_all("loc")]
            
            # Filter for job/career related URLs
            job_keywords = [
                "career", "careers", "job", "jobs", "recruit", "tuyen-dung", 
                "viec-lam", "employment", "opportunity", "position", "vacancy"
            ]
            
            job_urls = []
            for url in locs:
                url_lower = url.lower()
                if any(keyword in url_lower for keyword in job_keywords):
                    job_urls.append(url)
            
            logger.info(f"   📋 Sitemap parsing: found {len(locs)} total URLs, {len(job_urls)} job-related")
            return job_urls
            
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to parse sitemap: {e}")
            return []

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
            # Check if this is XML/sitemap content
            if self._is_xml_response(url):
                analysis['rejection_reason'] = 'XML/sitemap content - not a career page'
                return analysis
            
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
            
            # 2. Generic keywords (MEDIUM WEIGHT) - Chỉ match từ riêng biệt, không match substring
            generic_keywords = ['dev', 'software', 'tech', 'ml', 'ai', 'testing', 'it', 'digital']
            path_segments = path.strip('/').split('/')
            for keyword in generic_keywords:
                # Chỉ match nếu keyword là một segment riêng biệt hoặc có dấu gạch ngang
                if (f'/{keyword}' in path or f'{keyword}/' in path or 
                    f'-{keyword}' in path or f'{keyword}-' in path or
                    keyword in path_segments):
                    career_indicators.append(f"Path contains '{keyword}'")
                    analysis['confidence'] += 0.3
            
            # 3. Career patterns (HIGH WEIGHT) - EASIER TO REACH 0.5
            career_patterns = [
                '/career', '/careers', '/jobs', '/employment', 
                '/tuyen-dung', '/viec-lam', '/co-hoi-nghe-nghiep', '/tuyen-nhan-vien',
                '/tuyendung', '/vieclam', '/cohoi', '/tuyennhanvien',
                '/recruitment', '/hiring', '/opportunities', '/positions',
                '/vacancies', '/openings', '/join-us', '/work-with-us',
                '/careers/', '/tuyen-dung/', '/viec-lam/', '/hop-tac-tuyen-dung'
            ]
            for pattern in career_patterns:
                if pattern in path:
                    career_indicators.append(f"Career pattern: {pattern}")
                    analysis['confidence'] += 1.2  # Tăng từ 0.8 lên 1.2 để đảm bảo /careers/ được nhận diện
            
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
                '/blogs': -0.4,        # Tăng penalty
                '/post': -0.4,         # Tăng penalty
                '/posts': -0.4,        # Tăng penalty
                '/article': -0.4,      # Tăng penalty
                '/insights': -0.4,     # Tăng penalty
                '/showcase': -0.4,     # Tăng penalty
                '/case-': -0.4,        # Tăng penalty
                '/about': -0.3,        # Giữ nguyên
                '/contact': -0.3,      # Giữ nguyên
                '/admin': -0.8,        # Tăng penalty
                '/login': -0.8,        # Tăng penalty
                'sitemap.xml': -1.0,   # Strong penalty for sitemap
                'robots.txt': -1.0,    # Strong penalty for robots
                '.xml': -0.8,          # Penalty for XML files
                '.json': -0.8,         # Penalty for JSON files
            }
            
            for pattern, penalty in non_career_patterns.items():
                if pattern in path:
                    analysis['confidence'] += penalty
                    if penalty <= -0.5:  # Strong penalty
                        analysis['rejection_reason'] = f'Strong non-career pattern: {pattern}'
            
            # IMPROVED VALIDATION LOGIC (Cách 2)
            # Nếu confidence rất cao, luôn accept (bỏ qua strict validation)
            if analysis['confidence'] >= 1.0:  # Giảm từ 1.5 xuống 1.0
                analysis['is_career_page'] = True
                analysis['is_potential'] = False
                analysis['rejection_reason'] = None  # Clear rejection reason
            elif analysis['confidence'] >= 0.8:  # Giảm từ 1.0 xuống 0.8
                analysis['is_career_page'] = True
                analysis['is_potential'] = False
            elif analysis['confidence'] >= 0.5:  # Giảm từ 0.6 xuống 0.5
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
            
            # Fallback if netloc is empty (no scheme)
            if not domain:
                domain = parsed.path.strip('/')
                logger.warning(f"   ⚠️ No scheme in URL, using path: {domain}")
            
            # Remove www. prefix for subdomain generation
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Validate domain
            if not domain or '.' not in domain:
                logger.error(f"   ❌ Invalid domain: {domain}")
                return subdomain_results
                
            logger.info(f"   🔍 Parsed domain: {domain} (cleaned from {parsed.netloc})")
            
            # Dynamic subdomain discovery (NO MORE HARDCODED PATTERNS!)
            logger.info(f"   🔍 Starting dynamic subdomain discovery for: {domain}")
            
            # Use smart subdomain search instead of hardcoded patterns
            subdomain_urls = await self._smart_subdomain_search(base_url)
            
            logger.info(f"   🔗 Dynamic discovery found {len(subdomain_urls)} subdomain URLs")
            
            logger.info(f"   🔗 Generated {len(subdomain_urls)} subdomain URLs")
            logger.info(f"   🔗 Sample URLs: {subdomain_urls[:3]}")
            
            # Test subdomain URLs with concurrency limit
            logger.info(f"   🔍 Testing {len(subdomain_urls)} subdomain URLs for {domain}")
            
            # Limit concurrency to avoid overwhelming servers
            semaphore = asyncio.Semaphore(20)  # Max 20 concurrent requests
            
            async def limited_test_subdomain(url):
                async with semaphore:
                    return await self._test_subdomain_url(url, strict_filtering)
            
            tasks = []
            for subdomain_url in subdomain_urls:
                logger.info(f"   🔗 Testing subdomain: {subdomain_url}")






                task = asyncio.create_task(limited_test_subdomain(subdomain_url))
                tasks.append(task)
            
            # Test subdomain URLs with improved timeout handling
            if tasks:
                try:
                    # Use asyncio.wait with timeout to get completed tasks
                    done, pending = await asyncio.wait(
                        tasks, 
                        timeout=60,
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # Cancel pending tasks
                    for task in pending:
                        task.cancel()
                    
                    # Get results from completed tasks
                    results = []
                    for task in done:
                        try:
                            result = await task
                            results.append(result)
                        except Exception as e:
                            logger.warning(f"   ⚠️ Task failed: {e}")
                            results.append({
                                'url': 'unknown',
                                'success': False,
                                'is_career_page': False,
                                'is_potential': False,
                                'rejection_reason': f'Task error: {str(e)}'
                            })
                    
                    logger.info(f"   ✅ Subdomain search completed: {len(results)} completed, {len(pending)} cancelled")
                    
                    # Process results with better error handling
                    for result in results:
                        if isinstance(result, dict):
                            if result.get('success'):
                                if result.get('is_career_page'):
                                    subdomain_results['career_pages'].append(result.get('url', 'unknown'))
                                elif result.get('is_potential'):
                                    subdomain_results['potential_pages'].append(result.get('url', 'unknown'))
                                subdomain_results['analysis'].append(result)
                            else:
                                logger.warning(f"   ⚠️ Subdomain failed: {result.get('rejection_reason', 'Unknown error')}")
                        else:
                            logger.warning(f"   ⚠️ Unexpected result type: {type(result)}")
                except Exception as e:
                    logger.error(f"   ❌ Subdomain search error: {e}")
                    results = []
            
        except Exception as e:
            logger.error(f"Error in subdomain search: {e}")
        
        return subdomain_results
    
    async def _test_subdomain_url(self, url: str, strict_filtering: bool) -> Dict:
        """Test if a subdomain URL is accessible and contains career content"""
        try:
            logger.info(f"      🔗 Testing subdomain URL: {url}")
            result = await crawl_single_url(url)
            
            if result['success']:
                logger.info(f"      ✅ Subdomain crawl successful: {url}")
                analysis = await self._analyze_url_for_career(url, url, strict_filtering)
                analysis['success'] = True
                analysis['url'] = url
                return analysis
            else:
                logger.info(f"      ❌ Subdomain crawl failed: {url}")
                return {
                    'url': url,
                    'success': False,
                    'is_career_page': False,
                    'is_potential': False,
                    'rejection_reason': 'Failed to crawl'
                }
                
        except Exception as e:
            logger.error(f"      ❌ Subdomain crawl error for {url}: {e}")
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
            all_job_urls = []  # Collect all job URLs from career pages
            
            for page_data in career_pages_raw:
                if isinstance(page_data, dict):
                    # Extract URL from dict format
                    page_url = page_data.get('url', '')
                    if page_url:
                        career_pages.append(page_url)
                        
                        # Extract job URLs from this career page
                        job_urls = page_data.get('job_urls', [])
                        if job_urls:
                            all_job_urls.extend(job_urls)
                            logger.info(f"   🔗 Career page {page_url} has {len(job_urls)} job URLs")
                        
                        # Create analysis from dict data
                        analysis = {
                            'url': page_url,
                            'is_career_page': True,
                            'is_potential': False,
                            'confidence': page_data.get('confidence', 0.8),
                            'rejection_reason': None,
                            'indicators': page_data.get('indicators', ['Scrapy spider detected']),
                            'job_urls': job_urls
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
                        'indicators': ['Scrapy spider detected'],
                        'job_urls': []
                    }
                    career_page_analysis.append(analysis)
            
            # Remove duplicate job URLs
            unique_job_urls = list(set(all_job_urls))
            logger.info(f"   📊 Total unique job URLs found: {len(unique_job_urls)}")
            
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
                'crawl_method': 'scrapy_optimized',
                'job_urls': unique_job_urls,  # Include filtered job URLs
                'total_jobs_found': len(unique_job_urls)
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

    def _find_career_indicators_in_html(self, html_content: str, base_url: str) -> Dict:
        """
        Find career indicators in HTML content using text analysis
        """
        career_indicators = {
            'career_pages': [],
            'career_texts': [],
            'confidence': 0.0
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Vietnamese career keywords
            vietnamese_career_keywords = [
                'tuyển dụng', 'tuyển nhân viên', 'cơ hội nghề nghiệp', 'việc làm',
                'tuyển dụng nhân sự', 'cơ hội việc làm', 'tuyển dụng nhân viên',
                'tuyển dụng kỹ sư', 'tuyển dụng developer', 'tuyển dụng lập trình viên'
            ]
            
            # English career keywords
            english_career_keywords = [
                'career', 'careers', 'job', 'jobs', 'employment', 'hiring',
                'recruitment', 'join us', 'work with us', 'opportunities',
                'positions', 'vacancies', 'openings'
            ]
            
            all_career_keywords = vietnamese_career_keywords + english_career_keywords
            
            # Find all links with career-related text
            career_links = []
            for link in soup.find_all('a', href=True):
                link_text = link.get_text().strip().lower()
                href = link.get('href', '')
                
                # Check if link text contains career keywords
                if any(keyword in link_text for keyword in all_career_keywords):
                    career_links.append({
                        'text': link.get_text().strip(),
                        'href': href,
                        'full_url': urljoin(base_url, href)
                    })
            
            # Find career pages from links
            for link_info in career_links:
                full_url = link_info['full_url']
                if full_url.startswith(('http://', 'https://')):
                    career_indicators['career_pages'].append(full_url)
                    career_indicators['career_texts'].append(link_info['text'])
            
            # Calculate confidence based on findings
            if career_indicators['career_pages']:
                career_indicators['confidence'] = min(len(career_indicators['career_pages']) * 0.3, 1.0)
            
            logger.info(f"   🔍 Found {len(career_indicators['career_pages'])} career pages from HTML analysis")
            
        except Exception as e:
            logger.warning(f"   ⚠️ Error analyzing HTML for career indicators: {e}")
        
        return career_indicators

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

    async def _smart_subdomain_search(self, base_url: str) -> List[str]:
        """
        Smart subdomain search with 3-tier approach:
        1. Dynamic discovery from base domain content
        2. DNS/CT enumeration (if available)
        3. Minimal fallback from config (NO hardcoding)
        """
        root_domain, netloc = self._safe_domain(base_url)
        subdomains: List[str] = []
        
        logger.info(f"   🔍 Smart subdomain search for root domain: {root_domain}")
        
        # 1) Dynamic discovery (primary)
        discovered = await self._discover_subdomains_dynamically(base_url)
        subdomains.extend(discovered)
        logger.info(f"   ✅ Dynamic discovery found: {len(discovered)} subdomains")
        
        # 2) DNS/CT enumeration (secondary) - placeholder for future
        # dns_found = await self._enumerate_subdomains_dns(root_domain)
        # subdomains.extend(dns_found)
        
        # Dedup early
        subdomains = sorted(set(subdomains))
        
        # 3) Minimal fallback (ONLY IF NEEDED; NO hardcoding in code)
        if not subdomains:
            fallback = self._get_minimal_fallback_patterns(root_domain)
            subdomains.extend(fallback)
            logger.info(f"   ⚠️ Using minimal fallback: {len(fallback)} patterns")
        
        # Final dedup
        final_subdomains = sorted(set(subdomains))
        logger.info(f"   🎯 Total unique subdomains found: {len(final_subdomains)}")
        
        return final_subdomains
    
    async def _discover_subdomains_dynamically(self, base_url: str) -> List[str]:
        """
        Discover subdomains from base domain HTML content
        """
        root_domain, netloc = self._safe_domain(base_url)
        start_url = base_url if '://' in base_url else f"https://{netloc}"
        
        candidates: Set[str] = set()
        alive_urls: List[str] = []
        
        try:
            # Fetch base HTML
            result = await crawl_single_url(start_url)
            if not result or not result.get('success') or not result.get('html'):
                logger.warning(f"   ⚠️ Failed to fetch base domain HTML")
                return []
            
            html = result.get('html', '')
            logger.info(f"   📄 Base domain HTML length: {len(html)}")
            
            # Collect hosts from HTML
            hosts = self._collect_hosts_from_html(html, start_url)
            logger.info(f"   🔍 Found {len(hosts)} total hosts in HTML")
            
            # Filter: only keep subdomains of root_domain
            for h in hosts:
                if self._is_subdomain_of(h, root_domain):
                    candidates.add(h)
            
            logger.info(f"   🎯 Filtered to {len(candidates)} candidate subdomains")
            
            if not candidates:
                return []
            
            # Validate subdomains with concurrency limit
            sem = asyncio.Semaphore(self.MAX_CONCURRENCY)
            
            async def limited_validate(host: str):
                async with sem:
                    return await self._validate_host_alive(host)
            
            # Create tasks explicitly to avoid coroutine error
            tasks = [asyncio.create_task(limited_validate(h)) for h in candidates]
            
            # Use asyncio.wait with timeout
            done, pending = await asyncio.wait(tasks, timeout=self.GLOBAL_TIMEOUT)
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Collect results
            for task in done:
                try:
                    result = task.result()
                    if result and result.get('alive'):
                        alive_urls.append(result.get('url', ''))
                except Exception as e:
                    logger.warning(f"   ⚠️ Task failed: {e}")
                    continue
            
            logger.info(f"   ✅ Validation completed: {len(alive_urls)} alive subdomains")
            
        except Exception as e:
            logger.error(f"   ❌ Dynamic discovery error: {e}")
            # Don't re-raise the exception, just return empty list
            # This prevents the entire career page detection from failing
        
        return alive_urls
    
    async def _validate_host_alive(self, host: str) -> Dict:
        """
        Validate if host is alive (DNS + HTTP) with timeout
        """
        try:
            # Add timeout wrapper to prevent hanging
            async def validate_with_timeout():
                # Simple validation using existing crawl_single_url
                url = f"https://{host}"
                result = await crawl_single_url(url)
                
                if result and result.get('success'):
                    return {
                        'alive': True,
                        'url': url,
                        'host': host
                    }
                else:
                    # Try HTTP as fallback
                    url = f"http://{host}"
                    result = await crawl_single_url(url)
                    
                    if result and result.get('success'):
                        return {
                            'alive': True,
                            'url': url,
                            'host': host
                        }
                
                return {
                    'alive': False,
                    'url': url,
                    'host': host
                }
            
            # Use asyncio.wait_for with timeout
            result = await asyncio.wait_for(validate_with_timeout(), timeout=10.0)
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"      ⚠️ Host validation timeout for {host}")
            return {
                'alive': False,
                'url': f"https://{host}",
                'host': host,
                'error': 'timeout'
            }
        except Exception as e:
            logger.warning(f"      ⚠️ Host validation failed for {host}: {e}")
            return {
                'alive': False,
                'url': f"https://{host}",
                'host': host,
                'error': str(e)
            }
    
    def _get_minimal_fallback_patterns(self, domain: str) -> List[str]:
        """
        NO hardcoding in code - read from ENV or config
        """
        # Read from environment variable
        raw = os.getenv("CRAWLER_FALLBACK_SUBDOMAINS", "").strip()
        if not raw:
            logger.info(f"   ℹ️ No fallback patterns configured - returning empty list")
            return []
        
        # Parse comma-separated patterns
        tags = [t.strip().lower() for t in raw.split(',') if t.strip()]
        urls = [f"https://{t}.{domain}" for t in tags]
        
        logger.info(f"   🔧 Using fallback patterns from ENV: {tags}")
        return urls 