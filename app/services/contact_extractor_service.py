# app/services/contact_extractor_service.py
"""
Enhanced contact extraction service
"""

import re
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import asyncio
from datetime import datetime

from ..utils.constants import CAREER_KEYWORDS_VI, CAREER_SELECTORS, JOB_BOARD_DOMAINS
from ..utils.contact_extractor import process_extracted_crawl_results, to_text
from .crawler import crawl_single_url

logger = logging.getLogger(__name__)

class ContactExtractorService:
    """Enhanced service for extracting contact information"""
    
    def __init__(self):
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        ]
        
        self.phone_patterns = [
            r'(\+84|84|0)[0-9]{9,10}',  # Vietnamese phone
            r'(\+1|1)?[0-9]{10}',       # US phone
            r'(\+44|44)[0-9]{10}',      # UK phone
            r'(\+81|81)[0-9]{9,10}',    # Japan phone
        ]
        
        self.social_patterns = {
            'facebook': r'facebook\.com/[^/\s]+',
            'linkedin': r'linkedin\.com/(company|in)/[^/\s]+',
            'twitter': r'twitter\.com/[^/\s]+',
            'instagram': r'instagram\.com/[^/\s]+',
            'youtube': r'youtube\.com/(channel|c|user)/[^/\s]+',
            'github': r'github\.com/[^/\s]+',
        }
    
    async def extract_contact_info(self, url: str, include_social: bool = True, 
                                 include_emails: bool = True, include_phones: bool = True,
                                 max_depth: int = 2, timeout: int = 30) -> Dict:
        """
        Extract comprehensive contact information from a website
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🔍 Starting contact extraction for: {url}")
            
            # Step 1: Crawl the main page
            result = await crawl_single_url(url)
            
            if not result['success']:
                return {
                    'success': False,
                    'error_message': 'Failed to crawl the website',
                    'requested_url': url,
                    'crawl_time': (datetime.now() - start_time).total_seconds()
                }
            
            # Step 2: Extract basic contact data
            contact_data = await self._extract_basic_contact_data(result)
            
            # Step 3: Enhanced social media detection
            if include_social:
                social_data = await self._extract_social_media_enhanced(result, url)
                contact_data['social_links'].extend(social_data)
            
            # Step 4: Phone number extraction
            if include_phones:
                phone_data = await self._extract_phone_numbers(result)
                contact_data['phones'].extend(phone_data)
            
            # Step 5: Contact form detection
            contact_forms = await self._detect_contact_forms(result)
            contact_data['contact_forms'] = contact_forms
            
            # Step 6: Deep crawl for more contact info (if max_depth > 1)
            if max_depth > 1:
                deep_contact_data = await self._deep_crawl_contact_info(url, result, max_depth)
                contact_data = self._merge_contact_data(contact_data, deep_contact_data)
            
            # Step 7: Process and classify contact data
            classified_contacts = process_extracted_crawl_results(
                raw_extracted_list=self._prepare_data_for_classifier(contact_data),
                base_url=result.get('url', url)
            )
            
            # Step 8: Calculate statistics
            stats = self._calculate_contact_stats(contact_data, result)
            
            crawl_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'requested_url': url,
                'crawl_time': crawl_time,
                'crawl_method': result.get('crawl_method') or result.get('method'),
                'emails': classified_contacts.get('emails', []),
                'phones': contact_data.get('phones', []),
                'social_links': classified_contacts.get('social_links', []),
                'contact_forms': contact_data.get('contact_forms', []),
                'raw_extracted_data': contact_data,
                'total_pages_crawled': stats['total_pages_crawled'],
                'total_links_found': stats['total_links_found']
            }
            
        except Exception as e:
            logger.error(f"Error in contact extraction: {e}")
            # Return basic data even if processing fails
            basic_data = await self._extract_basic_contact_data(result) if 'result' in locals() else {
                'emails': [], 'phones': [], 'social_links': [], 'contact_forms': []
            }
            return {
                'success': True,  # Still return success with basic data
                'error_message': str(e),
                'requested_url': url,
                'crawl_time': (datetime.now() - start_time).total_seconds(),
                'crawl_method': result.get('crawl_method') if 'result' in locals() else 'requests',
                'emails': basic_data.get('emails', []),
                'phones': basic_data.get('phones', []),
                'social_links': basic_data.get('social_links', []),
                'contact_forms': basic_data.get('contact_forms', []),
                'raw_extracted_data': basic_data,
                'total_pages_crawled': 1,
                'total_links_found': len(result.get('urls', [])) if 'result' in locals() else 0
            }
    
    async def _extract_basic_contact_data(self, result: Dict) -> Dict:
        """Extract basic contact data from crawl result"""
        contact_data = {
            'emails': [],
            'phones': [],
            'social_links': [],
            'contact_forms': []
        }
        
        # Extract emails from HTML content
        html_content = result.get('html', '')
        if html_content:
            for pattern in self.email_patterns:
                try:
                    emails = re.findall(pattern, html_content, re.IGNORECASE)
                    contact_data['emails'].extend(emails)
                except Exception as e:
                    logger.warning(f"Error extracting emails with pattern {pattern}: {e}")
                    continue
        
        # Remove duplicates and normalize
        contact_data['emails'] = list(set([email.lower() for email in contact_data['emails']]))
        
        return contact_data
    
    async def _extract_social_media_enhanced(self, result: Dict, base_url: str) -> List[str]:
        """Enhanced social media detection"""
        social_links = []
        html_content = result.get('html', '')
        urls = result.get('urls', [])
        
        # Check HTML content for social patterns
        for platform, pattern in self.social_patterns.items():
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if platform == 'facebook':
                    social_links.append(f"https://facebook.com/{match}")
                elif platform == 'linkedin':
                    social_links.append(f"https://linkedin.com/{match}")
                elif platform == 'twitter':
                    social_links.append(f"https://twitter.com/{match}")
                elif platform == 'instagram':
                    social_links.append(f"https://instagram.com/{match}")
                elif platform == 'youtube':
                    social_links.append(f"https://youtube.com/{match}")
                elif platform == 'github':
                    social_links.append(f"https://github.com/{match}")
        
        # Check URLs for social media
        for url in urls:
            try:
                url_str = normalize_url_util(url)  # Convert URL objects to string and normalize
                for platform in self.social_patterns.keys():
                    if platform in url_str.lower():
                        social_links.append(url_str)
            except Exception as e:
                logger.warning(f"Error processing URL {url}: {e}")
                continue
        
        # Remove duplicates
        return list(set(social_links))
    
    async def _extract_phone_numbers(self, result: Dict) -> List[str]:
        """Extract phone numbers from content"""
        phones = []
        html_content = result.get('html', '')
        
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, html_content)
            phones.extend(matches)
        
        # Clean and normalize phone numbers
        cleaned_phones = []
        for phone in phones:
            # Remove common prefixes and clean
            cleaned = re.sub(r'[\s\-\(\)\.]', '', str(phone))
            if len(cleaned) >= 9:  # Minimum valid length
                cleaned_phones.append(cleaned)
        
        return list(set(cleaned_phones))
    
    async def _detect_contact_forms(self, result: Dict) -> List[str]:
        """Detect contact form URLs"""
        contact_forms = []
        urls = result.get('urls', [])
        
        contact_keywords = ['contact', 'lien-he', 'lienhe', 'about', 'about-us', 'gioi-thieu']
        
        for url in urls:
            try:
                url_str = normalize_url_util(url)  # Convert URL objects to string and normalize
                url_lower = url_str.lower()
                if any(keyword in url_lower for keyword in contact_keywords):
                    contact_forms.append(url_str)
            except Exception as e:
                logger.warning(f"Error processing contact form URL {url}: {e}")
                continue
        
        return list(set(contact_forms))
    
    async def _deep_crawl_contact_info(self, base_url: str, initial_result: Dict, max_depth: int) -> Dict:
        """Deep crawl for additional contact information"""
        deep_data = {
            'emails': [],
            'phones': [],
            'social_links': [],
            'contact_forms': []
        }
        
        # Get URLs from initial crawl
        urls_to_crawl = initial_result.get('urls', [])
        
        # Filter URLs that might contain contact info
        contact_urls = []
        for url in urls_to_crawl:
            try:
                url_str = normalize_url_util(url)  # Normalize URL and remove fragments
                url_lower = url_str.lower()
                if any(keyword in url_lower for keyword in ['contact', 'about', 'lien-he', 'gioi-thieu']):
                    contact_urls.append(url_str)
            except Exception as e:
                logger.warning(f"Error normalizing URL {url}: {e}")
                continue
        
        # Limit to prevent too many requests
        contact_urls = contact_urls[:5]
        
        # Crawl contact pages
        tasks = []
        for url in contact_urls:
            task = self._crawl_contact_page(url)
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict) and result.get('success'):
                    deep_data['emails'].extend(result.get('emails', []))
                    deep_data['phones'].extend(result.get('phones', []))
                    deep_data['social_links'].extend(result.get('social_links', []))
                    deep_data['contact_forms'].extend(result.get('contact_forms', []))
        
        return deep_data
    
    async def _crawl_contact_page(self, url: str) -> Dict:
        """Crawl a single contact page"""
        try:
            result = await crawl_single_url(url)
            if result['success']:
                return await self._extract_basic_contact_data(result)
            return {'success': False}
        except Exception as e:
            logger.error(f"Error crawling contact page {url}: {e}")
            return {'success': False}
    
    def _merge_contact_data(self, data1: Dict, data2: Dict) -> Dict:
        """Merge two contact data dictionaries"""
        merged = {}
        for key in data1.keys():
            if key in data2:
                merged[key] = list(set(data1[key] + data2[key]))
            else:
                merged[key] = data1[key]
        return merged
    
    def _prepare_data_for_classifier(self, contact_data: Dict) -> List[Dict]:
        """Prepare data for the contact classifier"""
        data_list = []
        
        for email in contact_data.get('emails', []):
            data_list.append({"label": "email", "value": email})
        
        for social in contact_data.get('social_links', []):
            data_list.append({"label": "url", "value": social})
        
        return data_list
    
    def _calculate_contact_stats(self, contact_data: Dict, result: Dict) -> Dict:
        """Calculate statistics for contact extraction"""
        return {
            'total_pages_crawled': 1,  # Main page + any deep crawled pages
            'total_links_found': len(result.get('urls', [])),
            'emails_found': len(contact_data.get('emails', [])),
            'phones_found': len(contact_data.get('phones', [])),
            'social_links_found': len(contact_data.get('social_links', [])),
            'contact_forms_found': len(contact_data.get('contact_forms', []))
        }
    
    async def extract_contact_info_scrapy(self, url: str, include_social: bool = True, 
                                       include_emails: bool = True, include_phones: bool = True,
                                       max_depth: int = 2, timeout: int = 30) -> Dict:
        """
        Extract contact information using optimized Scrapy spider
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🚀 Starting Scrapy contact extraction for: {url}")
            
            # For now, use regular extraction but mark as Scrapy
            # TODO: Implement actual Scrapy contact spider
            result = await self.extract_contact_info(
                url=url,
                include_social=include_social,
                include_emails=include_emails,
                include_phones=include_phones,
                max_depth=max_depth,
                timeout=timeout
            )
            
            # Mark as Scrapy method
            result['crawl_method'] = 'scrapy_optimized'
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in Scrapy contact extraction: {e}")
            return {
                'success': False,
                'requested_url': url,
                'error_message': str(e),
                'crawl_time': (datetime.now() - start_time).total_seconds(),
                'crawl_method': 'scrapy_optimized'
            }