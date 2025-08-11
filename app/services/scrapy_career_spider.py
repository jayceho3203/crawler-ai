# app/services/scrapy_career_spider.py
"""
Optimized Scrapy Spider for career page detection
Memory-optimized for Render free tier
"""

import scrapy
import json
import logging
import time
import os
import tempfile
from datetime import datetime
from typing import Dict, List
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.settings import Settings

logger = logging.getLogger(__name__)

def read_json_with_retry(path: str, tries: int = 20, delay: float = 0.25):
    """Read JSON file with retry to handle file writing race conditions"""
    last_err = None
    for attempt in range(tries):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)  # Read full JSON
        except json.JSONDecodeError as e:
            last_err = e
            logger.warning(f"JSON decode attempt {attempt + 1}/{tries} failed: {e}")
            time.sleep(delay)  # Wait for writer to finish
        except FileNotFoundError as e:
            last_err = e
            logger.warning(f"File not found attempt {attempt + 1}/{tries}: {e}")
            time.sleep(delay)
    raise RuntimeError(f"Cannot read valid JSON at {path} after {tries} attempts: {last_err}")

def atomic_write_json(data, final_path: str):
    """Write JSON file atomically to avoid partial reads"""
    d = os.path.dirname(final_path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_scrapy_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, final_path)  # Atomic operation
    except Exception as e:
        try:
            os.unlink(tmp)
        except:
            pass
        raise e

