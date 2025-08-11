"""
Debug routes for testing footer extraction
"""

from fastapi import APIRouter, Query
from pydantic import HttpUrl
import httpx
from app.utils.contact_footer import extract_footer_contacts_from_html

router = APIRouter()

async def fetch_html(url: str) -> str:
    """Fetch HTML content from URL"""
    transport = httpx.AsyncHTTPTransport(retries=2)
    async with httpx.AsyncClient(timeout=15, transport=transport, headers={"User-Agent": "crawler-ai/1.0"}) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text

@router.get("/api/v1/debug/footer")
async def debug_footer(url: HttpUrl = Query(..., description="Page to inspect footer")):
    """Debug endpoint để test footer extraction"""
    try:
        html = await fetch_html(str(url))
        data = extract_footer_contacts_from_html(html)
        return {
            "url": str(url),
            "success": True,
            **data
        }
    except Exception as e:
        return {
            "url": str(url),
            "success": False,
            "error": str(e),
            "phones": [],
            "emails": [],
            "debug": {}
        }
