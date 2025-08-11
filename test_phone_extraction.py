#!/usr/bin/env python3
"""
Test phone extraction from ICS-P footer
"""

import requests
import re
from bs4 import BeautifulSoup

def test_ics_p_phone_extraction():
    print("🔍 Testing phone extraction from ICS-P footer...")
    
    try:
        # Fetch ICS-P homepage
        html = requests.get('https://www.ics-p.vn/vi', headers={'User-Agent':'crawler-ai/1.0'}).text
        soup = BeautifulSoup(html, 'lxml')
        
        # Find footer
        footer = soup.select_one('footer, [role=contentinfo], #footer, .footer, .site-footer, .main-footer, .bottom-footer') or soup
        
        # Normalize text
        text = re.sub(r'[\s\u00A0\u2000-\u200B]+', ' ', footer.get_text(' ', strip=True))
        
        # Phone regex pattern
        rx = re.compile(r'(?<!\d)(?:\+?84|0)(?:[\s\.\-\(\)\u00A0\u2000-\u200B]*\d){8,10}(?!\d)')
        
        # Extract phones
        phones = []
        for m in rx.finditer(text):
            s = re.sub(r'[^\d+]', '', m.group(0))
            if s.startswith('+84'): 
                s = '0' + s[3:]
            s = re.sub(r'\D', '', s)
            if 10 <= len(s) <= 11 and s not in phones:
                phones.append(s)
        
        print(f"📞 Phones found: {phones}")
        print(f"🦶 Footer text preview: {text[:300]}")
        print(f"✅ Expected: ['02466899275']")
        
        if '02466899275' in phones:
            print("🎉 SUCCESS: Found expected phone number!")
        else:
            print("❌ FAILED: Expected phone number not found!")
            
        return phones
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    test_ics_p_phone_extraction()
