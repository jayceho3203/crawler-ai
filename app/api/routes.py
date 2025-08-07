# app/api/routes.py
"""
API routes for the crawler application
"""

import json
import logging
from datetime import datetime
from typing import List, Dict
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..models.schemas import (
    CrawlRequest, CrawlResponse, BatchCrawlRequest, BatchCrawlResponse,
    JobDetailRequest, ChildLinksRequest, AIExtractionRequest,
    ContactInfoRequest, ContactInfoResponse, CareerPagesRequest, CareerPagesResponse,
    JobExtractionRequest, JobExtractionResponse, AdvancedJobFindingRequest, AdvancedJobFindingResponse
)
from ..services.crawler import crawl_single_url
from ..services.cache import clear_cache, get_cache_stats
from ..utils.constants import CAREER_KEYWORDS_VI, CAREER_SELECTORS, JOB_BOARD_DOMAINS
from ..utils.contact_extractor import process_extracted_crawl_results
from ..services.job_extractor import extract_jobs_from_page
from ..services.contact_extractor_service import ContactExtractorService
from ..services.career_pages_service import CareerPagesService
from ..services.job_extraction_service import JobExtractionService
from ..services.advanced_job_finder import AdvancedJobFinder

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
contact_service = ContactExtractorService()
career_pages_service = CareerPagesService()
job_extraction_service = JobExtractionService()
advanced_job_finder = AdvancedJobFinder()

# Essential endpoints for N8N workflow

@router.post("/detect_career_pages_scrapy", response_model=CareerPagesResponse)
async def detect_career_pages_scrapy(request: CareerPagesRequest):
    """
    Detect career pages using optimized Scrapy spider + Extract contact info if career pages found
    """
    try:
        logger.info(f"🚀 Scrapy career page detection + contact extraction for: {request.url}")
        
        # Force use Scrapy to detect career pages with optimized settings
        result = await career_pages_service.detect_career_pages(
            url=request.url,
            include_subdomain_search=request.include_subdomain_search,
            max_pages_to_scan=min(request.max_pages_to_scan, 0),  # Limit to 20 pages max
            strict_filtering=request.strict_filtering,
            include_job_boards=request.include_job_boards,
            use_scrapy=True  # Force Scrapy
        )
        
        # If career pages found, extract contact info from the same crawl data
        contact_info = None
        if result.get('success') and result.get('career_pages'):
            logger.info(f"🎯 Career pages found! Extracting contact info from existing data for: {request.url}")
            try:
                # Use the same crawl data instead of crawling again
                from ..utils.contact_extractor import process_extracted_crawl_results
                
                # Extract contact info from the same HTML content that Scrapy already crawled
                if hasattr(result, 'raw_html') and result.get('raw_html'):
                    # Process the same HTML content
                    from ..services.crawler import extract_with_playwright
                    crawl_result = await extract_with_playwright(request.url)
                    
                    # Convert to format expected by contact extractor
                    extracted_data = []
                    
                    # Add emails
                    emails = crawl_result.get("emails", [])
                    for email in emails:
                        extracted_data.append({
                            "label": "email",
                            "value": email
                        })
                    
                    # Add phones
                    phones = crawl_result.get("phones", [])
                    for phone in phones:
                        extracted_data.append({
                            "label": "phone",
                            "value": phone
                        })
                    
                    # Add URLs
                    urls = crawl_result.get("urls", [])
                    for url_item in urls:
                        extracted_data.append({
                            "label": "url",
                            "value": url_item
                        })
                    
                    # Process the extracted data
                    contact_info = process_extracted_crawl_results(extracted_data, request.url)
                    logger.info(f"✅ Contact info extracted from existing crawl data")
                else:
                    # Fallback to separate crawl if no raw HTML
                    from ..utils.contact_extractor import extract_contact_info_from_url
                    contact_info = await extract_contact_info_from_url(request.url)
                    logger.info(f"✅ Contact info extracted with fallback method")
            except Exception as contact_error:
                logger.warning(f"⚠️ Contact extraction failed: {contact_error}")
                contact_info = None
        
        # Add contact info to response
        response_data = result.copy()
        response_data['contact_info'] = contact_info
        response_data['has_contact_info'] = contact_info is not None
        
        return CareerPagesResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error in Scrapy career page detection endpoint: {e}")
        return CareerPagesResponse(
            requested_url=request.url,
            success=False,
            error_message=str(e),
            contact_info=None,
            has_contact_info=False
        )

