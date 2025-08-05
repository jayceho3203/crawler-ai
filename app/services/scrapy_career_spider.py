# app/services/scrapy_career_spider.py
"""
Optimized Scrapy Spider for career page detection
Tối ưu keywords và performance
"""

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from urllib.parse import urljoin, urlparse
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class OptimizedCareerSpider(scrapy.Spider):
    """
    Optimized Scrapy Spider với keywords tối ưu
    """
    name = 'optimized_career_spider'
    
    # Cấu hình tối ưu
    custom_settings = {
        'CONCURRENT_REQUESTS': 8,        # Tăng lên 8 trang cùng lúc
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'DOWNLOAD_DELAY': 0.5,           # Giảm delay xuống 0.5s
        'ROBOTSTXT_OBEY': False,         # Tắt robots.txt để crawl nhanh hơn
        'COOKIES_ENABLED': False,        # Tắt cookies để tăng tốc
        'DOWNLOAD_TIMEOUT': 15,          # Timeout 15s
        'RETRY_TIMES': 2,                # Retry 2 lần
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    def __init__(self, start_url: str = None, max_pages: int = 20, *args, **kwargs):
        super(OptimizedCareerSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else ['https://example.com']
        self.max_pages = max_pages
        self.career_pages = []
        self.crawled_pages = 0
        self.found_career_pages = 0
        self.domain = None
        
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
        self.crawled_pages += 1
        logger.info(f"📄 Crawling homepage: {response.url}")
        
        # Tìm tất cả links trên homepage
        all_links = self.extract_all_links(response)
        
        # Phân loại và ưu tiên links
        prioritized_links = self.prioritize_links(all_links, response.url)
        
        # Crawl theo priority
        for priority, links in prioritized_links.items():
            for link in links:
                if self.crawled_pages >= self.max_pages:
                    break
                    
                full_url = urljoin(response.url, link)
                
                # Chỉ crawl cùng domain
                if urlparse(full_url).netloc == self.domain:
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_page,
                        priority=priority,
                        meta={'depth': 1, 'priority': priority}
                    )
    
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
        
        # Remove duplicates và filter
        unique_links = list(set(links))
        filtered_links = [link for link in unique_links if self.is_valid_link(link)]
        
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
        Parse từng trang với detection tối ưu
        """
        self.crawled_pages += 1
        priority = response.meta.get('priority', 10)
        
        logger.info(f"📄 Crawling page {self.crawled_pages}/{self.max_pages}: {response.url} (priority: {priority})")
        
        # Kiểm tra có phải career page không
        career_score = self.calculate_career_score(response)
        
        if career_score >= 0.6:  # Threshold cao hơn để chính xác
            career_page = {
                'url': response.url,
                'title': response.css('title::text').get() or '',
                'confidence': career_score,
                'indicators': self.get_career_indicators(response),
                'priority_found': priority
            }
            
            self.career_pages.append(career_page)
            self.found_career_pages += 1
            
            logger.info(f"🎯 Career page found: {response.url} (score: {career_score:.2f})")
        
        # Dừng nếu đã crawl đủ pages hoặc tìm thấy đủ career pages
        if self.crawled_pages >= self.max_pages or self.found_career_pages >= 3:
            return
        
        # Tìm thêm links nếu cần
        if self.crawled_pages < self.max_pages:
            links = self.extract_all_links(response)
            prioritized_links = self.prioritize_links(links, response.url)
            
            for priority, link_list in prioritized_links.items():
                for link in link_list[:2]:  # Chỉ crawl 2 links mỗi priority
                    if self.crawled_pages >= self.max_pages:
                        break
                        
                    full_url = urljoin(response.url, link)
                    if urlparse(full_url).netloc == self.domain:
                        yield scrapy.Request(
                            url=full_url,
                            callback=self.parse_page,
                            priority=priority,
                            meta={'depth': response.meta.get('depth', 0) + 1, 'priority': priority}
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
    
    def closed(self, reason):
        """
        Khi spider kết thúc
        """
        # Convert career_pages to list of URLs
        career_page_urls = []
        for page in self.career_pages:
            if isinstance(page, dict):
                career_page_urls.append(page.get('url', ''))
            else:
                career_page_urls.append(str(page))
        
        result = {
            'success': True,
            'requested_url': self.start_urls[0] if self.start_urls else '',
            'career_pages': career_page_urls,
            'total_pages_crawled': self.crawled_pages,
            'career_pages_found': len(self.career_pages),
            'crawl_time': getattr(self, 'crawl_time', 0),
            'crawl_method': 'scrapy_optimized'
        }
        
        logger.info(f"✅ Optimized crawling completed: {self.crawled_pages} pages, {len(self.career_pages)} career pages found")
        
        return result

# Hàm chạy spider
async def run_optimized_career_spider(url: str, max_pages: int = 20) -> Dict:
    """
    Chạy optimized Scrapy spider
    """
    try:
        # Cấu hình settings
        settings = get_project_settings()
        settings.update({
            'LOG_LEVEL': 'INFO',
            'LOG_FORMAT': '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
            'FEEDS': {
                'scrapy_result.json': {
                    'format': 'json',
                    'encoding': 'utf8',
                    'indent': 2,
                }
            }
        })
        
        # Tạo process
        process = CrawlerProcess(settings)
        
        # Chạy spider
        process.crawl(OptimizedCareerSpider, start_url=url, max_pages=max_pages)
        process.start()
        
        # Đọc kết quả
        try:
            with open('scrapy_result.json', 'r') as f:
                result = json.load(f)
            return result
        except FileNotFoundError:
            return {
                'success': False,
                'error_message': 'No result file found'
            }
            
    except Exception as e:
        logger.error(f"Error running optimized spider: {e}")
        return {
            'success': False,
            'error_message': str(e)
        } 