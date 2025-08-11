# app/services/scrapy_runner.py
"""
Scrapy runner service using blocking subprocess to avoid race conditions
"""

import json
import subprocess
import functools
import asyncio
import logging
from typing import Dict

logger = logging.getLogger(__name__)

def _run_spider_blocking(start_url: str, max_pages: int = 50) -> dict:
    """Run Scrapy spider in blocking mode to avoid race conditions"""
    try:
        # Use direct Scrapy command with JSON output to stdout
        cmd = [
            "python", "-m", "scrapy", "crawl", "career_spider",
            "-a", f"start_url={start_url}",
            "-a", f"max_pages={max_pages}",
            "-o", "-", "-t", "json",                 # ✅ Xuất JSON ra stdout
            "-s", "LOG_LEVEL=ERROR",                 # log đi stderr
            "-s", "FEED_EXPORT_ENCODING=utf-8",
            "-s", "TELNETCONSOLE_ENABLED=False",
            "-s", "MEMUSAGE_ENABLED=False",
            "-s", "DOWNLOAD_TIMEOUT=30",
            "-s", "CONCURRENT_REQUESTS=2",
            "-s", "DOWNLOAD_DELAY=1",
        ]
        
        logger.info(f"🚀 Running Scrapy command: {' '.join(cmd)}")
        
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        
        if res.returncode != 0:
            error_msg = res.stderr.strip() or res.stdout[:400] or "Unknown Scrapy error"
            logger.error(f"❌ Scrapy failed with return code {res.returncode}: {error_msg}")
            raise RuntimeError(f"Scrapy failed: {error_msg}")
        
        raw = res.stdout.strip()
        logger.info(f"📊 Scrapy raw output length: {len(raw)}")
        
        # Nếu spider không yield item nào, Scrapy vẫn in "[]"
        if not raw:
            raw = "[]"
            logger.warning("⚠️ Scrapy output empty, using empty array")
        
        try:
            items = json.loads(raw)
            logger.info(f"✅ Successfully parsed Scrapy JSON output: {len(items) if isinstance(items, list) else 'dict'}")
            
            # Convert items to expected format
            if isinstance(items, list):
                # Items from spider
                return {
                    "success": True,
                    "requested_url": start_url,
                    "career_pages": items,
                    "total_pages_crawled": len(items),
                    "career_pages_found": len(items),
                    "crawl_time": 0,
                    "crawl_method": "scrapy_optimized",
                    "contact_info": {
                        "emails": [],  # Will be extracted from items
                        "phones": [],
                        "contact_urls": []
                    }
                }
            else:
                # Direct result dict
                return items
                
        except json.JSONDecodeError as e:
            # Log 200 ký tự đầu để debug nếu JSON hỏng
            snippet = raw[:200].replace("\n", "\\n")
            error_msg = f"Invalid JSON from spider: {e}. Snippet: {snippet}"
            logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "Scrapy command timed out after 150 seconds"
        logger.error(f"❌ {error_msg}")
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error in Scrapy runner: {e}"
        logger.error(f"❌ {error_msg}")
        raise RuntimeError(error_msg)

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
