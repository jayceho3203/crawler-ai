# Career Page Extraction Fix for N8N

## Vấn đề đã được khắc phục

### 🔧 **Vấn đề chính**
Endpoint `/crawl_and_extract_contact_info` không tìm thấy job pages của các công ty Việt Nam vì:
- Chỉ sử dụng từ khóa tiếng Anh
- Thiếu từ khóa tiếng Việt phổ biến
- Logic phát hiện career pages chưa tối ưu

### ✅ **Giải pháp đã áp dụng**

#### 1. **Thêm từ khóa tiếng Việt**
Trong `contact_extractor.py`, đã thêm `CAREER_KEYWORDS_VI`:
```python
CAREER_KEYWORDS_VI = {
    # Vietnamese keywords
    'tuyen-dung', 'tuyển-dụng', 'viec-lam', 'việc-làm',
    'co-hoi', 'cơ-hội', 'nhan-vien', 'nhân-viên',
    'ung-vien', 'ứng-viên', 'cong-viec', 'công-việc',
    'lam-viec', 'làm-việc', 'moi', 'mời',
    'thu-viec', 'thử-việc', 'chinh-thuc', 'chính-thức',
    
    # English keywords (mở rộng)
    'developer', 'dev', 'programmer', 'engineer',
    'software', 'tech', 'technology', 'it',
    'career', 'job', 'recruitment', 'employment',
    'work', 'position', 'opportunity', 'vacancy',
    'apply', 'application', 'hiring', 'join-us',
    'team', 'talent', 'careers', 'jobs',
    'open-role', 'open-roles', 'we-are-hiring',
    'work-with-us', 'join-our-team', 'grow-with-us',
    'full-time', 'part-time', 'remote', 'hybrid',
    'internship', 'intern', 'graduate', 'entry-level',
    'senior', 'junior', 'lead', 'principal',
    'frontend', 'backend', 'fullstack', 'mobile', 'web',
    'data', 'ai', 'ml', 'machine-learning',
    'devops', 'qa', 'test', 'testing',
    'ui', 'ux', 'design', 'product'
}
```

#### 2. **Cập nhật logic phát hiện**
Hàm `process_extracted_crawl_results` giờ sử dụng cả từ khóa tiếng Anh và tiếng Việt:
```python
# Check both English and Vietnamese keywords
all_career_keywords = CAREER_KEYWORDS.union(CAREER_KEYWORDS_VI)
```

#### 3. **Cải thiện career path segments**
Thêm các path segments tiếng Việt:
```python
career_path_segments = [
    "career", "jobs", "hiring", "vacancy", "vacancies", 
    "tuyen-dung", "tuyển-dụng", "viec-lam", "việc-làm", 
    "co-hoi", "cơ-hội", "nhan-vien", "nhân-viên",
    "ung-vien", "ứng-viên", "cong-viec", "công-việc",
    "lam-viec", "làm-việc", "moi", "mời", 
    "thu-viec", "thử-việc"
]
```

## Cách sử dụng với N8N

### 1. **HTTP Request Node - Crawl and Extract**
```json
{
  "method": "POST",
  "url": "http://localhost:8000/crawl_and_extract_contact_info",
  "body": {
    "url": "{{$json.company_website}}"
  }
}
```

### 2. **Expected Response**
```json
{
  "requested_url": "https://fpt.com.vn",
  "success": true,
  "emails": ["hr@fpt.com.vn", "career@fpt.com.vn"],
  "social_links": ["https://linkedin.com/company/fpt-software"],
  "career_pages": [
    "https://careers.fpt.com.vn",
    "https://fpt.com.vn/tuyen-dung",
    "https://fpt.com.vn/careers"
  ],
  "crawl_method": "playwright",
  "crawl_time": 2.45
}
```

### 3. **Next Map Node - Process Results**
```javascript
// Map career pages to individual items
return $input.all().map(item => {
  const careerPages = item.json.career_pages || [];
  
  return careerPages.map(careerUrl => ({
    company_name: item.json.company_name,
    career_url: careerUrl,
    source_url: item.json.requested_url,
    extracted_at: new Date().toISOString()
  }));
}).flat();
```

## Test Script

Chạy test để kiểm tra:
```bash
python test_crawl_endpoint.py
```

## Các URL test hiệu quả

### Công ty Việt Nam
- `https://fpt.com.vn` - FPT Software
- `https://vng.com.vn` - VNG Corporation  
- `https://tma.vn` - TMA Solutions
- `https://cmc.com.vn` - CMC Corporation
- `https://viettel.com.vn` - Viettel

### Job Boards
- `https://topcv.vn` - TopCV
- `https://careerbuilder.vn` - CareerBuilder
- `https://vietnamworks.com` - VietnamWorks

## Troubleshooting

### Nếu vẫn không tìm thấy career pages:

1. **Kiểm tra URL có đúng không**
   ```bash
   curl -X POST "http://localhost:8000/crawl_and_extract_contact_info" \
     -H "Content-Type: application/json" \
     -d '{"url": "YOUR_URL_HERE"}'
   ```

2. **Kiểm tra logs**
   - Xem log để biết quá trình crawl
   - Kiểm tra có lỗi JavaScript không

3. **Clear cache nếu cần**
   ```bash
   curl "http://localhost:8000/clear_cache"
   ```

4. **Kiểm tra stats**
   ```bash
   curl "http://localhost:8000/stats"
   ```

## Kết quả mong đợi

Sau khi fix, endpoint `/crawl_and_extract_contact_info` sẽ:
- ✅ Tìm thấy career pages tiếng Việt
- ✅ Tìm thấy career pages tiếng Anh  
- ✅ Hoạt động tốt với N8N workflow
- ✅ Trả về format JSON chuẩn cho Next Map 