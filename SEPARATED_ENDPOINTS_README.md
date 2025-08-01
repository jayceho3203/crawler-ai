# Separated Endpoints - Enhanced Crawler API

## 🎯 Overview

Đã tách endpoint `crawl_and_extract_contact_info` thành **3 endpoint riêng biệt** với các tính năng nâng cao:

1. **`/extract_contact_info`** - Contact extraction với deep crawl
2. **`/detect_career_pages`** - Career page detection với subdomain search
3. **`/extract_jobs`** - Job extraction với advanced filtering

## 📋 API Endpoints

### 1. Contact Information Extraction

**Endpoint:** `POST /api/v1/extract_contact_info`

**Request:**
```json
{
  "url": "https://example.com",
  "include_social": true,
  "include_emails": true,
  "include_phones": true,
  "max_depth": 2,
  "timeout": 30
}
```

**Response:**
```json
{
  "success": true,
  "requested_url": "https://example.com",
  "crawl_time": 5.23,
  "crawl_method": "playwright",
  "emails": ["contact@example.com", "hr@example.com"],
  "phones": ["+84123456789", "0123456789"],
  "social_links": ["https://facebook.com/example", "https://linkedin.com/company/example"],
  "contact_forms": ["https://example.com/contact", "https://example.com/about"],
  "total_pages_crawled": 3,
  "total_links_found": 45
}
```

**Enhanced Features:**
- ✅ Deep crawl contact pages (max_depth)
- ✅ Phone number extraction (Vietnamese, US, UK, Japan)
- ✅ Enhanced social media detection
- ✅ Contact form detection
- ✅ Statistics and performance metrics

### 2. Career Page Detection

**Endpoint:** `POST /api/v1/detect_career_pages`

**Request:**
```json
{
  "url": "https://example.com",
  "include_subdomain_search": true,
  "max_pages_to_scan": 50,
  "strict_filtering": true,
  "include_job_boards": false
}
```

**Response:**
```json
{
  "success": true,
  "requested_url": "https://example.com",
  "crawl_time": 8.45,
  "career_pages": ["https://example.com/career", "https://career.example.com"],
  "potential_career_pages": ["https://example.com/jobs"],
  "rejected_urls": [
    {"url": "https://example.com/services", "reason": "Non-career pattern: /services"}
  ],
  "career_page_analysis": [
    {
      "url": "https://example.com/career",
      "is_career_page": true,
      "confidence": 0.8,
      "indicators": ["Path contains 'career'", "Career pattern: /career"]
    }
  ],
  "total_urls_scanned": 45,
  "valid_career_pages": 2,
  "confidence_score": 0.75
}
```

**Enhanced Features:**
- ✅ Subdomain search (career.example.com, jobs.example.com)
- ✅ Job board integration
- ✅ Detailed URL analysis with confidence scoring
- ✅ Strict filtering with rejection reasons
- ✅ Comprehensive statistics

### 3. Job Extraction

**Endpoint:** `POST /api/v1/extract_jobs`

**Request:**
```json
{
  "career_page_urls": ["https://example.com/career"],
  "max_jobs_per_page": 50,
  "include_hidden_jobs": true,
  "include_job_details": true,
  "job_types_filter": ["full-time", "part-time"],
  "location_filter": ["hanoi", "ho_chi_minh"],
  "salary_range": {"min": 10000000, "max": 50000000},
  "posted_date_filter": "last_month"
}
```

**Response:**
```json
{
  "success": true,
  "requested_urls": ["https://example.com/career"],
  "crawl_time": 12.34,
  "total_jobs_found": 15,
  "jobs": [
    {
      "title": "Senior Developer",
      "company": "Example Corp",
      "location": "Hanoi",
      "job_type": "full-time",
      "salary": "25,000,000 VND",
      "posted_date": "2024-01-15",
      "job_link": "https://example.com/career/senior-developer",
      "description": "We are looking for a senior developer..."
    }
  ],
  "formatted_jobs": {
    "jobs": [...],
    "total_count": 15
  },
  "job_summary": {
    "total_jobs": 15,
    "job_types": {"full-time": 10, "part-time": 5},
    "locations": {"Hanoi": 8, "Ho Chi Minh": 7}
  },
  "hidden_jobs_count": 5,
  "visible_jobs_count": 10,
  "page_results": [...]
}
```

**Enhanced Features:**
- ✅ Hidden job extraction (JavaScript, APIs, modals)
- ✅ Advanced filtering (job type, location, salary, date)
- ✅ Job deduplication
- ✅ Enhanced job details extraction
- ✅ Per-page results and statistics

## 🔄 Complete Workflow

**Step-by-step workflow using separated endpoints:**

```python
# 1. Extract contact info
contact_result = await contact_service.extract_contact_info(url)

# 2. Detect career pages
career_result = await career_pages_service.detect_career_pages(url)

# 3. Extract jobs from career pages
if career_result['career_pages']:
    job_result = await job_extraction_service.extract_jobs(
        career_result['career_pages']
    )
```

## 🚀 Benefits

### Performance
- **Faster response times** - Each endpoint focuses on one task
- **Parallel processing** - Can run endpoints concurrently
- **Resource optimization** - Only load required services

### Flexibility
- **Selective extraction** - Choose what to extract
- **Custom filtering** - Advanced job filtering options
- **Configurable depth** - Control crawl depth and scope

### Maintainability
- **Modular design** - Each service is independent
- **Easy testing** - Test each component separately
- **Clear separation** - Contact, career, job logic separated

### Enhanced Capabilities
- **Better contact extraction** - Deep crawl, phone detection
- **Smarter career detection** - Subdomain search, confidence scoring
- **Advanced job filtering** - Multiple filter types, hidden job extraction

## 📊 Comparison

| Feature | Original Endpoint | Separated Endpoints |
|---------|------------------|-------------------|
| Response Time | 15-30s | 5-10s each |
| Memory Usage | High | Optimized |
| Error Handling | Basic | Detailed |
| Filtering | Limited | Advanced |
| Statistics | Basic | Comprehensive |
| Flexibility | Low | High |

## 🔧 Usage Examples

### Basic Contact Extraction
```bash
curl -X POST "https://crawler-ai.fly.dev/api/v1/extract_contact_info" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Career Page Detection with Subdomain Search
```bash
curl -X POST "https://crawler-ai.fly.dev/api/v1/detect_career_pages" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "include_subdomain_search": true,
    "strict_filtering": true
  }'
```

### Job Extraction with Filters
```bash
curl -X POST "https://crawler-ai.fly.dev/api/v1/extract_jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "career_page_urls": ["https://example.com/career"],
    "job_types_filter": ["full-time"],
    "location_filter": ["hanoi"],
    "include_hidden_jobs": true
  }'
```

## 🔄 Backward Compatibility

Endpoint gốc `/crawl_and_extract_contact_info` vẫn được giữ lại để đảm bảo tương thích với n8n workflow hiện tại.

## 🧪 Testing

Chạy test script để kiểm tra các endpoint mới:

```bash
python test_separated_endpoints.py
```

## 📈 Performance Tips

1. **Use specific endpoints** - Chỉ gọi endpoint cần thiết
2. **Configure filters** - Sử dụng filters để giảm thời gian xử lý
3. **Limit depth** - Điều chỉnh max_depth phù hợp
4. **Parallel requests** - Gọi các endpoint song song khi có thể 