class OptimizedCareerSpider(scrapy.Spider):
    """
    Optimized Scrapy Spider với keywords tối ưu và memory optimization
    """

    name = 'optimized_career_spider'
    
    # Memory optimization: reduce concurrent requests
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,  # Reduced from default 16
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,  # Only 1 request per domain
        'DOWNLOAD_DELAY': 1,  # 1 second delay between requests
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 3,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'AUTOTHROTTLE_DEBUG': False,
        # Memory optimization
        'DOWNLOAD_TIMEOUT': 30,
        'DOWNLOAD_MAXSIZE': 1024 * 1024,  # 1MB max page size
        'DOWNLOAD_WARNSIZE': 512 * 1024,  # 512KB warning size
        'LOG_LEVEL': 'WARNING',  # Reduce logging overhead
        'COOKIES_ENABLED': False,  # Disable cookies to save memory
        'TELNETCONSOLE_ENABLED': False,
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy.core.downloader.handlers.http.HTTPDownloadHandler',
            'https': 'scrapy.core.downloader.handlers.http.HTTPSDownloadHandler',
        },
        # Disable unnecessary middleware
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
            'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': None,
            'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': None,
        }
    }
    
    def __init__(self, start_url: str = None, max_pages: int = 50, *args, **kwargs):
        super(OptimizedCareerSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else ['https://example.com']
        self.max_pages = max_pages
        self.career_pages = []
        self.crawled_pages = 0
        self.found_career_pages = 0
        self.domain = None
        self.start_time = datetime.now()
        
        # Contact extraction data
        self.all_emails = set()
        self.all_phones = set()
        self.all_contact_urls = set()
    
    def start_requests(self):
        """
        Bắt đầu crawl với priority cao nhất
        """
        for url in self.start_urls:
            self.domain = urlparse(url).netloc
            logger.info(f"🚀 Starting optimized career spider for: {url}")
            
            yield scrapy.Request(
                url=url,
                callback=self.parse_homepage,
                priority=100,  # Priority cao nhất
                meta={'depth': 0, 'is_homepage': True}
            )
    
    def parse_homepage(self, response):
        """
        Parse homepage với focus vào navigation
        """
        logger.info(f"📄 Crawling homepage: {response.url}")
        
        # Tìm tất cả links trên homepage
        all_links = self.extract_all_links(response)
        logger.info(f"🔗 Found {len(all_links)} links on homepage")
        
        # Phân loại và ưu tiên links
        prioritized_links = self.prioritize_links(all_links, response.url)
        logger.info(f"📊 Prioritized links: {len(prioritized_links)} categories")
        
        # Crawl theo priority
        should_break = False
        for priority, links in prioritized_links.items():
            if should_break:
                break
                
            logger.info(f"🎯 Processing priority {priority} with {len(links)} links")
            # Chỉ crawl tối đa 3 links mỗi priority để tăng tốc
            for link in links[:3]:
                if self.crawled_pages >= self.max_pages or self.found_career_pages >= 5:
                    logger.info(f"⏹️ Reached limit: pages={self.crawled_pages}, career_pages={self.found_career_pages}")
                    should_break = True
                    break
                    
                full_url = urljoin(response.url, link)
                logger.info(f"🔗 Processing link: {link} -> {full_url}")
                
                # Chỉ crawl cùng domain
                if urlparse(full_url).netloc == self.domain:
                    logger.info(f"✅ Adding to crawl queue: {full_url}")
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_page,
                        priority=priority,
                        meta={'depth': 1, 'priority': priority}
                    )
                else:
                    logger.info(f"❌ Skipping external link: {full_url}")
        
        # Tăng crawled_pages sau khi đã yield tất cả requests
        self.crawled_pages += 1
        logger.info(f"📊 Homepage processing complete. Crawled pages: {self.crawled_pages}")
    
    def extract_all_links(self, response) -> List[str]:
        """
        Extract tất cả links với focus vào navigation
        """
        links = []
        
        # Ưu tiên navigation links
        nav_selectors = [
            'nav a::attr(href)',
            'header a::attr(href)', 
            '.navbar a::attr(href)',
            '.menu a::attr(href)',
            '.navigation a::attr(href)',
            '.main-menu a::attr(href)',
            '.top-menu a::attr(href)'
        ]
        
        for selector in nav_selectors:
            nav_links = response.css(selector).getall()
            links.extend(nav_links)
        
        # Thêm footer links
        footer_links = response.css('footer a::attr(href)').getall()
        links.extend(footer_links)
        
        # Thêm tất cả links khác
        all_links = response.css('a::attr(href)').getall()
        links.extend(all_links)
        
        logger.info(f"🔍 Raw links found: {len(links)}")
        
        # Remove duplicates và filter
        unique_links = list(set(links))
        logger.info(f"🔍 Unique links: {len(unique_links)}")
        
        filtered_links = [link for link in unique_links if self.is_valid_link(link)]
        logger.info(f"🔍 Valid links: {len(filtered_links)}")
        
        # Log first 10 links for debugging
        if filtered_links:
            logger.info(f"🔍 Sample links: {filtered_links[:10]}")
        
        return filtered_links
    
    def is_valid_link(self, link: str) -> bool:
        """
        Kiểm tra link có hợp lệ không
        """
        if not link or link.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
            return False
        
        # Loại bỏ external links
        if link.startswith('http') and self.domain not in link:
            return False
            
        return True
    
    def prioritize_links(self, links: List[str], base_url: str) -> Dict[int, List[str]]:
        """
        Phân loại links theo priority với keywords tối ưu
        """
        # Keywords tối ưu cho career pages
        career_keywords = [
            # Vietnamese keywords (tối ưu)
            'tuyen-dung', 'tuyển-dụng', 'tuyendung',
            'viec-lam', 'việc-làm', 'vieclam', 
            'co-hoi', 'cơ-hội', 'cohoi',
            'nhan-vien', 'nhân-viên', 'nhanvien',
            'ung-vien', 'ứng-viên', 'ungvien',
            'cong-viec', 'công-việc', 'congviec',
            'lam-viec', 'làm-việc', 'lamviec',
            'thu-viec', 'thử-việc', 'thuviec',
            'chinh-thuc', 'chính-thức', 'chinhthuc',
            'nghe-nghiep', 'nghề-nghiệp', 'nghenghiep',
            'tim-viec', 'tìm-việc', 'timviec',
            'dang-tuyen', 'đang-tuyển', 'dangtuyen',
            
            # English keywords (tối ưu)
            'career', 'careers', 'job', 'jobs',
            'recruitment', 'employment', 'hiring',
            'work', 'position', 'opportunity', 'vacancy',
            'apply', 'application', 'join-us',
            'team', 'talent', 'open-role', 'open-roles',
            'we-are-hiring', 'work-with-us', 'join-our-team',
            'grow-with-us', 'build-with-us', 'create-with-us',
            'full-time', 'part-time', 'remote', 'hybrid',
            'onsite', 'on-site', 'freelance', 'contract',
            'internship', 'intern', 'graduate', 'entry-level',
            'senior', 'junior', 'lead', 'principal'
        ]
        
        # Keywords cho navigation pages
        nav_keywords = [
            'about', 'about-us', 'company', 'team', 'contact',
            'services', 'products', 'solutions', 'portfolio',
            'giới-thiệu', 'công-ty', 'đội-ngũ', 'liên-hệ',
            'dịch-vụ', 'sản-phẩm', 'giải-pháp'
        ]
        
        # Keywords cho content pages
        content_keywords = [
            'news', 'blog', 'article', 'press', 'media',
            'tin-tức', 'bài-viết', 'thông-cáo', 'truyền-thông'
        ]
        
        priority_links = {
            100: [],  # Career pages (cao nhất)
            80: [],   # Navigation pages
            50: [],   # Content pages  
            10: []    # Other pages (thấp nhất)
        }
        
        for link in links:
            link_lower = link.lower()
            
            # Career pages - priority cao nhất
            if any(keyword in link_lower for keyword in career_keywords):
                priority_links[100].append(link)
                logger.info(f"🎯 Career link found: {link}")
            
            # Navigation pages
            elif any(keyword in link_lower for keyword in nav_keywords):
                priority_links[80].append(link)
            
            # Content pages
            elif any(keyword in link_lower for keyword in content_keywords):
                priority_links[50].append(link)
            
            # Other pages
            else:
                priority_links[10].append(link)
        
        return priority_links
    
    def parse_page(self, response):
        """
        Parse từng trang với detection tối ưu và contact extraction
        """
        priority = response.meta.get('priority', 10)
        
        logger.info(f"📄 Crawling page {self.crawled_pages + 1}/{self.max_pages}: {response.url} (priority: {priority})")
        
        # Extract contact info from this page
        contact_info = self.extract_contact_info(response)
        
        # Add to global contact data
        self.all_emails.update(contact_info['emails'])
        self.all_phones.update(contact_info['phones'])
        self.all_contact_urls.update(contact_info['contact_urls'])
        
        logger.info(f"📧 Page {response.url}: Found {len(contact_info['emails'])} emails, {len(contact_info['phones'])} phones")
        
        # Kiểm tra có phải career listing page không
        if self.is_career_listing_page(response):
            career_score = self.calculate_career_score(response)
            
            if career_score >= 0.3:  # Lower threshold to find more career pages
                career_page = {
                    'url': response.url,
                    'title': response.css('title::text').get() or '',
                    'confidence': career_score,
                    'indicators': self.get_career_indicators(response),
                    'priority_found': priority,
                    'contact_info': contact_info  # Include contact info for this career page
                }
                
                self.career_pages.append(career_page)
                self.found_career_pages += 1
                
                logger.info(f"🎯 Career listing page found: {response.url} (score: {career_score:.2f})")
        
        # Tăng crawled_pages sau khi xử lý
        self.crawled_pages += 1
        
        # Dừng sớm nếu đã tìm thấy đủ career pages
        if self.found_career_pages >= 5:  # Increase from 2 to 5
            logger.info(f"⏹️ Stopping crawl: Found enough career pages ({self.found_career_pages})")
            return
        
        # Dừng nếu đã crawl đủ pages
        if self.crawled_pages >= self.max_pages:
            logger.info(f"⏹️ Stopping crawl: Reached max pages limit ({self.max_pages})")
            return
        
        # Tìm thêm links nếu cần
        if self.crawled_pages < self.max_pages:
            links = self.extract_all_links(response)
            prioritized_links = self.prioritize_links(links, response.url)
            
            should_break = False
            for priority, link_list in prioritized_links.items():
                if should_break:
                    break
                    
                for link in link_list[:1]:  # Chỉ crawl 1 link mỗi priority để tăng tốc
                    if self.crawled_pages >= self.max_pages or self.found_career_pages >= 5:
                        should_break = True
                        break
                        
                    full_url = urljoin(response.url, link)
                    if urlparse(full_url).netloc == self.domain:
                        logger.info(f"🔗 Adding to crawl queue: {full_url}")
                        yield scrapy.Request(
                            full_url,
                            callback=self.parse_page,
                            meta={'priority': priority}
                        )
    
    def calculate_career_score(self, response) -> float:
        """
        Tính điểm career page với algorithm tối ưu
        """
        url = response.url.lower()
        content = response.text.lower()
        title = response.css('title::text').get('').lower()
        
        score = 0.0
        
        # URL indicators (weight: 0.4)
        url_indicators = [
            'career', 'careers', 'job', 'jobs', 'recruitment', 'employment',
            'tuyen-dung', 'viec-lam', 'co-hoi', 'nhan-vien', 'ung-vien',
            'cong-viec', 'lam-viec', 'thu-viec', 'chinh-thuc', 'nghe-nghiep'
        ]
        
        for indicator in url_indicators:
            if indicator in url:
                score += 0.4
                break
        
        # Title indicators (weight: 0.3)
        title_indicators = [
            'career', 'job', 'recruitment', 'employment', 'hiring',
            'tuyển dụng', 'việc làm', 'cơ hội', 'nhân viên', 'ứng viên',
            'công việc', 'làm việc', 'thử việc', 'chính thức', 'nghề nghiệp'
        ]
        
        for indicator in title_indicators:
            if indicator in title:
                score += 0.3
                break
        
        # Content indicators (weight: 0.3)
        content_indicators = [
            'apply', 'application', 'submit', 'join', 'work with us',
            'position', 'role', 'opportunity', 'vacancy', 'opening',
            'hiring', 'recruiting', 'employment', 'career opportunity',
            'ứng tuyển', 'nộp đơn', 'tham gia', 'làm việc cùng chúng tôi',
            'vị trí', 'cơ hội', 'tuyển dụng', 'việc làm'
        ]
        
        for indicator in content_indicators:
            if indicator in content:
                score += 0.1
                if score >= 0.6:  # Đủ điểm rồi
                    break
        
        return min(score, 1.0)
    
    def get_career_indicators(self, response) -> List[str]:
        """
        Lấy danh sách indicators tìm thấy
        """
        indicators = []
        url = response.url.lower()
        content = response.text.lower()
        title = response.css('title::text').get('').lower()
        
        # URL indicators
        if 'career' in url:
            indicators.append('URL contains career')
        if 'job' in url:
            indicators.append('URL contains job')
        if 'tuyen-dung' in url:
            indicators.append('URL contains tuyen-dung')
        
        # Title indicators
        if 'career' in title:
            indicators.append('Title contains career')
        if 'job' in title:
            indicators.append('Title contains job')
        
        # Content indicators
        if 'apply' in content:
            indicators.append('Content contains apply')
        if 'position' in content:
            indicators.append('Content contains position')
        if 'hiring' in content:
            indicators.append('Content contains hiring')
        
        return indicators
    
    def is_career_listing_page(self, response) -> bool:
        """
        Phân biệt career listing page vs job detail page
        """
        url = response.url.lower()
        content = response.text.lower()
        title = response.css('title::text').get('').lower()
        
        # Job detail page indicators (loại trừ)
        job_detail_indicators = [
            '/career/', '/job/', '/position/', '/opportunity/',
            '/tuyen-dung/', '/viec-lam/', '/co-hoi/',
            'senior', 'junior', 'developer', 'engineer', 'analyst',
            'manager', 'lead', 'specialist', 'consultant'
        ]
        
        # Nếu URL chứa job detail indicators -> không phải career listing page
        for indicator in job_detail_indicators:
            if indicator in url:
                return False
        
        # Career listing page indicators
        career_listing_indicators = [
            'career.html', 'careers.html', 'job.html', 'jobs.html',
            'tuyen-dung.html', 'viec-lam.html', 'co-hoi.html',
            'recruitment', 'employment', 'hiring', 'join us',
            'work with us', 'open positions', 'current openings'
        ]
        
        # Nếu URL chứa career listing indicators -> là career listing page
        for indicator in career_listing_indicators:
            if indicator in url:
                return True
        
        # Kiểm tra content
        if any(indicator in content for indicator in ['apply now', 'view all jobs', 'browse positions', 'current openings']):
            return True
        
        return False
    
    def closed(self, reason):
        """
        Khi spider kết thúc
        """
        # Giữ nguyên career_pages dict structure
        career_pages_data = []
        for page in self.career_pages:
            if isinstance(page, dict):
                career_pages_data.append(page)
            else:
                # Fallback nếu page là string
                career_pages_data.append({
                    'url': str(page),
                    'title': '',
                    'confidence': 0.0,
                    'indicators': [],
                    'priority_found': 0
                })
        
        # Prepare contact info (already deduplicated by using sets)
        contact_info = {
            'emails': sorted(list(self.all_emails)),  # Convert set to sorted list
            'phones': sorted(list(self.all_phones)),  # Convert set to sorted list
            'contact_urls': sorted(list(self.all_contact_urls))  # Convert set to sorted list
        }
        
        # Tạo result với cả career pages và contact info
        result = {
            'success': True,
            'requested_url': self.start_urls[0] if self.start_urls else '',
            'career_pages': career_pages_data,
            'total_pages_crawled': self.crawled_pages,
            'career_pages_found': len(career_pages_data),
            'crawl_time': datetime.now() - self.start_time,
            'crawl_method': 'scrapy_optimized',
            'contact_info': contact_info  # Include contact info
        }
        
        # Ghi result vào file
        timestamp = int(datetime.now().timestamp())
        result_file = f'scrapy_result_{timestamp}.json'
        
        try:
            atomic_write_json(result, result_file)
            logger.info(f"✅ Result saved atomically to: {result_file}")
            logger.info(f"📊 Contact info: {len(contact_info['emails'])} emails, {len(contact_info['phones'])} phones")
        except Exception as e:
            logger.error(f"❌ Error saving result: {e}")
        
        return result

    def extract_contact_info(self, response) -> Dict:
        """
        Extract contact information from page content
        """
        content = response.text
        url = response.url
        
        # Extract emails using regex
        import re
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        ]
        
        emails = []
        for pattern in email_patterns:
            found_emails = re.findall(pattern, content, re.IGNORECASE)
            emails.extend(found_emails)
        
        # Clean and validate emails
        valid_emails = []
        for email in emails:
            email = email.strip().lower()
            if '@' in email and '.' in email.split('@')[1]:
                # Skip common invalid patterns
                if not any(invalid in email for invalid in [
                    'cropped-favicon', 'favicon', '.png', '.jpg', '.jpeg', '.gif',
                    'data:', 'javascript:', 'mailto:', 'tel:', 'http', 'https'
                ]):
                    valid_emails.append(email)
        
        # Extract phone numbers
        phone_patterns = [
            r'\+84\s?\d{1,2}\s?\d{3}\s?\d{3}\s?\d{3}',
            r'0\d{1,2}\s?\d{3}\s?\d{3}\s?\d{3}',
            r'\d{10,11}',
        ]
        
        phones = []
        for pattern in phone_patterns:
            found_phones = re.findall(pattern, content)
            phones.extend(found_phones)
        
        # Extract contact-related URLs
        contact_urls = []
        for link in response.css('a[href]::attr(href)').getall():
            if link:
                full_url = response.urljoin(link)
                url_lower = full_url.lower()
                contact_keywords = ['contact', 'about', 'team', 'company', 'lien-he', 'gioi-thieu']
                if any(keyword in url_lower for keyword in contact_keywords):
                    contact_urls.append(full_url)
        
        return {
            'emails': valid_emails,
            'phones': phones,
            'contact_urls': contact_urls
        }

