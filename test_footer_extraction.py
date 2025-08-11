#!/usr/bin/env python3
"""
Test đơn giản: chỉ lấy contact info từ footer
"""

import requests
import re
from bs4 import BeautifulSoup
from typing import Dict, List

def extract_footer_contact_simple(url: str) -> Dict[str, List[str]]:
    """
    Hàm đơn giản chỉ để test footer extraction
    """
    print(f"🔍 Testing footer extraction for: {url}")
    
    try:
        # 1. Fetch HTML
        response = requests.get(url, headers={'User-Agent': 'crawler-ai/1.0'}, timeout=10)
        response.raise_for_status()
        html = response.text
        
        print(f"✅ HTML fetched, length: {len(html)}")
        
        # 2. Parse với BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # 3. Tìm footer (giống logic trong service)
        footer = pick_footer_node_simple(soup)
        print(f"🦶 Footer found: {getattr(footer, 'name', 'unknown')}")
        
        # 4. Extract phones từ footer
        phones = extract_phones_from_footer_simple(footer)
        print(f"📞 Phones found: {phones}")
        
        # 5. Extract emails từ footer
        emails = extract_emails_from_footer_simple(footer)
        print(f"📧 Emails found: {emails}")
        
        return {
            'phones': phones,
            'emails': emails,
            'success': True
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            'phones': [],
            'emails': [],
            'success': False,
            'error': str(e)
        }

def pick_footer_node_simple(soup: BeautifulSoup):
    """Tìm footer node đơn giản"""
    # Thử các selector phổ biến
    selectors = [
        "footer",
        "[role=contentinfo]", 
        "#footer",
        ".footer",
        ".site-footer",
        ".main-footer",
        ".bottom-footer"
    ]
    
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            return node
    
    # Fallback: tìm element có id/class chứa 'footer'
    for el in soup.find_all(True):
        ident = (el.get("id") or "") + " " + " ".join(el.get("class") or [])
        if "footer" in ident.lower():
            return el
    
    # Fallback cuối: block cuối trang
    blocks = soup.select("footer, section, div")
    return blocks[-1] if blocks else soup

def extract_phones_from_footer_simple(footer) -> List[str]:
    """Extract phones từ footer đơn giản"""
    phones = []
    
    # 1. Lấy từ tel: links
    for a in footer.select('a[href^="tel:"]'):
        number = a.get('href', '')[4:]  # bỏ "tel:"
        clean_num = clean_phone_simple(number)
        if clean_num and clean_num not in phones:
            phones.append(clean_num)
            print(f"   📞 From tel: link: {number} -> {clean_num}")
    
    # 2. Lấy từ text content
    text = normalize_text_simple(footer.get_text(" ", strip=True))
    text_phones = extract_phones_from_text_simple(text)
    
    for phone in text_phones:
        if phone not in phones:
            phones.append(phone)
            print(f"   📞 From text: {phone}")
    
    return phones

def extract_emails_from_footer_simple(footer) -> List[str]:
    """Extract emails từ footer đơn giản"""
    emails = []
    
    # Email pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    text = footer.get_text()
    matches = re.findall(email_pattern, text, re.IGNORECASE)
    
    for email in matches:
        if email not in emails:
            emails.append(email)
            print(f"   📧 Email found: {email}")
    
    return emails

def normalize_text_simple(s: str) -> str:
    """Normalize text đơn giản"""
    # Gom mọi loại khoảng trắng về 1 space
    return re.sub(r'[\s\u00A0\u2000-\u200B]+', ' ', s).strip()

def extract_phones_from_text_simple(text: str) -> List[str]:
    """Extract phones từ text đơn giản"""
    phones = []
    
    # Phone regex pattern
    rx = re.compile(r'(?<!\d)(?:\+?84|0)(?:[\s\.\-\(\)\u00A0\u2000-\u200B]*\d){8,10}(?!\d)')
    
    for m in rx.finditer(text):
        raw_phone = m.group(0)
        clean_num = clean_phone_simple(raw_phone)
        if clean_num and clean_num not in phones:
            phones.append(clean_num)
    
    return phones

def clean_phone_simple(candidate: str) -> str | None:
    """Clean phone number đơn giản"""
    # Giữ + và số
    s = re.sub(r'[^\d+]', '', candidate)
    if s.startswith('+84'):
        s = '0' + s[3:]
    s = re.sub(r'\D', '', s)
    # VN: di động 10 số; cố định 10–11 số (tùy mã vùng)
    return s if 10 <= len(s) <= 11 else None

def test_ics_p():
    """Test với ICS-P"""
    print("=" * 50)
    print("🧪 TESTING ICS-P FOOTER EXTRACTION")
    print("=" * 50)
    
    result = extract_footer_contact_simple('https://www.ics-p.vn/vi')
    
    print("\n" + "=" * 50)
    print("📊 FINAL RESULTS:")
    print("=" * 50)
    print(f"Success: {result['success']}")
    print(f"Phones: {result['phones']}")
    print(f"Emails: {result['emails']}")
    
    # Kiểm tra kết quả mong đợi
    if '02466899275' in result['phones']:
        print("🎉 SUCCESS: Found expected phone '02466899275'!")
    else:
        print("❌ FAILED: Expected phone '02466899275' not found!")
        print("   Expected: ['02466899275']")
        print("   Got: ", result['phones'])

if __name__ == "__main__":
    test_ics_p()
