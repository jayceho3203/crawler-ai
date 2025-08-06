import requests
import json

# API endpoint
url = "https://crawler-ai.onrender.com/extract_job_details"

# Job URL cần extract
job_url = "https://www.ics-p.vn/vi/career/C-Sharp-DotNet-Senior-Developer-vn.html"

# Request payload
payload = {
    "url": job_url
}

# Headers
headers = {
    "Content-Type": "application/json"
}

try:
    print("🚀 Đang extract job details...")
    print(f"📄 Job URL: {job_url}")
    print("-" * 50)
    
    # Gửi request
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get('success'):
            job_details = result.get('job_details', {})
            
            print("✅ Extract thành công!")
            print(f"⏱️  Thời gian: {result.get('crawl_time', 0):.2f}s")
            print(f"🔧 Method: {result.get('crawl_method', 'unknown')}")
            print("-" * 50)
            
            # Hiển thị 5 trường chính cho Wehappi
            print("📋 JOB DETAILS (Wehappi Fields):")
            print(f"🎯 Job Name: {job_details.get('title', 'N/A')}")
            print(f"📝 Job Type: {job_details.get('job_type', 'N/A')}")
            print(f"👤 Job Role: {job_details.get('job_role', 'N/A')}")
            print(f"📄 Job Description: {job_details.get('description', 'N/A')[:200]}...")
            print(f"🔗 Job Link: {job_details.get('url', 'N/A')}")
            
            # Lưu kết quả vào file
            with open('job_details_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("-" * 50)
            print("💾 Đã lưu kết quả vào: job_details_result.json")
            
        else:
            print("❌ Extract thất bại!")
            print(f"Error: {result.get('error_message', 'Unknown error')}")
            
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {str(e)}") 