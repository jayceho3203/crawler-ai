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
            max_pages_to_scan=min(request.max_pages_to_scan, 50),  # Increase limit to 50 pages max
            strict_filtering=request.strict_filtering,
            include_job_boards=request.include_job_boards,
            use_scrapy=True  # Force Scrapy
        )
        
        # Extract contact info from Scrapy spider result
        contact_info = None
        logger.info(f"🎯 Processing contact info from Scrapy spider")
        
        # Check if Scrapy result contains contact info
        if result.get('success') and result.get('contact_info'):
            logger.info(f"✅ Using contact info from Scrapy spider")
            scrapy_contact = result['contact_info']
            
            # Convert to format expected by contact extractor
            extracted_data = []
            
            # Add emails from Scrapy (already deduplicated)
            emails = scrapy_contact.get("emails", [])
            logger.info(f"📧 Scrapy found {len(emails)} emails: {emails}")
            for email in emails:
                extracted_data.append({
                    "label": "email",
                    "value": email
                })
            
            # Add phones from Scrapy (already deduplicated)
            phones = scrapy_contact.get("phones", [])
            logger.info(f"📞 Scrapy found {len(phones)} phones: {phones}")
            for phone in phones:
                extracted_data.append({
                    "label": "phone",
                    "value": phone
                })
            
            # Add contact URLs from Scrapy (already deduplicated)
            contact_urls = scrapy_contact.get("contact_urls", [])
            logger.info(f"🔗 Scrapy found {len(contact_urls)} contact URLs")
            for url_item in contact_urls:
                extracted_data.append({
                    "label": "url",
                    "value": url_item
                })
            
            # Process the extracted data
            from ..utils.contact_extractor import process_extracted_crawl_results
            contact_info = process_extracted_crawl_results(extracted_data, request.url)
            logger.info(f"✅ Contact info processed from Scrapy: {contact_info}")
        else:
            logger.info(f"⚠️ No contact info from Scrapy, using fallback")
            # Simple fallback - just crawl main page
            try:
                from ..services.crawler import crawl_single_url
                main_crawl_result = await crawl_single_url(request.url)
                
                if main_crawl_result['success']:
                    extracted_data = []
                    
                    # Add emails
                    emails = main_crawl_result.get("emails", [])
                    logger.info(f"📧 Fallback found {len(emails)} emails: {emails}")
                    for email in emails:
                        extracted_data.append({
                            "label": "email",
                            "value": email
                        })
                    
                    # Add phones
                    phones = main_crawl_result.get("phones", [])
                    logger.info(f"📞 Fallback found {len(phones)} phones: {phones}")
                    for phone in phones:
                        extracted_data.append({
                            "label": "phone",
                            "value": phone
                        })
                    
                    # Add contact URLs
                    urls = main_crawl_result.get("urls", [])
                    contact_urls = []
                    for url_item in urls:
                        url_lower = url_item.lower()
                        contact_keywords = ['contact', 'about', 'team', 'company', 'lien-he', 'gioi-thieu']
                        is_contact_related = any(keyword in url_lower for keyword in contact_keywords)
                        if is_contact_related:
                            contact_urls.append(url_item)
                            extracted_data.append({
                                "label": "url",
                                "value": url_item
                            })
                    
                    logger.info(f"🔗 Fallback found {len(contact_urls)} contact URLs")
                    
                    from ..utils.contact_extractor import process_extracted_crawl_results
                    contact_info = process_extracted_crawl_results(extracted_data, request.url)
                    logger.info(f"✅ Contact info from fallback: {contact_info}")
                else:
                    logger.warning(f"⚠️ Fallback crawl failed: {main_crawl_result.get('error_message', 'Unknown error')}")
                    contact_info = None
                    
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
        
        # Get job details with new field names
        job_details = result.get('job_details', {})
        
        return {
            'success': True,
            'job_url': job_url,
            'job_name': job_details.get('job_name', ''),
            'job_type': job_details.get('job_type', 'Full-time'),
            'job_role': job_details.get('job_role', ''),
            'job_description': job_details.get('job_description', ''),
            'job_link': job_details.get('job_link', job_url),
            'crawl_time': result.get('crawl_time', 0),
            'crawl_method': 'scrapy_optimized'
        }
        
    except Exception as e:
        logger.error(f"Error in job details extraction endpoint: {e}")
        return {
            'success': False,
            'job_url': request.url,
            'error_message': str(e),
            'job_name': '',
            'job_type': 'Full-time',
            'job_role': '',
            'job_description': '',
            'job_link': request.url
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
        from app.services.crawler import crawl_single_url
        from app.utils.contact_extractor import process_extracted_crawl_results
        
        # Crawl the website
        crawl_result = await crawl_single_url(url)
        
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
        
        # Only add contact-related URLs, not all URLs
        urls = crawl_result.get("urls", [])
        for url_item in urls:
            url_lower = url_item.lower()
            # Only include contact-related URLs
            contact_keywords = ['contact', 'about', 'team', 'company', 'lien-he', 'gioi-thieu']
            is_contact_related = any(keyword in url_lower for keyword in contact_keywords)
            
            if is_contact_related:
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
                "website": url
            }
        }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
