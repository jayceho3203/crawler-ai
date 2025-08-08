# Crawler Performance Optimization

## Vấn đề ban đầu
- Thời gian crawl quá lâu: 228.20s cho một URL
- Timeout 10000ms exceeded cho dynamic content
- Quá nhiều xử lý không cần thiết

## Các tối ưu đã thực hiện

### 1. Tối ưu Timeout và Wait Times
- **DEFAULT_TIMEOUT**: Tăng từ 30s lên 60s
- **OPTIMIZED_TIMEOUT**: Giảm từ 30s xuống 15s cho navigation
- **PAGE_WAIT_TIMEOUT**: Giảm từ 500ms xuống 200ms
- **Dynamic content wait**: Giảm từ 3000ms xuống 1000ms

### 2. Tối ưu Browser Settings
```python
# Tắt các tính năng không cần thiết
'--disable-javascript',  # Tắt JS nếu không cần
'--disable-images',      # Tắt images
'--disable-css',         # Tắt CSS
'--disable-extensions',  # Tắt extensions
'--disable-plugins',     # Tắt plugins
```

### 3. Tối ưu Resource Blocking
```python
# Block thêm resources
await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,css,js,ico}", lambda route: route.abort())
```

### 4. Giới hạn Data Processing
- **URLs**: Giới hạn 100 URLs thay vì tất cả
- **Career URLs**: Chỉ dùng 5 selectors đầu, giới hạn 10 elements
- **Jobs**: Giới hạn 50 jobs thay vì tất cả
- **Hidden jobs**: Giới hạn 5 jobs mỗi technique
- **Pagination**: Giảm từ 10 pages xuống 3 pages

### 5. Tối ưu Hidden Job Extraction
- Giảm từ 10 techniques xuống 4 techniques chính
- Giới hạn thời gian chờ cho mỗi technique
- Chỉ extract jobs khi cần thiết (có career URLs hoặc job links)

### 6. Tối ưu Selectors
- Giảm số lượng selectors sử dụng
- Chỉ dùng các selectors quan trọng nhất
- Giới hạn số lượng elements xử lý

## Kết quả mong đợi

### Trước khi tối ưu:
- Thời gian crawl: 228.20s
- Timeout: 10s
- Memory usage: Cao
- CPU usage: Cao

### Sau khi tối ưu:
- Thời gian crawl: ~30-60s (giảm 60-75%)
- Timeout: 15s
- Memory usage: Giảm 40-50%
- CPU usage: Giảm 30-40%

## Cách test performance

```bash
# Chạy test script
python test_crawler_performance.py
```

## Monitoring

### Logs quan trọng:
- `🌐 Playwright navigating to: {url}`
- `✅ Playwright crawl completed: {url} - {time}s`
- `📊 Career URLs: {raw} raw -> {filtered} filtered`
- `📊 Job Links: {detected} detected -> {filtered} filtered`

### Metrics cần theo dõi:
1. **Crawl time**: Mục tiêu < 60s
2. **Success rate**: Mục tiêu > 90%
3. **Memory usage**: Mục tiêu < 500MB
4. **CPU usage**: Mục tiêu < 50%

## Troubleshooting

### Nếu vẫn chậm:
1. Kiểm tra network connection
2. Giảm thêm số lượng selectors
3. Tăng timeout nếu cần
4. Kiểm tra website có rate limiting không

### Nếu có lỗi:
1. Kiểm tra logs chi tiết
2. Thử với requests fallback
3. Kiểm tra website có anti-bot protection không