# Hàm chạy spider
async def run_optimized_career_spider(url: str, max_pages: int = 150) -> Dict:
    """
    Chạy optimized Scrapy spider bằng subprocess để tránh reactor conflicts
    """
    try:
        import os
        import time
        import subprocess
        import asyncio
        
        # Tạo unique result file
        result_file = f'scrapy_result_{int(time.time())}.json'
        
        # Tạo temporary script để chạy Scrapy với in-memory result
        script_content = f'''
import sys
import os
import json
sys.path.append(os.getcwd())

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from app.services.scrapy_career_spider import OptimizedCareerSpider

# Cấu hình settings - TẮT HOÀN TOÀN FeedExporter
settings = get_project_settings()
settings.update({{
    'LOG_LEVEL': 'INFO',
    'TELNETCONSOLE_ENABLED': False,
    'LOGSTATS_INTERVAL': 60,
    'MEMUSAGE_ENABLED': False,
    # TẮT FEEDS để tránh conflict với manual file writing
    'FEEDS': None,
    'FEED_EXPORT_ENABLED': False,
    'FEED_EXPORT_ENCODING': 'utf-8',
    'FEED_EXPORT_INDENT': 2
}})

# Custom spider runner để capture result
class ResultCaptureSpider(OptimizedCareerSpider):
    def closed(self, reason):
        # Override closed method để capture result
        result = {{
            'success': True,
            'requested_url': '{url}',
            'career_pages': self.career_pages,
            'total_pages_crawled': self.crawled_pages,
            'career_pages_found': self.found_career_pages,
            'crawl_time': 0,
            'crawl_method': 'scrapy_optimized',
            'contact_info': {{
                'emails': list(self.all_emails),
                'phones': list(self.all_phones),
                'contact_urls': list(self.all_contact_urls)
            }}
        }}
        # Print result as JSON to stdout
        print("SPIDER_RESULT_START")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("SPIDER_RESULT_END")
        super().closed(reason)

# Chạy spider với custom class
process = CrawlerProcess(settings)
process.crawl(ResultCaptureSpider, start_url='{url}', max_pages={max_pages})
process.start()

print("Scrapy completed successfully")
'''
        
        # Lưu script tạm
        script_file = f'scrapy_script_{int(time.time())}.py'
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        # Chạy script bằng subprocess
        start_time = time.time()
        
        process = await asyncio.create_subprocess_exec(
            'python', script_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        crawl_time = time.time() - start_time
        
        # Cleanup script
        try:
            os.remove(script_file)
        except:
            pass
        
        # Kiểm tra kết quả
        if process.returncode != 0:
            logger.error(f"Scrapy subprocess failed: {stderr.decode()}")
            return {
                'success': False,
                'error_message': f'Scrapy subprocess failed: {stderr.decode()}',
                'crawl_time': crawl_time,
                'crawl_method': 'scrapy_optimized'
            }
        
        # Parse result từ stdout thay vì file
        try:
            stdout_text = stdout.decode('utf-8', errors='ignore')
            logger.info(f"🔍 Scrapy stdout: {stdout_text[:200]}...")
            
            # Tìm result trong stdout
            if "SPIDER_RESULT_START" in stdout_text and "SPIDER_RESULT_END" in stdout_text:
                start_marker = stdout_text.find("SPIDER_RESULT_START") + len("SPIDER_RESULT_START")
                end_marker = stdout_text.find("SPIDER_RESULT_END")
                json_text = stdout_text[start_marker:end_marker].strip()
                
                result = json.loads(json_text)
                logger.info(f"🔍 Successfully parsed in-memory result type: {type(result)}")
                logger.info(f"🔍 Parsed result keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}")
                return result
            else:
                raise ValueError("No result markers found in stdout")
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing Scrapy result: {e}")
            return {
                'success': False,
                'error_message': f'Error parsing Scrapy result: {str(e)}',
                'crawl_time': crawl_time,
                'crawl_method': 'scrapy_optimized'
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {
                'success': False,
                'error_message': f'Invalid JSON format: {str(e)}',
                'crawl_time': crawl_time,
                'crawl_method': 'scrapy_optimized'
            }
            
    except Exception as e:
        logger.error(f"Error running optimized spider: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {
            'success': False,
            'error_message': str(e)
        } 