#!/usr/bin/env python3
"""
Debug script to test career page filtering logic
"""

def test_career_logic():
    """Test the career page filtering logic directly"""
    
    # URLs from Hyperlogy test
    test_urls = [
        "https://www.hyperlogy.com/vi/tuyen-dung/dang-can-tuyen/",
        "https://www.hyperlogy.com/products-en/software/",
        "https://www.hyperlogy.com/en/allow-customers-to-open-payment-accounts-without-direct-meeting-a-race-for-market-share-expanding-of-vietnamese-banks/",
        "https://www.hyperlogy.com/en/smart-rm-what-is-it-smart-rms-important-part-in-the-banking-system/",
        "https://www.hyperlogy.com/en/products-en/software/",
        "https://www.hyperlogy.com/products-en/customer-experience-management/",
        "https://www.hyperlogy.com/en/video-call-online-ekyc-solutions-powered-support-for-digital-onboarding/",
        "https://www.hyperlogy.com/en/military-commercial-join-stock-bank-mb-completed-the-target-of-digital-bank-with-smart-form/",
        "https://www.hyperlogy.com/en/ai-and-biometrics-major-trends-that-shape-the-online-banking-market/",
        "https://www.hyperlogy.com/en/revolutionizing-bank-with-business-intelligence-comprehensive-digitalization-orientation/"
    ]
    
    # Career exact patterns from the code
    career_exact_patterns = [
        '/tuyen-dung', '/tuyển-dụng', '/tuyendung',
        '/viec-lam', '/việc-làm', '/vieclam',
        '/co-hoi', '/cơ-hội', '/cohoi',
        '/nhan-vien', '/nhân-viên', '/nhanvien',
        '/ung-vien', '/ứng-viên', '/ungvien',
        '/cong-viec', '/công-việc', '/congviec',
        '/lam-viec', '/làm-việc', '/lamviec',
        '/moi', '/mời',
        '/thu-viec', '/thử-việc', '/thuviec',
        '/chinh-thuc', '/chính-thức', '/chinhthuc',
        '/tim-viec', '/tìm-việc', '/timviec',
        '/dang-tuyen', '/đang-tuyển', '/dangtuyen',
        '/career', '/careers', '/job', '/jobs', '/hiring', '/recruitment',
        '/employment', '/vacancy', '/vacancies', '/opportunity', '/opportunities',
        '/position', '/positions', '/apply', '/application', '/applications',
        '/join-us', '/joinus', '/work-with-us', '/workwithus',
        '/open-role', '/open-roles', '/openrole', '/openroles',
        '/we-are-hiring', '/wearehiring', '/talent', '/team'
    ]
    
    # Strong non-career indicators
    strong_non_career_indicators = ['blog', 'news', 'article', 'post', 'story', 'product', 'service', 'solution', 'about', 'contact', 'industry', 'market', 'research', 'analysis', 'report', 'webinar', 'conference', 'workshop', 'training', 'certification', 'award', 'recognition', 'milestone', 'achievement', 'case-study', 'success-story', 'testimonial', 'review', 'tutorial', 'guide', 'whitepaper', 'press', 'media', 'publication', 'tin-tuc', 'tin', 'impact', 'social', 'enterprise', 'doanh-nghiep', 'application', 'deployed', 'successfully', 'implementation', 'solution', 'technology', 'digital', 'transformation', 'business', 'customer', 'experience', 'management']
    
    print("🔍 DEBUGGING Career Page Filtering Logic")
    print("=" * 60)
    
    for url in test_urls:
        print(f"\n🔗 Testing: {url}")
        
        # Parse URL
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        path_lower = parsed_url.path.lower() if parsed_url.path else ""
        query_lower = parsed_url.query.lower()
        full_path = f"{path_lower}?{query_lower}"
        
        print(f"  Path: {path_lower}")
        
        # Check early rejection
        has_strong_non_career = any(indicator in path_lower for indicator in strong_non_career_indicators)
        print(f"  Early rejection: {'❌ REJECTED' if has_strong_non_career else '✅ PASSED'}")
        
        if has_strong_non_career:
            matching_indicators = [indicator for indicator in strong_non_career_indicators if indicator in path_lower]
            print(f"    Matching indicators: {matching_indicators}")
            continue
        
        # Check career patterns
        has_clear_career_pattern = False
        matching_patterns = []
        
        for pattern in career_exact_patterns:
            if pattern in path_lower:
                has_clear_career_pattern = True
                matching_patterns.append(pattern)
                break
        
        print(f"  Career pattern: {'✅ FOUND' if has_clear_career_pattern else '❌ NOT FOUND'}")
        if matching_patterns:
            print(f"    Matching patterns: {matching_patterns}")
        
        # Final result
        if has_clear_career_pattern:
            print(f"  🎯 RESULT: ✅ ACCEPTED (Career page)")
        else:
            print(f"  🎯 RESULT: ❌ REJECTED (Not a career page)")

if __name__ == "__main__":
    test_career_logic() 