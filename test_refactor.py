#!/usr/bin/env python3
"""
Simple test to check if the refactored structure works
"""

def test_imports():
    """Test if all modules can be imported"""
    try:
        # Test basic imports
        from app import __version__
        print(f"✅ App package imported: {__version__}")
        
        # Test models
        from app.models.schemas import CrawlRequest, CrawlResponse
        print("✅ Models imported successfully")
        
        # Test utils
        from app.utils.constants import CAREER_KEYWORDS_VI, JOB_BOARD_DOMAINS
        print(f"✅ Constants imported: {len(CAREER_KEYWORDS_VI)} keywords, {len(JOB_BOARD_DOMAINS)} job boards")
        
        # Test services (without playwright)
        from app.services.cache import get_cached_result, cache_result
        print("✅ Cache service imported successfully")
        
        from app.services.career_detector import is_job_board_url
        print("✅ Career detector imported successfully")
        
        # Test API structure
        from app.api.routes import router
        print("✅ API routes imported successfully")
        
        print("\n🎉 All imports successful! Refactor is working.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without external dependencies"""
    try:
        # Test career detector
        from app.services.career_detector import is_job_board_url
        
        # Test job board detection
        assert is_job_board_url("https://topcv.vn") == True
        assert is_job_board_url("https://example.com") == False
        print("✅ Career detector working")
        
        # Test cache
        from app.services.cache import cache_result, get_cached_result
        
        test_data = {"test": "data"}
        cache_result("https://test.com", test_data)
        cached = get_cached_result("https://test.com")
        assert cached == test_data
        print("✅ Cache working")
        
        print("🎉 Basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing refactored structure...")
    
    imports_ok = test_imports()
    if imports_ok:
        functionality_ok = test_basic_functionality()
        if functionality_ok:
            print("\n🎉 All tests passed! Refactor successful!")
        else:
            print("\n⚠️ Import tests passed but functionality tests failed")
    else:
        print("\n❌ Import tests failed") 