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

# utils for phone extraction
import re

WS_CLASS = r"\s\u00A0\u2000-\u200B"            # space + NBSP + zero-width range
SEP_CLASS = rf"[{WS_CLASS}\.\-\(\)]"          # cho phép . - ( ) và các khoảng trắng unicode
SEP = rf"{SEP_CLASS}*"                        # 0+ ký tự phân tách

def normalize_text(s: str) -> str:
    # gom mọi loại khoảng trắng về 1 space
    return re.sub(rf"[{WS_CLASS}]+", " ", s).strip()

def clean_phone(candidate: str) -> str | None:
    # giữ + và số
    s = re.sub(r"[^\d+]", "", candidate)
    if s.startswith("+84"):
        s = "0" + s[3:]
    s = re.sub(r"\D", "", s)
    # VN: di động 10 số; cố định 10–11 số (tùy mã vùng)
    return s if 10 <= len(s) <= 11 else None

from ..utils.constants import CAREER_KEYWORDS_VI, CAREER_SELECTORS, JOB_BOARD_DOMAINS
from ..utils.contact_extractor import process_extracted_crawl_results, to_text
from ..utils.text import normalize_url as normalize_url_util
from .crawler import crawl_single_url
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class ContactExtractorService:
    """Enhanced service for extracting contact information"""
    
    def __init__(self):
        self.email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        ]
        
        # Regex VN (không dùng capture, cho phép phân tách linh hoạt)
        from ..utils.text import SEP
        self.VN_PHONE_RX = re.compile(
            rf"(?<!\d)(?:\+?84|0)(?:{SEP}\d){{8,10}}(?!\d)"
        )
        
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
            
            # Step 2: Extract basic contact data (prioritize footer)
            contact_data = self._extract_basic_contact_data(result)
            
            # Step 2.5: PRIORITIZE FOOTER CONTACT INFO (sử dụng utils mới)
            logger.info(f"🔍 Prioritizing footer contact extraction...")
            try:
                from ..utils.contact_footer import extract_footer_contacts_from_html
                footer_contact_data = extract_footer_contacts_from_html(result.get('html', ''))
                if footer_contact_data and (footer_contact_data.get('phones') or footer_contact_data.get('emails')):
                    logger.info(f"✅ Found footer contact info: {footer_contact_data}")
                    # Merge footer data with priority
                    contact_data = self._merge_contact_data_with_priority(footer_contact_data, contact_data)
                else:
                    logger.info("⚠️ No footer contact info found")
            except Exception as e:
                logger.warning(f"⚠️ Footer extraction failed: {e}")
                # Fallback to old method
                footer_contact_data = await self._extract_footer_contact_info(result, url)
                if footer_contact_data:
                    contact_data = self._merge_contact_data_with_priority(footer_contact_data, contact_data)
            
            # Step 3: Enhanced social media detection
            if include_social:
                social_data = self._extract_social_media_enhanced(result, url)
                contact_data['social_links'].extend(social_data)
            
            # Step 4: Phone number extraction
            if include_phones:
                logger.info(f"📞 Extracting phone numbers from HTML content (length: {len(result.get('html', ''))})")
                phone_data = await self._extract_phone_numbers(result)
                contact_data['phones'].extend(phone_data)
                logger.info(f"📞 Phone extraction result: {phone_data}")
            
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
            basic_data = self._extract_basic_contact_data(result) if 'result' in locals() else {
                'emails': [], 'phones': [], 'contact_forms': []
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

    async def _extract_footer_contact_info(self, result: Dict, base_url: str) -> Dict:
        """Extract contact information from footer section with priority"""
        footer_data = {'emails': [], 'phones': [], 'social_links': [], 'contact_forms': []}
        try:
            html = result.get('html', '') or ''
            soup = BeautifulSoup(html, "lxml")

            # chọn footer linh hoạt
            footer = self.pick_footer_node(soup)

            # 1) lấy số từ tel: trước
            tel_phones = []
            for a in footer.select('a[href^="tel:"]'):
                number = a.get('href', '')[4:]
                n = clean_phone(number)
                if n and n not in tel_phones:
                    tel_phones.append(n)

            # 2) lấy từ text node
            text = normalize_text(footer.get_text(" ", strip=True))
            text_phones = self._extract_phones_from_text(text)

            phones = list(dict.fromkeys(tel_phones + text_phones))  # dedupe giữ thứ tự
            footer_data['phones'].extend(phones)

            # emails (giữ logic cũ của bạn)
            footer_emails = self._extract_emails_from_footer(html)
            footer_data['emails'].extend(footer_emails)

            # log debug chi tiết
            preview = (normalize_text(footer.get_text(" ", strip=True))[:200])
            logger.debug("🦶 footer tag=%s preview=%s", getattr(footer,'name',None), preview)
            logger.info("📦 footer phones (tel+text) = %s", phones)
            return footer_data
        except Exception as e:
            logger.warning(f"⚠️ Footer contact extraction failed: {e}")
            return footer_data

    def _extract_phone_numbers_from_footer(self, html_content: str) -> List[str]:
        """Extract phone numbers specifically from footer content"""
        soup = BeautifulSoup(html_content or "", "lxml")
        footer = self.pick_footer_node(soup)
        text = normalize_text(footer.get_text(" ", strip=True))
        # tìm theo iterator để luôn lấy full match
        cands = [m.group(0) for m in self.VN_PHONE_RX.finditer(text)]
        out: list[str] = []
        for c in cands:
            n = clean_phone(c)
            if n and n not in out:
                out.append(n)
        return out

    def _extract_emails_from_footer(self, html_content: str) -> List[str]:
        """Extract emails specifically from footer content"""
        emails = []
        
        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(email_pattern, html_content, re.IGNORECASE)
        emails.extend(matches)
        
        return list(set(emails))

    def _extract_phones_from_text(self, text: str) -> list[str]:
        text = normalize_text(text)
        out = []
        for m in self.VN_PHONE_RX.finditer(text):
            n = clean_phone(m.group(0))
            if n and n not in out:
                out.append(n)
        return out

    def pick_footer_node(self, soup: BeautifulSoup):
        node = soup.select_one("footer, [role=contentinfo], #footer, .footer, .site-footer, .main-footer, .bottom-footer")
        if node:
            return node
        # fallback: phần tử có id/class chứa 'footer'
        for el in soup.find_all(True):
            ident = (el.get("id") or "") + " " + " ".join(el.get("class") or [])
            if "footer" in ident.lower():
                return el
        # fallback cuối: block cuối trang
        blocks = soup.select("footer, section, div")
        return blocks[-1] if blocks else soup

    def _merge_contact_data_with_priority(self, priority_data: Dict, fallback_data: Dict) -> Dict:
        """Merge contact data with priority (footer data takes precedence)"""
        merged = {}
        
        for key in ['emails', 'phones', 'social_links', 'contact_forms']:
            priority_items = priority_data.get(key, [])
            fallback_items = fallback_data.get(key, [])
            
            # Priority data comes first, then fallback (avoid duplicates)
            combined = priority_items + [item for item in fallback_items if item not in priority_items]
            merged[key] = combined
        
        return merged
    
    def _extract_basic_contact_data(self, result: Dict) -> Dict:
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
    
    def _extract_social_media_enhanced(self, result: Dict, base_url: str) -> List[str]:
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
                    social_links.append(f"https://twitter.com/{match}")
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
    
    async def _extract_phone_numbers(self, result: dict) -> list[str]:
        """Extract phone numbers from content with improved patterns"""
        html_content = result.get("html", "") or ""
        soup = BeautifulSoup(html_content, "lxml")
        text = normalize_text(soup.get_text(" ", strip=True))

        # 1) VN ưu tiên
        phones = [m.group(0) for m in self.VN_PHONE_RX.finditer(text)]

        # 2) (tuỳ chọn) các pattern quốc tế khác → nhớ dùng (?: ) và finditer
        # INTERNATIONAL_RX = re.compile(r"...")  # nếu cần
        # phones += [m.group(0) for m in INTERNATIONAL_RX.finditer(text)]

        # 3) Clean & unique
        out: list[str] = []
        for p in phones:
            n = clean_phone(p)
            if n and n not in out:
                out.append(n)

        out.sort(key=len)
        logger.info("📞 Found %d raw matches, cleaned to %d phones", len(phones), len(out))
        return out
    
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