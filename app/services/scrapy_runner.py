# app/services/scrapy_runner.py
"""
Scrapy runner service using blocking subprocess to avoid race conditions
"""

import os
import json
import uuid
import subprocess
import shlex
import functools
import asyncio
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Create data directory for Scrapy results
BASE_DIR = "/opt/render/project/src/.data/scrapy"
os.makedirs(BASE_DIR, exist_ok=True)

def _run_spider_blocking(start_url: str, max_pages: int = 50) -> dict:
    """Run Scrapy spider in blocking mode to avoid race conditions"""
    try:
        # Generate unique output file
        out_path = os.path.join(BASE_DIR, f"scrapy_result_{uuid.uuid4().hex}.json")
        
        # Create temporary script for Scrapy
        script_content = f'''
import sys
import os
sys.path.append(os.getcwd())

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from app.services.scrapy_career_spider import OptimizedCareerSpider

# Configure settings
settings = get_project_settings()
settings.update({{
    'LOG_LEVEL': 'ERROR',
    'TELNETCONSOLE_ENABLED': False,
    'LOGSTATS_INTERVAL': 60,
    'MEMUSAGE_ENABLED': False,
    'FEEDS': None,
    'FEED_EXPORT_ENABLED': False,
    'DOWNLOAD_TIMEOUT': 30,
    'DOWNLOAD_MAXSIZE': 1024 * 1024,
    'DOWNLOAD_WARNSIZE': 512 * 1024,
    'CONCURRENT_REQUESTS': 2,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
    'DOWNLOAD_DELAY': 1,
    'AUTOTHROTTLE_ENABLED': True,
    'AUTOTHROTTLE_START_DELAY': 1,
    'AUTOTHROTTLE_MAX_DELAY': 3,
    'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
    'COOKIES_ENABLED': False,
    'DOWNLOADER_MIDDLEWARES': {{
        'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
        'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
        'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
    }},
    'SPIDER_MIDDLEWARES': {{
        'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': None,
        'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': None,
    }}
}})

# Custom spider to capture results
class ResultCaptureSpider(OptimizedCareerSpider):
    def closed(self, reason):
        # Capture results when spider finishes
        result = {{
            'success': True,
            'requested_url': '{start_url}',
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
        
        # Write result to file
        with open('{out_path}', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"Result saved to: {{out_path}}")
        super().closed(reason)

# Run spider
process = CrawlerProcess(settings)
process.crawl(ResultCaptureSpider, start_url='{start_url}', max_pages={max_pages})
process.start()
print("Scrapy completed successfully")
'''
        
        # Save temporary script
        script_file = f'scrapy_script_{uuid.uuid4().hex}.py'
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        try:
            # Run script with timeout
            result = subprocess.run(
                ['python', script_file],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutes timeout
                cwd=os.getcwd()
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Scrapy failed: {result.stderr}")
            
            # Wait a bit for file to be written
            import time
            time.sleep(1)
            
            # Read result file
            if os.path.exists(out_path):
                with open(out_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Cleanup
                try:
                    os.remove(out_path)
                except:
                    pass
                
                return data
            else:
                raise FileNotFoundError(f"Result file not found: {out_path}")
                
        finally:
            # Cleanup script
            try:
                os.remove(script_file)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error in blocking Scrapy runner: {e}")
        raise

async def run_spider(start_url: str, max_pages: int = 50) -> dict:
    """Run Scrapy spider asynchronously using executor"""
    try:
        loop = asyncio.get_running_loop()
        fn = functools.partial(_run_spider_blocking, start_url=start_url, max_pages=max_pages)
        result = await loop.run_in_executor(None, fn)
        
        logger.info(f"✅ Scrapy spider completed successfully for {start_url}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Scrapy spider failed for {start_url}: {e}")
        return {
            'success': False,
            'error_message': str(e),
            'requested_url': start_url,
            'career_pages': [],
            'total_pages_crawled': 0,
            'career_pages_found': 0,
            'crawl_time': 0,
            'crawl_method': 'scrapy_optimized',
            'contact_info': {
                'emails': [],
                'phones': [],
                'contact_urls': []
            }
        }
