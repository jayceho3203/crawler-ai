# app/utils/text.py
"""
Text normalization utilities to prevent URL decode errors
"""

from typing import Any
try:
    from yarl import URL
except ImportError:
    class URL:  # fallback type
        pass

from urllib.parse import ParseResult

def to_text(v: Any) -> str:
    """Convert any value to text, handling URL objects properly"""
    if isinstance(v, (bytes, bytearray)):
        return v.decode("utf-8", errors="ignore")
    if isinstance(v, URL):
        return str(v)
    if isinstance(v, ParseResult):
        return v.geturl()
    return str(v)

def normalize_url(u: Any) -> str:
    """Normalize URL by removing fragments and converting to string"""
    u = to_text(u)  # ✅ ép về str
    if "#" in u:
        u = u.split("#", 1)[0]  # bỏ fragment như #vitex_contact
    return u.strip()

def safe_decode(data: Any, encoding: str = "utf-8") -> str:
    """Safely decode data, handling both bytes and text"""
    if isinstance(data, (bytes, bytearray)):
        return data.decode(encoding, errors="ignore")
    return to_text(data)
