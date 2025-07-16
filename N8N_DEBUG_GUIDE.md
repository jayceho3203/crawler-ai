# Hướng dẫn Debug n8n Workflow

## Vấn đề hiện tại
API nhận request nhưng không có dữ liệu:
- Company name: None
- URLs to crawl: 0
- Results: 0 emails, 0 social, 0 career

## Cách debug

### 1. Thêm node Code để log dữ liệu
Thêm node **Code** trước node "Scrape website1":

```javascript
// Log dữ liệu đầu vào
console.log("=== INPUT DATA ===");
console.log("Name:", $json.name);
console.log("Domain:", $json.domain);
console.log("Social:", $json.social);
console.log("Career page:", $json.career_page);
console.log("Phone:", $json.phone);
console.log("Description:", $json.description);
console.log("Data raw:", $json.data_raw);

// Trả về dữ liệu gốc
return $json;
```

### 2. Kiểm tra cấu hình HTTP Request
Trong node "Scrape website1":

**Method:** POST
**URL:** `https://crawler-ai.fly.dev/batch_crawl_and_extract`
**Body Content Type:** JSON
**Body Parameters:**
```
Name: name
Value: {{ $json.name }}

Name: domain
Value: {{ $json.domain }}

Name: social
Value: {{ $json.social || [] }}

Name: career_page
Value: {{ $json.career_page || [] }}

Name: phone
Value: {{ $json.phone }}

Name: description
Value: {{ $json.description }}

Name: crawl_data
Value: {{ $json.data_raw || "" }}
```

### 3. Kiểm tra dữ liệu từ node trước
Xem node trước "Scrape website1" có trả về dữ liệu đúng không:
- Có trường `name` không?
- Có trường `social` không?
- Có trường `career_page` không?

### 4. Test với dữ liệu mẫu
Thay thế tạm thời bằng dữ liệu cố định:
```javascript
return {
  name: "Test Company",
  domain: "example.com",
  social: ["https://facebook.com/test"],
  career_page: ["https://example.com/careers"],
  phone: "+1234567890",
  description: "Test description"
};
```

## Kết quả mong đợi
Sau khi debug, bạn sẽ thấy:
- Dữ liệu đầy đủ trong log
- API nhận được URLs để crawl
- Kết quả crawl thành công 