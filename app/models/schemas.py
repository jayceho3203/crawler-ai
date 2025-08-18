# app/models/schemas.py
"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel
from typing import Optional, List, Dict

class CrawlRequest(BaseModel):
    """Request model for single URL crawling"""
    url: str

class BatchCrawlRequest(BaseModel):
    """Request model for batch crawling"""
    name: Optional[str] = None
    domain: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    data_raw: Optional[str] = None
    social: Optional[List[str]] = []
    career_page: Optional[List[str]] = []
    crawl_data: Optional[str] = None
    url: Optional[str] = None

class CrawlResponse(BaseModel):
    """Response model for crawling results"""
    requested_url: str
    final_url: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    emails: List[str] = []
    social_links: List[str] = []
    career_pages: List[str] = []
    raw_extracted_data: Optional[Dict] = None
    fit_markdown: Optional[str] = None
    crawl_method: Optional[str] = None
    crawl_time: Optional[float] = None
    # Job extraction fields
    total_jobs_found: Optional[int] = None
    jobs: Optional[List[Dict]] = None
    # Simple job formatting fields
    formatted_jobs: Optional[Dict] = None
    job_summary: Optional[Dict] = None

# New schemas for separated endpoints
class ContactInfoRequest(BaseModel):
    """Request model for contact info extraction"""
    url: str
    include_social: bool = True
    include_emails: bool = True
    include_phones: bool = True
    max_depth: int = 2
    timeout: int = 30

class ContactInfoResponse(BaseModel):
    """Response model for contact info extraction"""
    requested_url: str
    success: bool
    error_message: Optional[str] = None
    crawl_time: Optional[float] = None
    crawl_method: Optional[str] = None
    # Contact data
    emails: List[str] = []
    phones: List[str] = []
    social_links: List[str] = []
    contact_forms: List[str] = []
    # Raw data for debugging
    raw_extracted_data: Optional[Dict] = None
    # Statistics
    total_pages_crawled: int = 0
    total_links_found: int = 0

class CareerPagesRequest(BaseModel):
    """Request model for career page detection"""
    url: str
    include_subdomain_search: bool = False
    max_pages_to_scan: int = 30
    strict_filtering: bool = True
    include_job_boards: bool = False
    use_scrapy: bool = True
    # Apify data fields (optional)
    Title: Optional[str] = None
    Phone: Optional[str] = None
    Website: Optional[str] = None
    Domain: Optional[str] = None
    Street: Optional[str] = None
    location_query_id: Optional[str] = None

class CareerPagesResponse(BaseModel):
    """Response model for career page detection"""
    requested_url: str
    success: bool
    error_message: Optional[str] = None
    crawl_time: Optional[float] = None
    # Career pages found
    career_pages: List[str] = []
    potential_career_pages: List[str] = []
    rejected_urls: List[Dict] = []  # URLs that were rejected with reasons
    # Analysis results
    career_page_analysis: List[Dict] = []  # Detailed analysis of each career page
    # Statistics
    total_urls_scanned: int = 0
    valid_career_pages: int = 0
    confidence_score: float = 0.0
    # Contact info (if career pages found)
    contact_info: Optional[Dict] = None
    has_contact_info: bool = False
    # Additional company info from Apify
    company_title: Optional[str] = None

class BatchCareerPagesRequest(BaseModel):
    """Request model for batch career page detection"""
    urls: List[str]
    include_subdomain_search: bool = False
    max_pages_to_scan: int = 30
    strict_filtering: bool = False
    include_job_boards: bool = False
    use_scrapy: bool = True

class BatchCareerPagesResponse(BaseModel):
    """Response model for batch career page detection"""
    success: bool
    error_message: Optional[str] = None
    total_urls: int = 0
    completed_urls: int = 0
    results: List[Dict] = []

class JobExtractionRequest(BaseModel):
    """Request model for job extraction"""
    career_page_urls: List[str]
    max_jobs_per_page: int = 50
    include_hidden_jobs: bool = True
    include_job_details: bool = True
    job_types_filter: Optional[List[str]] = None  # Filter by job types
    location_filter: Optional[List[str]] = None   # Filter by locations
    salary_range: Optional[Dict] = None  # min/max salary
    posted_date_filter: Optional[str] = None  # "last_week", "last_month", etc.

class JobExtractionResponse(BaseModel):
    """Response model for job extraction"""
    requested_urls: List[str]
    success: bool
    error_message: Optional[str] = None
    crawl_time: Optional[float] = None
    # Job data
    total_jobs_found: int = 0
    jobs: List[Dict] = []
    formatted_jobs: Dict = {}  # Simple format for n8n
    job_summary: Dict = {}     # Statistics
    # Detailed analysis
    job_analysis: List[Dict] = []  # Detailed analysis of each job
    # Per-page results
    page_results: List[Dict] = []  # Results for each career page
    # Hidden jobs found
    hidden_jobs_count: int = 0
    visible_jobs_count: int = 0

# New schema for advanced job finding
class AdvancedJobFindingRequest(BaseModel):
    """Request model for advanced job finding"""
    career_url: str
    max_jobs: int = 100
    search_strategy: str = "comprehensive"  # "comprehensive", "deep_crawl", "pattern_based"
    include_detailed_analysis: bool = True
    quality_threshold: float = 0.5  # Minimum quality score to include

class AdvancedJobFindingResponse(BaseModel):
    """Response model for advanced job finding"""
    career_url: str
    success: bool
    error_message: Optional[str] = None
    crawl_time: Optional[float] = None
    # Job data
    total_jobs_found: int = 0
    high_quality_jobs: int = 0
    average_quality_score: float = 0.0
    jobs: List[Dict] = []
    # Statistics
    statistics: Dict = {}
    # Search methods used
    search_methods_used: List[str] = []

class BatchCrawlResponse(BaseModel):
    """Response model for batch crawling results"""
    company_name: Optional[str] = None
    domain: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    social_links: List[str] = []
    career_pages: List[str] = []
    emails: List[str] = []
    crawl_results: List[Dict] = []
    total_urls_processed: int = 0
    successful_crawls: int = 0
    total_crawl_time: Optional[float] = None

class JobDetailRequest(BaseModel):
    """Request model for job detail crawling"""
    job_urls: List[str]
    max_jobs: Optional[int] = 50

class ChildLinksRequest(BaseModel):
    """Request model for crawling child links"""
    career_page_url: str
    max_links: Optional[int] = 20

class AIExtractionRequest(BaseModel):
    """Request model for AI extraction checking"""
    page_content: str
    ai_response: str 