#!/usr/bin/env python3
"""
Test script for enhanced career page filtering and job link detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.career_detector import (
    analyze_url_structure, check_early_rejection, calculate_career_score,
    validate_career_page_content, filter_career_urls
)
from app.services.job_extractor import (
    analyze_job_link_structure, calculate_job_link_score,
    validate_job_link_content, extract_job_links_detailed
)
from bs4 import BeautifulSoup

def test_career_url_filtering():
    """Test career URL filtering with various examples"""
    print("🧪 Testing Career URL Filtering")
    print("=" * 50)
    
    # Test URLs with expected results
    test_urls = [
        # Good career URLs (should pass)
        ("https://example.com/career", "Good career page"),
        ("https://example.com/tuyen-dung", "Vietnamese career page"),
        ("https://example.com/jobs", "Jobs page"),
        ("https://example.com/careers/developer", "Developer career page"),
        ("https://example.com/tuyen-dung-nhan-vien", "Vietnamese employee recruitment"),
        
        # Bad URLs (should be rejected)
        ("https://example.com/blog/2024/01/15/news", "Blog post with date"),
        ("https://example.com/product/service", "Product/service page"),
        ("https://example.com/about/contact", "About/contact page"),
        ("https://example.com/news/article-12345", "News article with ID"),
        ("https://example.com/admin/login", "Admin login page"),
        ("https://example.com/cart/checkout", "Shopping cart"),
        ("https://example.com/user/profile", "User profile"),
        ("https://example.com/very/deep/path/that/is/too/long", "Too deep path"),
        ("https://example.com/document.pdf", "PDF file"),
        ("https://example.com/image.jpg", "Image file"),
    ]
    
    for url, description in test_urls:
        print(f"\n🔍 Testing: {description}")
        print(f"   URL: {url}")
        
        # Analyze URL structure
        url_analysis = analyze_url_structure(url)
        print(f"   Path depth: {url_analysis['path_depth']}")
        print(f"   Path: {url_analysis['path']}")
        
        # Check early rejection
        is_rejected, rejection_reason = check_early_rejection(url, url_analysis)
        if is_rejected:
            print(f"   ❌ REJECTED: {rejection_reason}")
            continue
        
        # Calculate career score
        career_score, score_breakdown = calculate_career_score(url, url_analysis)
        print(f"   Career score: {career_score}")
        
        # Show top scoring factors
        top_factors = sorted(score_breakdown.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        for factor, score in top_factors:
            print(f"     {factor}: {score}")
        
        # Final decision
        if career_score >= 6:
            print(f"   ✅ ACCEPTED (score: {career_score})")
        else:
            print(f"   ❌ REJECTED (score: {career_score} < 6)")

def test_job_link_detection():
    """Test job link detection with various examples"""
    print("\n\n🧪 Testing Job Link Detection")
    print("=" * 50)
    
    # Test job links with expected results
    test_job_links = [
        # Good job links (should have high scores)
        ("https://example.com/job/developer", "Apply for Developer", "Good job link"),
        ("https://example.com/career/engineer", "Join our team", "Career engineer link"),
        ("https://example.com/tuyen-dung/nhan-vien", "Tuyển dụng nhân viên", "Vietnamese job link"),
        ("https://example.com/position/senior-dev", "Senior Developer Position", "Senior position"),
        ("https://example.com/apply/123", "Apply Now", "Apply button"),
        
        # Bad job links (should have low scores)
        ("https://example.com/blog/news", "Read more", "Blog link"),
        ("https://example.com/product/details", "View product", "Product link"),
        ("https://example.com/about/team", "Our team", "About team link"),
        ("https://example.com/contact", "Contact us", "Contact link"),
        ("https://example.com/admin", "Admin panel", "Admin link"),
    ]
    
    for url, link_text, description in test_job_links:
        print(f"\n🔍 Testing: {description}")
        print(f"   URL: {url}")
        print(f"   Link text: '{link_text}'")
        
        # Analyze job link structure
        link_analysis = analyze_job_link_structure(url, link_text)
        print(f"   Path depth: {link_analysis['path_depth']}")
        print(f"   Path: {link_analysis['path']}")
        
        # Calculate job link score
        job_score, score_breakdown = calculate_job_link_score(url, link_text)
        print(f"   Job score: {job_score}")
        
        # Show top scoring factors
        top_factors = sorted(score_breakdown.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
        for factor, score in top_factors:
            print(f"     {factor}: {score}")
        
        # Final decision
        if job_score >= 5:
            print(f"   ✅ ACCEPTED (score: {job_score})")
        else:
            print(f"   ❌ REJECTED (score: {job_score} < 5)")

def test_filter_career_urls_batch():
    """Test batch filtering of career URLs"""
    print("\n\n🧪 Testing Batch Career URL Filtering")
    print("=" * 50)
    
    # Sample career URLs to test
    test_career_urls = [
        "https://example.com/career",
        "https://example.com/tuyen-dung",
        "https://example.com/jobs",
        "https://example.com/blog/2024/01/15/news",
        "https://example.com/product/service",
        "https://example.com/careers/developer",
        "https://example.com/about/contact",
        "https://example.com/tuyen-dung-nhan-vien",
        "https://example.com/admin/login",
        "https://example.com/career/engineer",
    ]
    
    print(f"Testing {len(test_career_urls)} URLs...")
    
    # Apply filtering
    filtered_results = filter_career_urls(test_career_urls)
    
    print(f"\n📊 Results:")
    print(f"   Raw URLs: {len(test_career_urls)}")
    print(f"   Filtered URLs: {len(filtered_results)}")
    
    print(f"\n✅ Accepted URLs:")
    for result in filtered_results:
        print(f"   {result['url']} (score: {result['career_score']})")
        print(f"     Reason: {result['acceptance_reason']}")

def test_job_link_extraction():
    """Test job link extraction from HTML"""
    print("\n\n🧪 Testing Job Link Extraction from HTML")
    print("=" * 50)
    
    # Sample HTML with job links
    sample_html = """
    <html>
    <head><title>Company Careers</title></head>
    <body>
        <nav>
            <a href="/career">Careers</a>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
        </nav>
        <div class="job-listings">
            <div class="job-item">
                <h3>Senior Developer</h3>
                <a href="/job/senior-developer" class="apply-btn">Apply Now</a>
            </div>
            <div class="job-item">
                <h3>Frontend Engineer</h3>
                <a href="/career/frontend-engineer">View Position</a>
            </div>
            <div class="job-item">
                <h3>Product Manager</h3>
                <a href="/position/product-manager">Join our team</a>
            </div>
        </div>
        <footer>
            <a href="/blog">Blog</a>
            <a href="/product">Product</a>
        </footer>
    </body>
    </html>
    """
    
    soup = BeautifulSoup(sample_html, 'html.parser')
    base_url = "https://example.com"
    
    # Extract job links
    job_links = extract_job_links_detailed(soup, base_url)
    
    print(f"📊 Extracted {len(job_links)} job links:")
    for i, link in enumerate(job_links, 1):
        print(f"\n{i}. {link['url']}")
        print(f"   Text: '{link['link_text']}'")
        print(f"   Score: {link['job_score']}")
        print(f"   Selector: {link['selector_used']}")

def main():
    """Run all tests"""
    print("🚀 Enhanced Career Page and Job Link Detection Tests")
    print("=" * 60)
    
    try:
        test_career_url_filtering()
        test_job_link_detection()
        test_filter_career_urls_batch()
        test_job_link_extraction()
        
        print("\n\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 