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

### 2. Cấu hình node HTTP Request

#### Method: POST
#### Headers:
```
Content-Type: application/json
```

#### Body Parameters (Dựa trên dữ liệu thực tế):
```
Name: name
Value: {{ $json.Title }}

Name: domain
Value: {{ $json.Website }}

Name: phone
Value: {{ $json.Phone }}

Name: description
Value: {{ $json.Street }}

Name: social
Value: []

Name: career_page
Value: []

Name: crawl_data
Value: null
```

### 3. Mapping dữ liệu n8n:
Dữ liệu n8n có:
- `Title` → `name`
- `Website` → `domain` 
- `Phone` → `phone`
- `Street` → `description`
- `social` và `career_page` → mảng rỗng (vì chưa có dữ liệu)

### 4. Xử lý dữ liệu trả về

Endpoint mới trả về cấu trúc:
```json
{
  "company_name": "Intelligent Battery Analytics",
  "domain": "https://intelligentbatteryanalytics.com/",
  "phone": "+34 938 25 37 09",
  "description": "Carrer de Ramon Turró, 100",
  "social_links": [],
  "career_pages": [],
  "emails": [],
  "crawl_results": [...],
  "total_urls_processed": 1,
  "successful_crawls": 1
}
```

### 5. Lưu ý quan trọng

- **Endpoint mới** tự động xử lý cả trường hợp `social` và `career_page` là **mảng** hoặc **chuỗi**
- Nếu là chuỗi, API sẽ tự động split bằng dấu phẩy
- API sẽ crawl tất cả URL được cung cấp và trả về kết quả tổng hợp

### 6. Test endpoint

Bạn có thể test trước bằng curl:
```bash
curl -X POST https://crawler-ai.fly.dev/batch_crawl_and_extract \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Intelligent Battery Analytics",
    "domain": "https://intelligentbatteryanalytics.com/",
    "phone": "+34 938 25 37 09",
    "description": "Carrer de Ramon Turró, 100",
    "social": [],
    "career_page": [],
    "crawl_data": null
  }'
```

## Kết quả mong đợi
- ✅ Không còn lỗi "Expected array, received string"
- ✅ API crawl được nhiều URL cùng lúc
- ✅ Trả về dữ liệu tổng hợp từ tất cả URL
- ✅ Tương thích với workflow n8n hiện tại 