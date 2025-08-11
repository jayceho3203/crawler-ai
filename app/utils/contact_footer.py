"""
Footer contact extraction utilities
"""

import re
from bs4 import BeautifulSoup

# khoảng trắng unicode hay gặp trong footer
WS = r"\s\u00A0\u2000-\u200B"
SEP_CLASS = rf"[{WS}\.\-\(\)]"
SEP = rf"{SEP_CLASS}*"

# VN: 0xxxx… hoặc +84… cho phép chèn dấu / khoảng trắng unicode giữa các block số
VN_PHONE_RX = re.compile(rf"(?<!\d)(?:\+?84|0)(?:{SEP}\d){{8,10}}(?!\d)")
EMAIL_RX = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)

def normalize_text(s: str) -> str:
    """Normalize text, gom mọi loại khoảng trắng về 1 space"""
    return re.sub(rf"[{WS}]+", " ", s or "").strip()

def clean_phone(raw: str) -> str | None:
    """Clean phone number, giữ + và số"""
    s = re.sub(r"[^\d+]", "", raw or "")
    if s.startswith("+84"):
        s = "0" + s[3:]
    s = re.sub(r"\D", "", s)
    # VN: di động 10 số; cố định 10–11 số (tùy mã vùng)
    return s if 10 <= len(s) <= 11 else None

def pick_footer_node(soup: BeautifulSoup):
    """Tìm footer node linh hoạt"""
    # footer "thực tế"
    node = soup.select_one(
        "footer, [role=contentinfo], #footer, .footer, .site-footer, .main-footer, .bottom-footer"
    )
    if node:
        return node
    # id/class chứa 'footer'
    for el in soup.find_all(True):
        ident = (el.get("id") or "") + " " + " ".join(el.get("class") or [])
        if "footer" in ident.lower():
            return el
    # fallback: block cuối
    blocks = soup.select("footer, section, div")
    return blocks[-1] if blocks else soup

def extract_footer_contacts_from_html(html: str) -> dict:
    """Extract contact info từ footer HTML"""
    soup = BeautifulSoup(html or "", "html.parser")  # dùng html.parser thay vì lxml
    footer = pick_footer_node(soup)

    # tel: trước
    tel_nums: list[str] = []
    for a in footer.select('a[href^="tel:"]'):
        n = clean_phone((a.get("href") or "")[4:])
        if n and n not in tel_nums:
            tel_nums.append(n)

    # text node
    text = normalize_text(footer.get_text(" ", strip=True))
    text_nums: list[str] = []
    for m in VN_PHONE_RX.finditer(text):
        n = clean_phone(m.group(0))
        if n and n not in text_nums:
            text_nums.append(n)

    # emails trong footer
    emails = []
    for m in EMAIL_RX.finditer(text):
        e = m.group(0).lower()
        if e not in emails:
            emails.append(e)

    phones = list(dict.fromkeys(tel_nums + text_nums))  # dedupe + giữ thứ tự
    return {
        "phones": phones,
        "emails": emails,
        "debug": {
            "footer_tag": getattr(footer, "name", None),
            "tel_raw": tel_nums,
            "text_first200": text[:200],
        },
    }
