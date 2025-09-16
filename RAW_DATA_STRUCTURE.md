# Raw Crawl Data Structure

## Tổng quan
Trường `crawl_data` trong API response `/api/v1/detect_career_pages_scrapy` giờ đây chứa dữ liệu thô (raw data) đầy đủ từ quá trình crawl.

## Cấu trúc dữ liệu

### 1. HTML Content
```json
"html_content": "<!DOCTYPE html>..."
```
- **Mô tả**: Toàn bộ mã HTML gốc của trang web
- **Kích thước**: ~77,570 ký tự (FPT)
- **Mục đích**: Lưu trữ dữ liệu thô để phân tích sau

### 2. Text Content
```json
"text_content": "Tập đoàn FPT Về FPT Thông điệp Chủ tịch..."
```
- **Mô tả**: Nội dung văn bản được trích xuất từ HTML
- **Kích thước**: ~6,908 ký tự (FPT)
- **Mục đích**: Dễ dàng tìm kiếm và phân tích nội dung

### 3. Metadata
```json
"metadata": {
  "meta_tags": {...},
  "structured_data": [...],
  "og_tags": {...},
  "twitter_tags": {...},
  "title_tag": "...",
  "head_scripts": 36,
  "head_styles": 7,
  "images": 27,
  "links": 121
}
```

#### 3.1 Meta Tags
- **Mô tả**: Tất cả thẻ meta của trang web
- **Ví dụ**: description, viewport, keywords, author
- **Số lượng**: 9 tags (FPT)

#### 3.2 Structured Data
- **Mô tả**: Dữ liệu có cấu trúc (JSON-LD)
- **Ví dụ**: WebSite, Organization, BreadcrumbList
- **Số lượng**: 6 structured data (FPT)

#### 3.3 Open Graph Tags
- **Mô tả**: Thẻ meta cho social media sharing
- **Ví dụ**: og:title, og:description, og:image
- **Số lượng**: 4 tags (FPT)

#### 3.4 Twitter Cards
- **Mô tả**: Thẻ meta cho Twitter sharing
- **Ví dụ**: twitter:title, twitter:card
- **Số lượng**: 0 tags (FPT)

#### 3.5 Thống kê trang web
- **Scripts**: 36 JavaScript files
- **Styles**: 7 CSS files  
- **Images**: 27 hình ảnh
- **Links**: 121 liên kết

### 4. Raw Response
```json
"raw_response": {
  "status_code": 200,
  "final_url": "https://fpt.com",
  "crawl_time": 3.27,
  "crawl_method": "requests_optimized",
  "content_length": 77570,
  "text_length": 6908
}
```
- **Mô tả**: Thông tin response gốc từ HTTP request
- **Bao gồm**: Status code, URL cuối, thời gian crawl, phương pháp

### 5. Processed Data (Backward Compatibility)
```json
"title": "Tập đoàn FPT",
"description": "FPT là một trong những công ty...",
"emails": [],
"phones": ["91936967046"],
"urls": ["https://fpt.com/en", ...]
```
- **Mô tả**: Dữ liệu đã được xử lý (tương thích ngược)
- **Bao gồm**: Title, description, emails, phones, URLs

## Lợi ích

### 1. Dữ liệu thô đầy đủ
- Lưu trữ toàn bộ HTML gốc
- Không mất thông tin trong quá trình xử lý
- Có thể phân tích lại sau này

### 2. Metadata chi tiết
- Tất cả meta tags quan trọng
- Structured data cho SEO
- Open Graph cho social media
- Thống kê trang web

### 3. Debugging và Analytics
- Thời gian crawl chi tiết
- Phương pháp crawl được sử dụng
- Kích thước nội dung
- Status code và URL cuối

### 4. Tương thích ngược
- Vẫn có dữ liệu đã xử lý
- Không ảnh hưởng đến code hiện tại
- Dễ dàng migrate

## Sử dụng

### 1. Phân tích nội dung
```python
# Lấy HTML thô
html_content = response['crawl_data']['html_content']

# Lấy text đã xử lý
text_content = response['crawl_data']['text_content']

# Lấy metadata
metadata = response['crawl_data']['metadata']
```

### 2. SEO Analysis
```python
# Meta tags
meta_tags = response['crawl_data']['metadata']['meta_tags']

# Structured data
structured_data = response['crawl_data']['metadata']['structured_data']

# Open Graph
og_tags = response['crawl_data']['metadata']['og_tags']
```

### 3. Performance Analysis
```python
# Thời gian crawl
crawl_time = response['crawl_data']['raw_response']['crawl_time']

# Kích thước nội dung
content_length = response['crawl_data']['raw_response']['content_length']
```

## Kết luận
Trường `crawl_data` mới cung cấp dữ liệu thô đầy đủ và chi tiết, giúp:
- Phân tích sâu hơn về trang web
- Debug và tối ưu hóa crawler
- Lưu trữ dữ liệu gốc để sử dụng sau
- Tương thích với code hiện tại
