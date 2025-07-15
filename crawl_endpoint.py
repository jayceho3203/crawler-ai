# crawl_endpoint.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import json
import logging
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
from datetime import datetime

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.extraction_strategy import RegexExtractionStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai import MarkdownGenerationResult

# Import from the refactored contact_extractor
from contact_extractor import (
    process_extracted_crawl_results,
    SOCIAL_DOMAINS,
    CAREER_KEYWORDS,
    normalize_url
)

# Keep urllib.parse if used for any direct URL manipulation in the endpoint itself
from urllib.parse import urlparse, urljoin

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class CrawlRequest(BaseModel):
    url: str

class CrawlResponse(BaseModel):
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


@app.post("/crawl_and_extract_contact_info", response_model=CrawlResponse)
async def crawl_and_extract_contact_info(request: CrawlRequest):
    start_time = datetime.now()
    logger.info(f"🚀 Starting crawl for: {request.url}")
    
    response_data = CrawlResponse(requested_url=request.url, success=False)

    contact_regex_strategy = RegexExtractionStrategy(
        pattern=(
            RegexExtractionStrategy.Email |
            RegexExtractionStrategy.Url
        )
    )

    config_params = {
        "extraction_strategy": contact_regex_strategy,
        "markdown_generator": DefaultMarkdownGenerator()
    }
    run_config = CrawlerRunConfig(**config_params)

    async with AsyncWebCrawler() as crawler:
        try:
            logger.info(f"📡 Crawling: {request.url}")
            result = await crawler.arun(url=request.url, config=run_config)

            response_data.final_url = result.url
            response_data.success = result.success
            response_data.error_message = result.error_message
            response_data.status_code = result.status_code

            if result.markdown and isinstance(result.markdown, MarkdownGenerationResult):
                 response_data.fit_markdown = result.markdown.fit_markdown
            elif isinstance(result.markdown, str): # Fallback if markdown is just a string
                 response_data.fit_markdown = result.markdown

            logger.info(f"✅ Crawl completed: {request.url} - Status: {result.status_code}")

            data_for_extractor = []
            processed_html_for_urls = False # Flag to track if BS was used

            # Extract Emails (from crawl_result.raw_extracted_data if it exists and has emails)
            # Assuming result.extracted_content is the JSON string from RegexExtractionStrategy
            if result.extracted_content:
                try:
                    # Parse the JSON string from extracted_content
                    # This part assumes extracted_content is where regex results are stored as a JSON string
                    # And that this JSON string, when parsed, becomes a list of dicts like:
                    # [{"label": "email", "value": "test@example.com"}, {"label": "url", "value": "http..."}]
                    parsed_extracted_content = json.loads(result.extracted_content)
                    response_data.raw_extracted_data = parsed_extracted_content # Store for debugging/transparency

                    if isinstance(parsed_extracted_content, list):
                        for item in parsed_extracted_content:
                            if isinstance(item, dict) and item.get("label") == "email" and item.get("value"):
                                data_for_extractor.append({"label": "email", "value": str(item["value"])})
                except json.JSONDecodeError:
                    # Log or handle error if extracted_content is not valid JSON
                    logger.error(f"❌ Error decoding JSON from extracted_content: {result.extracted_content}")
                    # Optionally, set an error message in response_data
                    # response_data.error_message = "Failed to parse raw extracted data."


            # Extract URLs (using BeautifulSoup from crawl_result.html)
            if result.html: # <<< CORRECTED: Ensure this is .html
                try:
                    soup = BeautifulSoup(result.html, "html.parser") # <<< CORRECTED: Ensure this is .html
                    for a_tag in soup.find_all('a', href=True):
                        href = a_tag.get('href')
                        if href and str(href).strip():
                            data_for_extractor.append({"label": "url", "value": str(href)})
                    processed_html_for_urls = True
                except Exception as e:
                    logger.error(f"❌ Error during BeautifulSoup parsing: {e}")
                    # Potentially log this error, but allow fallback

            # Fallback for URLs if HTML wasn't processed by BeautifulSoup
            # (e.g. crawl_result.html was None or BS failed)
            # and raw_extracted_data from crawler has URL data (assuming this means parsed_extracted_content)
            if not processed_html_for_urls and response_data.raw_extracted_data and isinstance(response_data.raw_extracted_data, list):
                for item in response_data.raw_extracted_data: # Use response_data.raw_extracted_data which holds the parsed content
                    if isinstance(item, dict) and item.get("label") == "url" and item.get("value"):
                        is_duplicate = False
                        # Check against already added items (which could be from regex emails or BS URLs)
                        for existing_item in data_for_extractor:
                            if existing_item.get("label") == "url" and existing_item.get("value") == item.get("value"):
                                is_duplicate = True
                                break
                        if not is_duplicate:
                             data_for_extractor.append({"label": "url", "value": str(item["value"])})
    
            # Call process_extracted_crawl_results
            classified_contacts = process_extracted_crawl_results(
                raw_extracted_list=data_for_extractor,
                base_url=str(result.url) if result.url else request.url # Use result.url (final URL) if available
            )
            response_data.emails = classified_contacts.get("emails", [])
            response_data.social_links = classified_contacts.get("social_links", [])
            response_data.career_pages = classified_contacts.get("career_pages", [])

            # Log extraction results
            logger.info(f"📊 Extraction results for {request.url}:")
            logger.info(f"   📧 Emails: {len(response_data.emails)}")
            logger.info(f"   🔗 Social links: {len(response_data.social_links)}")
            logger.info(f"   💼 Career pages: {len(response_data.career_pages)}")

        except Exception as e:
            response_data.success = False
            response_data.error_message = f"An unexpected error occurred during crawling: {str(e)}"
            logger.error(f"❌ Crawl failed for {request.url}: {str(e)}")
            # Ensure status_code is not None if an early exception occurs before result object is formed
            if response_data.status_code is None:
                 response_data.status_code = 500 # Generic server error

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"⏱️ Total time for {request.url}: {duration:.2f}s")
    
    return response_data

@app.get("/stats")
async def get_crawl_stats():
    """Get crawling statistics"""
    return {
        "message": "Crawl API is running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "crawl": "/crawl_and_extract_contact_info",
            "stats": "/stats"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)