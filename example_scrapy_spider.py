# example_scrapy_spider.py
"""
Ví dụ Scrapy Spider để crawl career pages
Đây là cách Scrapy hoạt động so với code hiện tại
"""

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from urllib.parse import urljoin
import json

class CareerPageSpider(scrapy.Spider):
    """
    Scrapy Spider để tìm career pages
    """
    name = 'career_spider'
    
    # Cấu hình spider
    custom_settings = {
        'CONCURRENT_REQUESTS': 5,  # Crawl 5 trang cùng lúc
        'DOWNLOAD_DELAY': 1,       # Delay 1 giây giữa các request
        'ROBOTSTXT_OBEY': True,    # Tuân thủ robots.txt
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def __init__(self, start_url=None, *args, **kwargs):
        super(CareerPageSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else ['https://example.com']
        self.career_pages = []
        self.crawled_pages = 0
        self.max_pages = 20
        
    def start_requests(self):
        """
        Bắt đầu crawl từ URL gốc
        """
        for url in self.start_urls:
            # Ưu tiên cao nhất cho trang gốc
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                priority=10,  # Priority cao nhất
                meta={'depth': 0}
            )
    
    def parse(self, response):
        """
        Parse trang gốc và tìm career pages
        """
        self.crawled_pages += 1
        
        # Dừng nếu đã crawl đủ pages
        if self.crawled_pages >= self.max_pages:
            return
        
        # Tìm tất cả links trên trang
        all_links = response.css('a::attr(href)').getall()
        
        # Phân loại links theo priority
        priority_links = self.categorize_links(all_links, response.url)
        
        # Crawl theo priority
        for priority, links in priority_links.items():
            for link in links[:5]:  # Chỉ crawl 5 links mỗi priority
                full_url = urljoin(response.url, link)
                
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_page,
                    priority=priority,
                    meta={'depth': response.meta.get('depth', 0) + 1}
                )
    
    def categorize_links(self, links, base_url):
        """
        Phân loại links theo priority
        """
        career_keywords = [
            'career', 'careers', 'job', 'jobs', 'recruitment', 'employment',
            'tuyen-dung', 'viec-lam', 'co-hoi', 'nhan-vien'
        ]
        
        navigation_keywords = [
            'about', 'contact', 'company', 'team', 'services', 'products'
        ]
        
        priority_links = {
            10: [],  # Career pages (cao nhất)
            8: [],   # Navigation pages
            5: [],   # Content pages
            1: []    # Other pages (thấp nhất)
        }
        
        for link in links:
            link_lower = link.lower()
            
            # Career pages - priority cao nhất
            if any(keyword in link_lower for keyword in career_keywords):
                priority_links[10].append(link)
            
            # Navigation pages
            elif any(keyword in link_lower for keyword in navigation_keywords):
                priority_links[8].append(link)
            
            # Content pages (news, blog, etc.)
            elif any(keyword in link_lower for keyword in ['news', 'blog', 'article']):
                priority_links[5].append(link)
            
            # Other pages
            else:
                priority_links[1].append(link)
        
        return priority_links
    
    def parse_page(self, response):
        """
        Parse từng trang và kiểm tra có phải career page không
        """
        self.crawled_pages += 1
        
        # Dừng nếu đã crawl đủ pages
        if self.crawled_pages >= self.max_pages:
            return
        
        # Kiểm tra có phải career page không
        if self.is_career_page(response):
            self.career_pages.append({
                'url': response.url,
                'title': response.css('title::text').get(),
                'confidence': self.calculate_confidence(response)
            })
            
            # Log kết quả
            self.logger.info(f"🎯 Career page found: {response.url}")
        
        # Tìm thêm links nếu chưa đủ pages
        if self.crawled_pages < self.max_pages:
            links = response.css('a::attr(href)').getall()
            for link in links[:3]:  # Chỉ crawl 3 links mỗi trang
                full_url = urljoin(response.url, link)
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_page,
                    priority=5,
                    meta={'depth': response.meta.get('depth', 0) + 1}
                )
    
    def is_career_page(self, response):
        """
        Kiểm tra có phải career page không
        """
        url = response.url.lower()
        content = response.text.lower()
        
        career_indicators = [
            'career', 'job', 'recruitment', 'employment',
            'tuyen-dung', 'viec-lam', 'co-hoi', 'nhan-vien',
            'apply', 'application', 'hiring', 'join-us'
        ]
        
        # Kiểm tra URL
        if any(indicator in url for indicator in career_indicators):
            return True
        
        # Kiểm tra content
        if any(indicator in content for indicator in career_indicators):
            return True
        
        return False
    
    def calculate_confidence(self, response):
        """
        Tính độ tin cậy của career page
        """
        confidence = 0.0
        url = response.url.lower()
        content = response.text.lower()
        
        # URL indicators
        if 'career' in url:
            confidence += 0.4
        if 'job' in url:
            confidence += 0.3
        if 'tuyen-dung' in url:
            confidence += 0.4
        
        # Content indicators
        if 'apply' in content:
            confidence += 0.2
        if 'position' in content:
            confidence += 0.2
        if 'hiring' in content:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def closed(self, reason):
        """
        Khi spider kết thúc
        """
        result = {
            'success': True,
            'career_pages': self.career_pages,
            'total_pages_crawled': self.crawled_pages,
            'career_pages_found': len(self.career_pages)
        }
        
        # Lưu kết quả
        with open('scrapy_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        self.logger.info(f"✅ Crawling completed: {self.crawled_pages} pages, {len(self.career_pages)} career pages found")

# Hàm chạy spider
def run_scrapy_spider(url):
    """
    Chạy Scrapy spider
    """
    # Cấu hình settings
    settings = get_project_settings()
    settings.update({
        'LOG_LEVEL': 'INFO',
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
    process.crawl(CareerPageSpider, start_url=url)
    process.start()

# Ví dụ sử dụng
if __name__ == "__main__":
    # Chạy spider với URL
    run_scrapy_spider("https://www.ics-p.vn/vi") 