# app/services/cache.py
"""
Caching service for crawl results
"""

import time
import hashlib
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Cache for crawl results
crawl_cache = {}
CACHE_DURATION = 3600  # 1 hour

def get_cached_result(url: str) -> Optional[Dict]:
    """Get cached crawl result if available and not expired"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    if url_hash in crawl_cache:
        cached = crawl_cache[url_hash]
        if time.time() - cached['timestamp'] < CACHE_DURATION:
            logger.info(f"📋 Using cached result for {url}")
            return cached['data']
    return None

def cache_result(url: str, data: Dict):
    """Cache crawl result"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    crawl_cache[url_hash] = {
        'data': data,
        'timestamp': time.time()
    }

def clear_cache():
    """Clear all cached results"""
    global crawl_cache
    cache_size = len(crawl_cache)
    crawl_cache.clear()
    return cache_size

def get_cache_stats():
    """Get cache statistics"""
    return {
        "cache_size": len(crawl_cache),
        "cache_duration": CACHE_DURATION
    } 