class JobUrlsRequest(BaseModel):
    url: str
    max_jobs: int = 50

@router.post("/extract_job_urls", response_model=dict)
async def extract_job_urls(request: JobUrlsRequest):
    """
    Extract job URLs from career pages (for n8n workflow)
    """
    try:
        career_page_url = request.url
        max_jobs = request.max_jobs
        
        logger.info(f"🔗 Extracting job URLs from: {career_page_url}")
        
        # Extract job URLs
        result = await job_extraction_service.extract_job_urls_only(
            career_page_url=career_page_url,
            max_jobs=max_jobs,
            include_job_data=False
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in job URLs extraction endpoint: {e}")
        return {
            'success': False,
            'career_page_url': request.url,
            'error_message': str(e),
            'total_jobs_found': 0,
            'has_individual_urls': False,
            'crawl_method': 'scrapy_optimized'
        }

class JobDetailsRequest(BaseModel):
    url: str

@router.post("/extract_job_details", response_model=dict)
async def extract_job_details(request: JobDetailsRequest):
    """
    Extract detailed job information from a single job URL
    """
    try:
        job_url = request.url
        
        logger.info(f"📄 Extracting job details from: {job_url}")
        
        # Extract job details
        result = await job_extraction_service.extract_job_details_only(
            job_url=job_url
        )
        
        return {
            'success': True,
            'job_url': job_url,
            'job_details': result.get('job_details', {}),
            'crawl_time': result.get('crawl_time', 0),
            'crawl_method': 'scrapy_optimized'
        }
        
    except Exception as e:
        logger.error(f"Error in job details extraction endpoint: {e}")
        return {
            'success': False,
            'job_url': request.url,
            'error_message': str(e),
            'job_details': {}
        }

class AIAgentRequest(BaseModel):
    job_data: list = []
    analysis_type: str = "summary"
    ai_model: str = "gemini"

@router.post("/ai_agent_analysis", response_model=dict)
async def ai_agent_analysis(request: AIAgentRequest):
    """
    AI Agent analysis for job data processing
    """
    try:
        logger.info(f"🤖 AI Agent analysis request")
        
        # Extract data from request
        job_data = request.job_data
        analysis_type = request.analysis_type
        ai_model = request.ai_model
        
        result = await advanced_job_finder.ai_agent_analysis(
            job_data=job_data,
            analysis_type=analysis_type,
            ai_model=ai_model
        )
        
        return {
            'success': True,
            'analysis_type': analysis_type,
            'ai_model': ai_model,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in AI Agent analysis endpoint: {e}")
        return {
            'success': False,
            'error_message': str(e),
            'timestamp': datetime.now().isoformat()
        }

@router.post("/api/v1/extract_contact_info")
async def extract_contact_info(request: dict):
    """
    Extract contact information from company website
    """
    try:
        url = request.get("url")
        if not url:
            return {"error": "URL is required"}
        
        # Use existing crawler service to extract contact info
        from app.services.crawler import extract_with_playwright
        from app.utils.contact_extractor import process_extracted_crawl_results
        
        # Crawl the website
        crawl_result = await extract_with_playwright(url)
        
        # Convert to format expected by contact extractor
        extracted_data = []
        
        # Add emails
        emails = crawl_result.get("emails", [])
        for email in emails:
            extracted_data.append({
                "label": "email",
                "value": email
            })
        
        # Add phones
        phones = crawl_result.get("phones", [])
        for phone in phones:
            extracted_data.append({
                "label": "phone",
                "value": phone
            })
        
        # Add URLs
        urls = crawl_result.get("urls", [])
        for url_item in urls:
            extracted_data.append({
                "label": "url",
                "value": url_item
            })
        
        # Process the extracted data
        contact_info = process_extracted_crawl_results(extracted_data, url)
        
        return {
            "success": True,
            "data": contact_info
        }
        
    except Exception as e:
        logger.error(f"Error extracting contact info from {url}: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "emails": [],
                "phones": [],
                "social_links": [],
                "career_pages": [],
                "website": url
            }
        }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
