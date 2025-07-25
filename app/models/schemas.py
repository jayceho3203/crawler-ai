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