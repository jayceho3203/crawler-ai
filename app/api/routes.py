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
    BatchCareerPagesRequest, BatchCareerPagesResponse,
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
async def detect_career_pages_scrapy_main(request: CareerPagesRequest):
    """
    Detect career pages using optimized Scrapy spider + Extract contact info if career pages found
    """
    try:
        logger.info(f"🚀 Scrapy career page detection + contact extraction for: {request.url}")
        
        # Extract Apify data first (phone, title, etc.)
        apify_data = {}
        if hasattr(request, 'Title') and request.Title:
            apify_data['title'] = request.Title
        if hasattr(request, 'Phone') and request.Phone:
            apify_data['phone'] = request.Phone
        if hasattr(request, 'Website') and request.Website:
            apify_data['website'] = request.Website
        if hasattr(request, 'Domain') and request.Domain:
            apify_data['domain'] = request.Domain
            
        logger.info(f"📱 Apify data extracted: {apify_data}")
        
        # Force use Scrapy to detect career pages with optimized settings
        result = await career_pages_service.detect_career_pages(
            url=request.url,
            include_subdomain_search=request.include_subdomain_search,
            max_pages_to_scan=min(request.max_pages_to_scan, 50),  # Reasonable limit to 50 pages max
            strict_filtering=request.strict_filtering,
            include_job_boards=request.include_job_boards,
            use_scrapy=True  # Force Scrapy
        )
        
        # Extract contact info from Scrapy spider result
        contact_info = None
        logger.info(f"🎯 Processing contact info from Scrapy spider")
        
        # Check if Scrapy result contains contact info
        if result and result.get('success') and result.get('contact_info'):
            logger.info(f"✅ Using contact info from Scrapy spider")
            scrapy_contact = result.get('contact_info', {})
            
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
            # Prefer enhanced contact service with deep-crawl over simple main-page parse
            try:
                enhanced = await contact_service.extract_contact_info(
                    url=request.url,
                    include_social=True,
                    include_emails=True,
                    include_phones=True,
                    max_depth=2,
                )
                contact_info = {
                    "emails": enhanced.get("emails", []),
                    "phones": enhanced.get("phones", []),
                    "social_links": enhanced.get("social_links", []),
                    "contact_forms": enhanced.get("contact_forms", []),
                    "website": request.url,
                }
                logger.info(f"✅ Contact info from enhanced fallback: {contact_info}")
            except Exception as contact_error:
                logger.warning(f"⚠️ Contact extraction failed: {contact_error}")
                contact_info = None

                    # Step 2: Only crawl contact info if we found career pages
            if result and result.get('success') and result.get('career_pages') and len(result.get('career_pages', [])) > 0:
                career_pages = result.get('career_pages', [])
                logger.info(f"✅ Found {len(career_pages)} career pages → extracting contact info")
                
                # Extract contact info from homepage + career pages
                unique_targets = [request.url]  # homepage trước
                # cộng thêm tối đa 2 trang career cho chắc
                unique_targets += career_pages[:2]
                seen = set()
                merged = {"emails": [], "phones": [], "social_links": [], "contact_forms": []}

                for u in unique_targets:
                    if u in seen: 
                        continue
                    seen.add(u)
                    try:
                        data = await contact_service.extract_contact_info(
                            url=u, include_social=True, include_emails=True, include_phones=True, max_depth=1
                        )
                        # merge (ưu tiên footer nếu có hàm ưu tiên)
                        merged["emails"].extend(data.get("emails", []))
                        merged["phones"].extend(data.get("phones", []))
                        merged["social_links"].extend(data.get("social_links", []))
                        merged["contact_forms"].extend(data.get("contact_forms", []))
                    except Exception as e:
                        logger.warning(f"⚠️ Contact extraction failed for {u}: {e}")

                # dedupe
                merged["emails"] = list(dict.fromkeys(merged["emails"]))
                merged["phones"] = list(dict.fromkeys(merged["phones"]))
                contact_info = {**merged, "website": request.url}
                logger.info(f"✅ Contact info extracted from {len(unique_targets)} pages: {len(merged['emails'])} emails, {len(merged['phones'])} phones")
            else:
                logger.info(f"⚠️ No career pages found → skip contact extraction")
                contact_info = None
        
        # Add contact info to response
        response_data = result.copy()
        response_data['contact_info'] = contact_info
        response_data['has_contact_info'] = contact_info is not None
        
        # Merge Apify data with crawled contact info
        if contact_info and apify_data:
            # Add Apify phone if not already found
            if apify_data.get('phone') and apify_data['phone'] not in contact_info.get('phones', []):
                if 'phones' not in contact_info:
                    contact_info['phones'] = []
                contact_info['phones'].append(apify_data['phone'])
                logger.info(f"📱 Added Apify phone: {apify_data['phone']}")
            
            # Add Apify title if available
            if apify_data.get('title'):
                response_data['company_title'] = apify_data['title']
                logger.info(f"🏢 Added Apify company title: {apify_data['title']}")
        

        
        # Add missing fields for n8n compatibility
        response_data['fit_markdown'] = None  # Placeholder for future implementation
        response_data['meta_description'] = None  # Placeholder for future implementation
        
        # Add company title from Apify if available (already set above, so skip duplicate)
        # if apify_data.get('title'):
        #     response_data['company_title'] = apify_data['title']
        #     logger.info(f"🏢 Added company title to response: {apify_data['title']}")
        
        return CareerPagesResponse(**response_data)
        
    except Exception as e:
        import traceback
        logger.exception("Error in Scrapy career page detection endpoint")  # tự động in traceback
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

