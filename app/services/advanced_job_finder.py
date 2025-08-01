# app/services/advanced_job_finder.py
"""
Advanced job finding service for career pages
"""

import logging
import asyncio
import json
import re
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .crawler import crawl_single_url
from .hidden_job_extractor import HiddenJobExtractor
from .job_analyzer import JobAnalyzer

logger = logging.getLogger(__name__)

class AdvancedJobFinder:
    """Advanced service for finding jobs in career pages"""
    
    def __init__(self):
        self.hidden_job_extractor = HiddenJobExtractor()
        self.job_analyzer = JobAnalyzer()
        
        # Job detection patterns
        self.job_patterns = {
            'title_patterns': [
                r'job[-\s]?title', r'position[-\s]?title', r'role[-\s]?title',
                r'tên[-\s]?công[-\s]?việc', r'vị[-\s]?trí[-\s]?tuyển[-\s]?dụng'
            ],
            'link_patterns': [
                r'/job/', r'/career/', r'/position/', r'/vacancy/',
                r'/tuyen-dung/', r'/viec-lam/', r'/co-hoi/', r'/apply/'
            ],
            'keywords': [
                'tuyển dụng', 'việc làm', 'cơ hội', 'vị trí', 'công việc',
                'job', 'position', 'vacancy', 'opening', 'opportunity'
            ]
        }
    
    async def find_jobs_advanced(self, career_url: str, max_jobs: int = 100) -> Dict:
        """Advanced job finding with multiple strategies"""
        start_time = datetime.now()
        
        try:
            logger.info(f"🔍 Advanced job finding for: {career_url}")
            
            all_jobs = []
            
            # Strategy 1: Basic extraction
            basic_jobs = await self._basic_job_extraction(career_url, max_jobs)
            all_jobs.extend(basic_jobs)
            
            # Strategy 2: Hidden job extraction
            hidden_jobs = await self._hidden_job_extraction(career_url, max_jobs)
            all_jobs.extend(hidden_jobs)
            
            # Strategy 3: Pattern-based search
            pattern_jobs = await self._pattern_based_search(career_url, max_jobs)
            all_jobs.extend(pattern_jobs)
            
            # Strategy 4: Deep link discovery
            deep_jobs = await self._deep_link_discovery(career_url, max_jobs)
            all_jobs.extend(deep_jobs)
            
            # Deduplicate and enhance
            unique_jobs = self._deduplicate_jobs(all_jobs)
            enhanced_jobs = await self._enhance_jobs(unique_jobs, career_url)
            ranked_jobs = self._rank_jobs_by_quality(enhanced_jobs)
            
            crawl_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'career_url': career_url,
                'crawl_time': crawl_time,
                'total_jobs_found': len(ranked_jobs),
                'jobs': ranked_jobs,
                'statistics': self._generate_statistics(ranked_jobs)
            }
            
        except Exception as e:
            logger.error(f"Error in advanced job finding: {e}")
            return {
                'success': False,
                'error_message': str(e),
                'career_url': career_url,
                'jobs_found': 0
            }
    
    async def _basic_job_extraction(self, career_url: str, max_jobs: int) -> List[Dict]:
        """Basic job extraction using existing service"""
        try:
            from .job_extractor import extract_jobs_from_page
            result = extract_jobs_from_page(career_url, max_jobs)
            if result.get('success'):
                logger.info(f"   ✅ Basic extraction: {len(result.get('jobs', []))} jobs")
                return result.get('jobs', [])
        except Exception as e:
            logger.warning(f"   ⚠️ Basic extraction failed: {e}")
        return []
    
    async def _hidden_job_extraction(self, career_url: str, max_jobs: int) -> List[Dict]:
        """Hidden job extraction"""
        try:
            result = await self.hidden_job_extractor.extract_hidden_jobs_from_page(career_url)
            if result.get('success'):
                logger.info(f"   ✅ Hidden extraction: {len(result.get('jobs', []))} jobs")
                return result.get('jobs', [])
        except Exception as e:
            logger.warning(f"   ⚠️ Hidden extraction failed: {e}")
        return []
    
    async def _pattern_based_search(self, career_url: str, max_jobs: int) -> List[Dict]:
        """Pattern-based job search"""
        try:
            result = await crawl_single_url(career_url)
            if not result['success']:
                return []
            
            html_content = result.get('html', '')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            job_elements = self._find_job_elements(soup)
            jobs = []
            
            for element in job_elements[:max_jobs]:
                job = self._extract_job_from_element(element, career_url)
                if job:
                    jobs.append(job)
            
            logger.info(f"   ✅ Pattern search: {len(jobs)} jobs")
            return jobs
            
        except Exception as e:
            logger.warning(f"   ⚠️ Pattern search failed: {e}")
            return []
    
    def _find_job_elements(self, soup: BeautifulSoup) -> List:
        """Find job elements using patterns"""
        job_elements = []
        
        # Find by class patterns
        class_patterns = [
            '[class*="job"]', '[class*="career"]', '[class*="position"]',
            '[class*="vacancy"]', '[class*="opening"]'
        ]
        
        for pattern in class_patterns:
            elements = soup.select(pattern)
            job_elements.extend(elements)
        
        # Find by ID patterns
        id_patterns = [
            '[id*="job"]', '[id*="career"]', '[id*="position"]'
        ]
        
        for pattern in id_patterns:
            elements = soup.select(pattern)
            job_elements.extend(elements)
        
        # Find by text content
        for keyword in self.job_patterns['keywords']:
            elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for element in elements:
                if element.parent:
                    job_elements.append(element.parent)
        
        return list(set(job_elements))
    
    def _extract_job_from_element(self, element, base_url: str) -> Optional[Dict]:
        """Extract job from element"""
        try:
            job = {
                'title': '',
                'company': '',
                'location': '',
                'job_type': 'Full-time',
                'salary': '',
                'posted_date': '',
                'url': '',
                'description': ''
            }
            
            # Extract title
            title_element = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if title_element:
                job['title'] = title_element.get_text().strip()
            
            # Extract link
            link_element = element.find('a')
            if link_element and link_element.get('href'):
                job['url'] = urljoin(base_url, link_element.get('href'))
            
            # Extract description
            desc_element = element.find(['p', 'div', 'span'])
            if desc_element:
                job['description'] = desc_element.get_text().strip()[:500]
            
            return job if job['title'] else None
            
        except Exception as e:
            logger.warning(f"Error extracting job from element: {e}")
            return None
    
    async def _deep_link_discovery(self, career_url: str, max_jobs: int) -> List[Dict]:
        """Deep link discovery for job pages"""
        try:
            result = await crawl_single_url(career_url)
            if not result['success']:
                return []
            
            all_links = result.get('urls', [])
            job_links = [link for link in all_links if self._is_job_link(link)]
            
            jobs = []
            for job_link in job_links[:max_jobs]:
                job = await self._extract_job_from_link(job_link)
                if job:
                    jobs.append(job)
            
            logger.info(f"   ✅ Deep discovery: {len(jobs)} jobs")
            return jobs
            
        except Exception as e:
            logger.warning(f"   ⚠️ Deep discovery failed: {e}")
            return []
    
    def _is_job_link(self, url: str) -> bool:
        """Check if URL is a job link"""
        url_lower = url.lower()
        
        for pattern in self.job_patterns['link_patterns']:
            if re.search(pattern, url_lower):
                return True
        
        for keyword in self.job_patterns['keywords']:
            if keyword in url_lower:
                return True
        
        return False
    
    async def _extract_job_from_link(self, job_url: str) -> Optional[Dict]:
        """Extract job from job link"""
        try:
            result = await crawl_single_url(job_url)
            if not result['success']:
                return None
            
            html_content = result.get('html', '')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            job = {
                'title': '',
                'company': '',
                'location': '',
                'job_type': 'Full-time',
                'salary': '',
                'posted_date': '',
                'url': job_url,
                'description': ''
            }
            
            # Extract title
            title_selectors = ['h1', '.job-title', '.position-title']
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    job['title'] = title_element.get_text().strip()
                    break
            
            # Extract description
            desc_selectors = ['.job-description', '.description', 'p']
            for selector in desc_selectors:
                desc_element = soup.select_one(selector)
                if desc_element:
                    job['description'] = desc_element.get_text().strip()[:1000]
                    break
            
            return job if job['title'] else None
            
        except Exception as e:
            logger.warning(f"Error extracting job from link {job_url}: {e}")
            return None
    
    async def _enhance_jobs(self, jobs: List[Dict], career_url: str) -> List[Dict]:
        """Enhance jobs with analysis"""
        enhanced_jobs = []
        
        for job in jobs:
            enhanced_job = job.copy()
            
            # Add analysis
            analysis = self.job_analyzer.analyze_job(job)
            enhanced_job['analysis'] = analysis
            enhanced_job['quality_score'] = analysis.get('quality_scores', {}).get('overall', 0)
            enhanced_job['source_url'] = career_url
            
            enhanced_jobs.append(enhanced_job)
        
        return enhanced_jobs
    
    def _rank_jobs_by_quality(self, jobs: List[Dict]) -> List[Dict]:
        """Rank jobs by quality score"""
        ranked_jobs = sorted(jobs, key=lambda x: x.get('quality_score', 0), reverse=True)
        
        for i, job in enumerate(ranked_jobs):
            job['rank'] = i + 1
        
        return ranked_jobs
    
    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            title = job.get('title', '').lower().strip()
            company = job.get('company', '').lower().strip()
            key = f"{title}|{company}"
            
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _generate_statistics(self, jobs: List[Dict]) -> Dict:
        """Generate job statistics"""
        job_types = {}
        locations = {}
        
        for job in jobs:
            job_type = job.get('job_type', 'Unknown')
            job_types[job_type] = job_types.get(job_type, 0) + 1
            
            location = job.get('location', 'Unknown')
            locations[location] = locations.get(location, 0) + 1
        
        return {
            'job_types': job_types,
            'locations': locations,
            'quality_distribution': {
                'excellent': len([j for j in jobs if j.get('quality_score', 0) > 0.8]),
                'good': len([j for j in jobs if 0.6 < j.get('quality_score', 0) <= 0.8]),
                'fair': len([j for j in jobs if 0.4 < j.get('quality_score', 0) <= 0.6]),
                'poor': len([j for j in jobs if j.get('quality_score', 0) <= 0.4])
            }
        } 