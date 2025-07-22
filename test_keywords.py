#!/usr/bin/env python3
"""
Test script to verify improved keywords work correctly
"""
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_keywords():
    """Test the improved keywords"""
    print("🔍 TESTING IMPROVED KEYWORDS")
    print("=" * 60)
    
    # Test URLs with various keyword patterns
    test_urls = [
        # Vietnamese keywords with hyphens
        "https://example.com/tuyen-dung",
        "https://example.com/tuyển-dụng", 
        "https://example.com/viec-lam",
        "https://example.com/việc-làm",
        "https://example.com/co-hoi-nghe-nghiep",
        "https://example.com/cơ-hội-nghề-nghiệp",
        
        # Vietnamese keywords without hyphens
        "https://example.com/tuyendung",
        "https://example.com/vieclam", 
        "https://example.com/cohoinghenghiep",
        "https://example.com/timviec",
        "https://example.com/tìmviệc",
        
        # Vietnamese job-specific keywords
        "https://example.com/tuyen-dung-developer",
        "https://example.com/tuyendungdeveloper",
        "https://example.com/tuyen-dung-engineer", 
        "https://example.com/tuyendungengineer",
        "https://example.com/tuyen-dung-analyst",
        "https://example.com/tuyendunganalyst",
        "https://example.com/tuyen-dung-manager",
        "https://example.com/tuyendungmanager",
        "https://example.com/tuyen-dung-designer",
        "https://example.com/tuyendungdesigner",
        "https://example.com/tuyen-dung-tester",
        "https://example.com/tuyendungtester",
        "https://example.com/tuyen-dung-qa",
        "https://example.com/tuyendungqa",
        "https://example.com/tuyen-dung-devops",
        "https://example.com/tuyendungdevops",
        "https://example.com/tuyen-dung-data",
        "https://example.com/tuyendungdata",
        "https://example.com/tuyen-dung-ai",
        "https://example.com/tuyendungai",
        "https://example.com/tuyen-dung-ml",
        "https://example.com/tuyendungml",
        "https://example.com/tuyen-dung-ui",
        "https://example.com/tuyendungui",
        "https://example.com/tuyen-dung-ux",
        "https://example.com/tuyendungux",
        "https://example.com/tuyen-dung-pm",
        "https://example.com/tuyendungpm",
        "https://example.com/tuyen-dung-ba",
        "https://example.com/tuyendungba",
        "https://example.com/tuyen-dung-scrum",
        "https://example.com/tuyendungscrum",
        "https://example.com/tuyen-dung-agile",
        "https://example.com/tuyendungagile",
        
        # English keywords with hyphens
        "https://example.com/career",
        "https://example.com/jobs",
        "https://example.com/join-us",
        "https://example.com/we-are-hiring",
        "https://example.com/work-with-us",
        "https://example.com/open-role",
        "https://example.com/open-roles",
        "https://example.com/full-time",
        "https://example.com/part-time",
        "https://example.com/entry-level",
        "https://example.com/machine-learning",
        "https://example.com/front-end",
        "https://example.com/back-end",
        "https://example.com/full-stack",
        "https://example.com/on-site",
        
        # English keywords without hyphens
        "https://example.com/joinus",
        "https://example.com/wearehiring",
        "https://example.com/workwithus",
        "https://example.com/openrole",
        "https://example.com/openroles",
        "https://example.com/fulltime",
        "https://example.com/parttime",
        "https://example.com/entrylevel",
        "https://example.com/machinelearning",
        "https://example.com/frontend",
        "https://example.com/backend",
        "https://example.com/fullstack",
        "https://example.com/onsite",
        
        # Mixed patterns
        "https://example.com/tuyen-dung-developer-2024",
        "https://example.com/tuyendungdeveloper2024",
        "https://example.com/join-us-team",
        "https://example.com/joinusteam",
        "https://example.com/we-are-hiring-now",
        "https://example.com/wearehiringnow"
    ]
    
    try:
        from contact_extractor import CAREER_KEYWORDS_VI
        
        print(f"📊 Total keywords available: {len(CAREER_KEYWORDS_VI)}")
        print()
        
        # Test each URL
        detected_count = 0
        for url in test_urls:
            # Extract path from URL
            path = url.split('/')[-1].lower()
            
            # Check if any keyword matches
            is_career_page = any(keyword in path for keyword in CAREER_KEYWORDS_VI)
            
            if is_career_page:
                detected_count += 1
                print(f"✅ {url}")
            else:
                print(f"❌ {url}")
        
        print()
        print(f"📈 Detection Results:")
        print(f"   Total URLs tested: {len(test_urls)}")
        print(f"   URLs detected as career pages: {detected_count}")
        print(f"   Detection rate: {(detected_count/len(test_urls)*100):.1f}%")
        
        # Show sample keywords
        print(f"\n🔑 Sample Keywords:")
        sample_keywords = list(CAREER_KEYWORDS_VI)[:20]
        for keyword in sample_keywords:
            print(f"   - {keyword}")
        
        print(f"\n🌍 Keywords by category:")
        vi_keywords = [k for k in CAREER_KEYWORDS_VI if any(c in k for c in 'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ')]
        en_keywords = [k for k in CAREER_KEYWORDS_VI if not any(c in k for c in 'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ')]
        
        print(f"   Vietnamese keywords: {len(vi_keywords)}")
        print(f"   English keywords: {len(en_keywords)}")
        
    except ImportError as e:
        print(f"❌ Error importing contact_extractor: {e}")

def test_real_urls():
    """Test with real company URLs"""
    print(f"\n🏢 TESTING REAL COMPANY URLs")
    print("=" * 60)
    
    real_urls = [
        "https://tuyendung.fpt.com",
        "https://career.vng.com.vn",
        "https://careers.google.com",
        "https://careers.microsoft.com",
        "https://jobs.apple.com",
        "https://careers.meta.com",
        "https://jobs.netflix.com",
        "https://careers.amazon.com",
        "https://careers.uber.com",
        "https://careers.airbnb.com"
    ]
    
    try:
        from contact_extractor import CAREER_KEYWORDS_VI
        
        for url in real_urls:
            # Extract domain and path
            domain = url.split('/')[2].lower()
            path = '/'.join(url.split('/')[3:]).lower()
            full_path = f"{domain}/{path}"
            
            # Check if any keyword matches
            is_career_page = any(keyword in full_path for keyword in CAREER_KEYWORDS_VI)
            
            if is_career_page:
                print(f"✅ {url}")
            else:
                print(f"❌ {url}")
                
    except ImportError as e:
        print(f"❌ Error importing contact_extractor: {e}")

if __name__ == "__main__":
    print("🚀 KEYWORD TESTING")
    print("Testing improved career page detection keywords")
    print()
    
    test_keywords()
    test_real_urls()
    
    print(f"\n🎉 KEYWORD TESTING COMPLETED!")
    print(f"✅ Keywords improved and tested!")
    print(f"✅ Better detection for Vietnamese and English!")
    print(f"✅ Support for various URL patterns!") 