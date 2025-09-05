# Scrapy settings for crawler_ai project

BOT_NAME = 'crawler_ai'

SPIDER_MODULES = ['app.services']
NEWSPIDER_MODULE = 'app.services'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 2

# Configure a delay for requests for the same website (default: 0)
DOWNLOAD_DELAY = 1

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 2
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en,vi',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    # 'crawler_ai.middlewares.CrawlerAiSpiderMiddleware': 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    # 'crawler_ai.middlewares.CrawlerAiDownloaderMiddleware': 543,
}

# Enable or disable extensions
EXTENSIONS = {
    # 'scrapy.extensions.telnet.TelnetConsole': None,
}

# Configure item pipelines
ITEM_PIPELINES = {
    # 'crawler_ai.pipelines.CrawlerAiPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'

# Fix HTTPS handler issue - use default handlers
DOWNLOAD_HANDLERS = {
    'http': 'scrapy.core.downloader.handlers.http.HTTPDownloadHandler',
    'https': 'scrapy.core.downloader.handlers.http.HTTPDownloadHandler',
}

# Alternative: disable HTTPS verification
DOWNLOADER_CLIENT_TLS_METHOD = 'TLS'
DOWNLOADER_CLIENT_TLS_VERIFY = False

# Enable redirect following
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 3
