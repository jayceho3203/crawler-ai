# app/api/routes.py
"""
API routes for the crawler application
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..models.schemas import (
    JobDetailValidationRequest, CareerPagesRequest, CareerPagesResponse,
    BatchCareerPagesRequest, BatchCareerPagesResponse
)
from ..services.cache import clear_cache
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
                merged["social_links"] = list(dict.fromkeys(merged["social_links"]))
                merged["contact_forms"] = list(dict.fromkeys(merged["contact_forms"]))
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
    job_index: int = None  # Optional job index for career pages

@router.post("/extract_job_details", response_model=dict)
async def extract_job_details(request: JobDetailsRequest):
    """
    Extract detailed job information from a single job URL
    For career pages, job_index specifies which job to extract (1-based)
    """
    try:
        job_url = request.url
        job_index = request.job_index
        
        logger.info(f"📄 Extracting job details from: {job_url}")
        if job_index:
            logger.info(f"   🎯 Job index: {job_index}")
        
        # Extract job details
        result = await job_extraction_service.extract_job_details_only(
            job_url=job_url,
            job_index=job_index
        )
        
        # Get job details with new field names
        job_details = result.get('job_details', {})
        
        return {
            'success': True,
            'job_url': job_url,
            'job_index': job_index,
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
            'job_index': request.job_index,
            'error_message': str(e),
            'job_name': '',
            'job_type': 'Full-time',
            'job_role': '',
            'job_description': '',
            'job_link': request.url
        }

@router.post("/validate_job_details")
async def validate_job_details(request: JobDetailValidationRequest):
    """
    Validate job details before processing (n8n integration)
    """
    try:
        logger.info(f"🔍 Validating job details for: {request.job_name}")
        
        # Validation is handled by Pydantic model
        # If we reach here, validation passed
        
        return {
            "success": True,
            "validated_data": {
                "job_name": request.job_name,
                "job_type": request.job_type,
                "job_role": request.job_role,
                "job_description": request.job_description,
                "job_link": request.job_link,
                "crawl_company_id": request.crawl_company_id
            },
            "message": "Job details validated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error validating job details: {e}")
        return {
            "success": False,
            "error_message": str(e),
            "validation_errors": [
                {"field": "job_link", "message": "Job link must be a valid URL"} if "job_link" in str(e) else
                {"field": "job_description", "message": "Job description must be at least 10 characters"} if "job_description" in str(e) else
                {"field": "unknown", "message": str(e)}
            ]
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

@router.post("/debug_job_extraction")
async def debug_job_extraction(request: JobDetailsRequest):
    """Debug endpoint to test job extraction logic"""
    try:
        from ..services.crawler import crawl_single_url
        from bs4 import BeautifulSoup
        import re
        
        result = await crawl_single_url(request.url)
        
        if not result['success']:
            return {
                'success': False,
                'error': 'Failed to crawl page'
            }
        
        html_content = result.get('html', '')
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Test title extraction
        title_selectors = [
            'h1', 'h2', 'h3', '.job-title', '.position-title', '.title',
            '.career-title', '.vacancy-title', '.opening-title'
        ]
        
        found_titles = []
        for selector in title_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) > 3:
                    found_titles.append({
                        'selector': selector,
                        'text': text,
                        'length': len(text)
                    })
        
        # Test description extraction
        desc_selectors = [
            '.job-description', '.description', '.content', '.job-content',
            'article', '.main-content', '.job-details'
        ]
        
        found_descriptions = []
        for selector in desc_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) > 50:
                    found_descriptions.append({
                        'selector': selector,
                        'text': text[:200] + '...' if len(text) > 200 else text,
                        'length': len(text)
                    })
        
        # Test fallback extraction
        fallback_text = ''
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if main_content:
            fallback_text = main_content.get_text().strip()
            if len(fallback_text) > 200:
                fallback_text = fallback_text[:200] + '...'
        
        return {
            'success': True,
            'url': request.url,
            'html_length': len(html_content),
            'found_titles': found_titles,
            'found_descriptions': found_descriptions,
            'fallback_text': fallback_text,
            'fallback_length': len(main_content.get_text().strip()) if main_content else 0
        }
        
    except Exception as e:
        logger.error(f"Error in debug job extraction: {e}")
        return {
            'success': False,
            'error': str(e)
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

class PromptTestRequest(BaseModel):
    job_link: str
    job_name: Optional[str] = None
    job_type: Optional[str] = None
    job_role: Optional[str] = None
    job_description: Optional[str] = None

@router.post("/test_prompt")
async def test_prompt(request: PromptTestRequest):
    """
    Test prompt validation and extraction without triggering full workflow
    """
    try:
        logger.info(f"🧪 Testing prompt with job data...")
        
        # Simulate the prompt validation logic
        job_data = {
            'title': request.job_name or '',
            'description': request.job_description or '',
            'company': '',
            'location': '',
            'job_type': request.job_type or '',
            'job_role': request.job_role or ''
        }
        
        # Use the same validation logic as the service
        from ..services.job_extraction_service import JobExtractionService
        job_service = JobExtractionService()
        
        # Test AI validation
        is_valid = await job_service._validate_job_with_ai(job_data, request.job_link)
        
        # Test prompt processing
        prompt_result = {
            "input": {
                "job_link": request.job_link,
                "job_name": request.job_name,
                "job_type": request.job_type,
                "job_role": request.job_role,
                "job_description": request.job_description
            },
            "validation": {
                "is_valid_job": is_valid,
                "ai_validation_passed": is_valid
            },
            "extraction": {
                "job_link": request.job_link,
                "job_name": request.job_name or None,
                "job_type": request.job_type or "Full-time",
                "job_role": request.job_role or None,
                "job_description": request.job_description or None,
                "job_link_final": request.job_link
            },
            "prompt_analysis": {
                "has_title": bool(request.job_name and len(request.job_name.strip()) > 3),
                "has_description": bool(request.job_description and len(request.job_description.strip()) > 50),
                "description_length": len(request.job_description or ""),
                "title_length": len(request.job_name or ""),
                "would_be_accepted": is_valid
            }
        }
        
        return {
            "success": True,
            "test_result": prompt_result,
            "message": "Prompt test completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in prompt test endpoint: {e}")
        return {
            "success": False,
            "error_message": str(e),
            "test_result": None
        }

class SimulateApifyRequest(BaseModel):
    url: str
    Title: Optional[str] = None
    Phone: Optional[str] = None
    Website: Optional[str] = None
    Domain: Optional[str] = None

@router.post("/simulate_apify_workflow")
async def simulate_apify_workflow(request: SimulateApifyRequest):
    """
    Simulate the full Apify workflow without actually calling Apify (to save money)
    This endpoint simulates the data that would come from Apify and runs through the full pipeline
    """
    try:
        logger.info(f"🧪 Simulating Apify workflow for: {request.url}")
        
        # Step 1: Simulate career page detection
        career_service = CareerPagesService()
        career_result = await career_service.detect_career_pages(
            url=request.url,
            include_subdomain_search=True,
            max_pages_to_scan=10,
            strict_filtering=False,
            include_job_boards=True,
            use_scrapy=True
        )
        
        # Step 2: Simulate job extraction if career pages found
        job_results = []
        if career_result.get('success') and career_result.get('career_pages'):
            job_service = JobExtractionService()
            
            for career_page in career_result.get('career_pages', [])[:2]:  # Test first 2 career pages
                # Extract job URLs
                job_urls_result = await job_service.extract_job_urls_only(
                    career_page_url=career_page,
                    max_jobs=5,
                    include_job_data=False
                )
                
                # Extract job details for each job found
                if job_urls_result.get('job_indices'):
                    for job_index in job_urls_result.get('job_indices', [])[:3]:  # Test first 3 jobs
                        job_details_result = await job_service.extract_job_details_only(
                            job_url=career_page,
                            job_index=job_index
                        )
                        
                        if job_details_result.get('success') and job_details_result.get('job'):
                            job = job_details_result['job']
                            job_results.append({
                                "career_page": career_page,
                                "job_index": job_index,
                                "job_data": {
                                    "job_link": job.get('job_link', career_page),
                                    "job_name": job.get('title', ''),
                                    "job_type": job.get('job_type', 'Full-time'),
                                    "job_role": job.get('job_role', ''),
                                    "job_description": job.get('description', '')
                                },
                                "extraction_success": True
                            })
                        else:
                            job_results.append({
                                "career_page": career_page,
                                "job_index": job_index,
                                "job_data": None,
                                "extraction_success": False,
                                "error": job_details_result.get('error_message', 'Unknown error')
                            })
        
        # Step 3: Simulate contact extraction
        contact_service = ContactExtractorService()
        contact_result = await contact_service.extract_contact_info(
            url=request.url,
            include_social=True,
            include_emails=True,
            include_phones=True,
            max_depth=1
        )
        
        # Step 4: Simulate N8N prompt processing
        prompt_tests = []
        for job_result in job_results:
            if job_result.get('job_data'):
                job_data = job_result['job_data']
                
                # Test the prompt validation
                test_job_data = {
                    'title': job_data.get('job_name', ''),
                    'description': job_data.get('job_description', ''),
                    'company': '',
                    'location': '',
                    'job_type': job_data.get('job_type', ''),
                    'job_role': job_data.get('job_role', '')
                }
                
                job_service = JobExtractionService()
                is_valid = await job_service._validate_job_with_ai(test_job_data, job_data.get('job_link', ''))
                
                prompt_tests.append({
                    "job_index": job_result['job_index'],
                    "career_page": job_result['career_page'],
                    "prompt_input": job_data,
                    "ai_validation": {
                        "passed": is_valid,
                        "would_be_accepted": is_valid
                    },
                    "prompt_analysis": {
                        "has_title": bool(job_data.get('job_name', '').strip()),
                        "has_description": bool(job_data.get('job_description', '').strip()),
                        "title_length": len(job_data.get('job_name', '')),
                        "description_length": len(job_data.get('job_description', ''))
                    }
                })
        
        return {
            "success": True,
            "simulation_result": {
                "input_url": request.url,
                "apify_data": {
                    "Title": request.Title,
                    "Phone": request.Phone,
                    "Website": request.Website,
                    "Domain": request.Domain
                },
                "career_detection": {
                    "success": career_result.get('success', False),
                    "career_pages_found": len(career_result.get('career_pages', [])),
                    "career_pages": career_result.get('career_pages', [])
                },
                "job_extraction": {
                    "total_jobs_found": len(job_results),
                    "successful_extractions": len([j for j in job_results if j.get('extraction_success')]),
                    "job_results": job_results
                },
                "contact_extraction": {
                    "emails": contact_result.get('emails', []),
                    "phones": contact_result.get('phones', []),
                    "social_links": contact_result.get('social_links', [])
                },
                "n8n_prompt_tests": prompt_tests,
                "summary": {
                    "total_career_pages": len(career_result.get('career_pages', [])),
                    "total_jobs": len(job_results),
                    "valid_jobs": len([j for j in job_results if j.get('extraction_success')]),
                    "prompt_passed": len([p for p in prompt_tests if p.get('ai_validation', {}).get('passed')]),
                    "prompt_failed": len([p for p in prompt_tests if not p.get('ai_validation', {}).get('passed')])
                }
            },
            "message": "Apify workflow simulation completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in Apify workflow simulation: {e}")
        return {
            "success": False,
            "error_message": str(e),
            "simulation_result": None
        }

@router.post("/test_n8n_prompt")
async def test_n8n_prompt(request: SimulateApifyRequest):
    """
    Test N8N prompt with real job data from a website (without calling Apify)
    This simulates the exact data flow that would happen in N8N
    """
    try:
        logger.info(f"🧪 Testing N8N prompt for: {request.url}")
        
        # Step 1: Get career pages
        career_service = CareerPagesService()
        career_result = await career_service.detect_career_pages(
            url=request.url,
            include_subdomain_search=True,
            max_pages_to_scan=5,
            strict_filtering=False,
            include_job_boards=True,
            use_scrapy=True
        )
        
        # Step 2: Get jobs from career pages
        all_jobs = []
        if career_result.get('success') and career_result.get('career_pages'):
            job_service = JobExtractionService()
            
            for career_page in career_result.get('career_pages', [])[:1]:  # Test first career page only
                # Get job URLs
                job_urls_result = await job_service.extract_job_urls_only(
                    career_page_url=career_page,
                    max_jobs=3,
                    include_job_data=False
                )
                
                # Get job details
                if job_urls_result.get('job_indices'):
                    for job_index in job_urls_result.get('job_indices', [])[:2]:  # Test first 2 jobs
                        job_details_result = await job_service.extract_job_details_only(
                            job_url=career_page,
                            job_index=job_index
                        )
                        
                        if job_details_result.get('success') and job_details_result.get('job'):
                            job = job_details_result['job']
                            all_jobs.append({
                                "job_link": job.get('job_link', career_page),
                                "job_name": job.get('title', ''),
                                "job_type": job.get('job_type', 'Full-time'),
                                "job_role": job.get('job_role', ''),
                                "job_description": job.get('description', '')
                            })
        
        # Step 3: Test each job with N8N prompt logic
        prompt_results = []
        for i, job in enumerate(all_jobs):
            # This simulates the exact data that would go to N8N prompt
            n8n_input = {
                "job_link": job.get('job_link', ''),
                "job_name": job.get('job_name', ''),
                "job_type": job.get('job_type', ''),
                "job_role": job.get('job_role', ''),
                "job_description": job.get('job_description', '')
            }
            
            # Test AI validation (same as N8N would do)
            test_job_data = {
                'title': n8n_input.get('job_name', ''),
                'description': n8n_input.get('job_description', ''),
                'company': '',
                'location': '',
                'job_type': n8n_input.get('job_type', ''),
                'job_role': n8n_input.get('job_role', '')
            }
            
            job_service = JobExtractionService()
            is_valid = await job_service._validate_job_with_ai(test_job_data, n8n_input.get('job_link', ''))
            
            # Simulate N8N prompt output
            if is_valid:
                n8n_output = {
                    "job_link": n8n_input.get('job_link'),
                    "job_name": n8n_input.get('job_name'),
                    "job_type": n8n_input.get('job_type') or "Full-time",
                    "job_role": n8n_input.get('job_role'),
                    "job_description": n8n_input.get('job_description')
                }
            else:
                n8n_output = {
                    "job_link": n8n_input.get('job_link'),
                    "job_name": None,
                    "job_type": None,
                    "job_role": None,
                    "job_description": None
                }
            
            prompt_results.append({
                "job_index": i + 1,
                "n8n_input": n8n_input,
                "ai_validation_passed": is_valid,
                "n8n_output": n8n_output,
                "analysis": {
                    "has_title": bool(n8n_input.get('job_name', '').strip()),
                    "has_description": bool(n8n_input.get('job_description', '').strip()),
                    "title_length": len(n8n_input.get('job_name', '')),
                    "description_length": len(n8n_input.get('job_description', ''))
                }
            })
        
        return {
            "success": True,
            "test_result": {
                "input_url": request.url,
                "apify_simulation": {
                    "Title": request.Title,
                    "Phone": request.Phone,
                    "Website": request.Website,
                    "Domain": request.Domain
                },
                "career_pages_found": len(career_result.get('career_pages', [])),
                "career_pages": career_result.get('career_pages', []),
                "jobs_extracted": len(all_jobs),
                "n8n_prompt_tests": prompt_results,
                "summary": {
                    "total_jobs": len(all_jobs),
                    "prompt_passed": len([p for p in prompt_results if p.get('ai_validation_passed')]),
                    "prompt_failed": len([p for p in prompt_results if not p.get('ai_validation_passed')]),
                    "success_rate": f"{(len([p for p in prompt_results if p.get('ai_validation_passed')]) / max(len(prompt_results), 1)) * 100:.1f}%"
                }
            },
            "message": "N8N prompt test completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in N8N prompt test: {e}")
        return {
            "success": False,
            "error_message": str(e),
            "test_result": None
        }
