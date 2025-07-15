# Hướng dẫn sử dụng Workflow n8n Crawler AI

## 📋 Tổng quan

Workflow này tự động hóa quá trình crawl và phân tích dữ liệu công ty từ Google Maps và website của họ.

## 🔧 Cải thiện đã thực hiện

### ✅ URL API đã được cập nhật
- **Trước:** `http://host.docker.internal:8000/crawl_and_extract_contact_info`
- **Sau:** `https://crawler-ai-1.onrender.com/crawl_and_extract_contact_info`

### ✅ Timeout được thêm vào
- **Scrape website:** 30 giây
- **Google Maps Scraper:** 60 giây  
- **Get next map batch:** 30 giây
- **HTTP Request2:** 30 giây

### ✅ Validation được thêm vào
- Kiểm tra website có hợp lệ trước khi crawl
- Tránh crawl các website rỗng hoặc null
- Xử lý trường hợp dữ liệu null/empty
- Thêm fallback values cho các trường bắt buộc

## 🚀 Cách sử dụng

### 1. Import workflow vào n8n
1. Mở n8n dashboard
2. Vào **Workflows** → **Import from file**
3. Chọn file `map-crawl-huan.json`

### 2. Cấu hình credentials
Đảm bảo các credentials sau đã được cấu hình:
- **Google Gemini API** (cho AI Agent)
- **OpenAI API** (backup cho AI)
- **Supabase** (cho database)

### 3. Trigger workflow
Có 3 cách để trigger:

#### A. Webhook1 - Crawl webpage
```
POST https://your-n8n-instance.com/webhook/7782568b-dfe1-441b-96a7-0fc59ebbb7ba
```

#### B. Webhook - Google Maps scraping
```
POST https://your-n8n-instance.com/webhook/7782568b-dfe1-441b-96a7-0fc59ebbb7ba
```

#### C. Start workflow - Toàn bộ quy trình
```
POST https://your-n8n-instance.com/webhook/7782568b-dfe1-441b-96a7-0fc59ebbb7ba
```

## 📊 Luồng hoạt động

1. **Trigger** → Nhận yêu cầu từ webhook
2. **Read File** → Đọc cấu hình từ file
3. **Get Cities** → Lấy danh sách thành phố chưa xử lý
4. **Google Maps Scraper** → Tìm công ty trong thành phố
5. **Save Companies** → Lưu công ty vào database
6. **Get Batch** → Lấy batch công ty cần crawl
7. **Validate Website** → Kiểm tra website hợp lệ
8. **Scrape Website** → Gọi API crawl của bạn
9. **AI Analysis** → Phân tích dữ liệu bằng AI
10. **Save Results** → Lưu kết quả vào database

## 🔍 Monitoring

### Kiểm tra logs
- Theo dõi execution logs trong n8n
- Kiểm tra response từ API crawl
- Xem kết quả trong Supabase database

### Metrics quan trọng
- Số lượng công ty đã crawl
- Tỷ lệ thành công/thất bại
- Thời gian xử lý trung bình

## ⚠️ Troubleshooting

### Lỗi timeout
- Tăng timeout trong node settings
- Kiểm tra kết nối mạng
- Đảm bảo API Render.com hoạt động

### Lỗi website không crawl được
- Kiểm tra website có hợp lệ không
- Xem logs của API crawl
- Thử crawl thủ công để debug

### Lỗi dữ liệu null/empty
- Workflow đã được cập nhật để xử lý null values
- Các trường bắt buộc sẽ có fallback values
- AI Agent sẽ xử lý dữ liệu thiếu một cách an toàn

### Lỗi database
- Kiểm tra Supabase credentials
- Xem RPC functions có hoạt động không
- Kiểm tra schema database

## 📈 Tối ưu hóa

### Performance
- Tăng batch size nếu cần
- Thêm delay giữa các requests
- Sử dụng parallel processing

### Error Handling
- Thêm retry logic
- Log chi tiết lỗi
- Alert khi có lỗi nghiêm trọng

## 🔐 Security

- Không commit credentials vào git
- Sử dụng environment variables
- Rotate API keys định kỳ

## 📞 Support

Nếu gặp vấn đề:
1. Kiểm tra logs trong n8n
2. Test API crawl trực tiếp
3. Xem database schema
4. Liên hệ support team 