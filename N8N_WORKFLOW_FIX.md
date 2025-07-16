# Hướng dẫn sửa lỗi n8n Workflow

## Vấn đề hiện tại
Lỗi **"Expected array, received string"** cho trường `career_page` trong node HTTP Request của n8n.

## Nguyên nhân
- API endpoint cũ (`/crawl_and_extract_contact_info`) chỉ nhận **một URL duy nhất**
- n8n đang cố gắng gửi **nhiều URL** (social, career pages) như parameters
- Trường `career_page` được truyền dưới dạng **chuỗi** thay vì **mảng**

## Giải pháp

### 1. Sử dụng endpoint mới
Thay đổi URL trong node HTTP Request từ:
```
https://crawler-ai.fly.dev/crawl_and_extract_contact_info
```
Thành:
```
https://crawler-ai.fly.dev/batch_crawl_and_extract
```

### 2. Cập nhật cấu hình node HTTP Request

#### Method: POST
#### Headers:
```
Content-Type: application/json
```

#### Body Parameters:
```
Name: name
Value: {{ $json.name }}

Name: domain  
Value: {{ $json.domain }}

Name: phone
Value: {{ $json.phone }}

Name: description
Value: {{ $json.description }}

Name: social
Value: {{ $json.social || [] }}

Name: career_page
Value: {{ $json.career_page || [] }}

Name: crawl_data
Value: {{ $json.data_raw || "" }}
```

### 3. Xử lý dữ liệu trả về

Endpoint mới trả về cấu trúc:
```json
{
  "company_name": "OpenCommerce Group",
  "domain": "www.opencommercegroup.com", 
  "social_links": ["url1", "url2"],
  "career_pages": ["url1", "url2"],
  "emails": ["email1", "email2"],
  "crawl_results": [...],
  "total_urls_processed": 5,
  "successful_crawls": 4
}
```

### 4. Lưu ý quan trọng

- **Endpoint mới** tự động xử lý cả trường hợp `social` và `career_page` là **mảng** hoặc **chuỗi**
- Nếu là chuỗi, API sẽ tự động split bằng dấu phẩy
- API sẽ crawl tất cả URL được cung cấp và trả về kết quả tổng hợp

### 5. Test endpoint

Bạn có thể test trước bằng curl:
```bash
curl -X POST https://crawler-ai.fly.dev/batch_crawl_and_extract \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenCommerce Group",
    "domain": "www.opencommercegroup.com",
    "social": ["https://www.facebook.com/OCGCareers"],
    "career_page": ["https://www.opencommercegroup.com/careers"]
  }'
```

## Kết quả mong đợi
- ✅ Không còn lỗi "Expected array, received string"
- ✅ API crawl được nhiều URL cùng lúc
- ✅ Trả về dữ liệu tổng hợp từ tất cả URL
- ✅ Tương thích với workflow n8n hiện tại 