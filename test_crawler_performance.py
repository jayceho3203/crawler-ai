#!/usr/bin/env python3
"""
Test script để kiểm tra performance của crawler đã được tối ưu
"""

import asyncio
import time
import logging
from app.services.crawler import extract_with_playwright

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_crawler_performance():
    """Test performance của crawler"""
    
    # Test URLs
    test_urls = [
        "https://www.ics-p.vn/vi",
        "https://fpt.com.vn",
        "https://vng.com.vn"
    ]
    
    for url in test_urls:
        logger.info(f"🚀 Testing crawler performance for: {url}")
        start_time = time.time()
        
        try:
            result = await extract_with_playwright(url)
            end_time = time.time()
            crawl_time = end_time - start_time
            
            logger.info(f"✅ Crawl completed: {url}")
            logger.info(f"⏱️  Total time: {crawl_time:.2f}s")
            logger.info(f"📊 Success: {result.get('success', False)}")
            logger.info(f"📧 Emails found: {len(result.get('emails', []))}")
            logger.info(f"📞 Phones found: {len(result.get('phones', []))}")
            logger.info(f"🔗 Career URLs: {len(result.get('career_urls', []))}")
            logger.info(f"💼 Jobs found: {len(result.get('total_jobs', []))}")
            logger.info("-" * 50)
            
        except Exception as e:
            end_time = time.time()
            crawl_time = end_time - start_time
            logger.error(f"❌ Crawl failed for {url}: {str(e)}")
            logger.error(f"⏱️  Time before failure: {crawl_time:.2f}s")
            logger.info("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_crawler_performance())