# Contact info extraction is now integrated into detect_career_pages_scrapy endpoint
# No need for separate extract_contact_info endpoint

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@router.post("/debug_html")
async def debug_html(request: JobDetailsRequest):
    """Debug endpoint to check HTML content"""
    try:
        job_url = request.url
        logger.info(f"🔍 Debug HTML for: {job_url}")
        
        # Crawl the URL
        from ..services.crawler import crawl_single_url
        result = await crawl_single_url(job_url)
        
        html_content = result.get('html', '')
        
        return {
            'success': result.get('success', False),
            'url': job_url,
            'html_length': len(html_content),
            'html_preview': html_content[:1000] if html_content else "No HTML content",
            'status_code': result.get('status_code', 0),
            'error': result.get('error_message', None)
        }
        
    except Exception as e:
        logger.error(f"Error in debug HTML endpoint: {e}")
        return {
            'success': False,
            'error_message': str(e)
        }

@router.post("/batch_detect_career_pages")
async def batch_detect_career_pages(request: BatchCareerPagesRequest):
    """Batch detect career pages from multiple URLs"""
    try:
        urls = request.urls
        logger.info(f"🚀 Batch career page detection for {len(urls)} URLs")
        
        results = []
        for url in urls:
            try:
                # Detect career pages for each URL
                result = await career_pages_service.detect_career_pages(
                    url=url,
                    include_subdomain_search=request.include_subdomain_search,
                    max_pages_to_scan=request.max_pages_to_scan,
                    strict_filtering=request.strict_filtering,
                    include_job_boards=request.include_job_boards,
                    use_scrapy=request.use_scrapy
                )
                
                results.append({
                    'url': url,
                    'result': result
                })
                
                logger.info(f"✅ Completed career page detection for: {url}")
                
            except Exception as e:
                logger.error(f"❌ Error detecting career pages for {url}: {e}")
                results.append({
                    'url': url,
                    'result': {
                        'success': False,
                        'error_message': str(e)
                    }
                })
        
        return {
            'success': True,
            'total_urls': len(urls),
            'completed_urls': len([r for r in results if r['result'].get('success', False)]),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in batch career page detection: {e}")
        return {
            'success': False,
            'error_message': str(e)
        }

@router.post("/clear-cache")
async def clear_cache():
    """Clear all cached results"""
    from ..services.cache import clear_cache
    cleared_count = clear_cache()
    return {"success": True, "cleared_items": cleared_count, "message": f"Cleared {cleared_count} cached items"}
