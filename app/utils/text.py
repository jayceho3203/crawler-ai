# app/utils/text.py
"""
Text normalization utilities to prevent URL decode errors
"""

from typing import Any
import re
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

# utils for phone extraction
WS_CLASS = r"\s\u00A0\u2000-\u200B"            # space + NBSP + zero-width range
SEP_CLASS = rf"[{WS_CLASS}\.\-\(\)]"          # cho phép . - ( ) và các khoảng trắng unicode
SEP = rf"{SEP_CLASS}*"                        # 0+ ký tự phân tách

def normalize_text(s: str) -> str:
    # gom mọi loại khoảng trắng về 1 space
    return re.sub(rf"[{WS_CLASS}]+", " ", s).strip()

def clean_phone(candidate: str) -> str | None:
    # giữ + và số
    s = re.sub(r"[^\d+]", "", candidate)
    if s.startswith("+84"):
        s = "0" + s[3:]
    s = re.sub(r"\D", "", s)
    # VN: di động 10 số; cố định 10–11 số (tùy mã vùng)
    return s if 10 <= len(s) <= 11 else None
