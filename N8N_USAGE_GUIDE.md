# N8N Usage Guide - Job Extraction

## 🎯 **Cập nhật endpoint `/crawl_and_extract_contact_info`**

Endpoint này giờ đây **tự động extract jobs** từ career pages mà nó tìm thấy!

## 📋 **Response mới bao gồm:**

### **Fields cũ (vẫn giữ nguyên):**
- `emails`: Danh sách email
- `social_links`: Danh sách social links  
- `career_pages`: Danh sách career pages
- `success`: Trạng thái thành công
- `crawl_time`: Thời gian crawl

### **Fields mới (thêm vào):**
- `jobs`: Danh sách các job cụ thể
- `total_jobs_found`: Tổng số job tìm được

## 💼 **Job Object Structure:**
```json
{
  "title": "Senior Frontend Developer",
  "company": "VNG Corporation", 
  "location": "Ho Chi Minh City",
  "url": "https://career.vng.com.vn/job/senior-frontend",
  "salary": "2000-4000 USD",
  "job_type": "Full-time",
  "description": "We are looking for a Senior Frontend Developer...",
  "source_url": "https://career.vng.com.vn/co-hoi-nghe-nghiep",
  "extracted_at": "2024-01-15 14:30:25"
}
```

## 🔧 **Cách sử dụng trong N8N:**

### **1. HTTP Request Node (không thay đổi):**
```json
{
  "method": "POST",
  "url": "https://crawler-ai.fly.dev/crawl_and_extract_contact_info",
  "body": {
    "url": "{{$json.website}}"
  }
}
```

### **2. Next Map Node - Process Jobs:**
```javascript
// Map jobs to individual items
return $input.all().map(item => {
  const jobs = item.json.jobs || [];
  
  if (jobs.length === 0) {
    return {
      company_name: item.json.company_name,
      website: item.json.requested_url,
      jobs_found: 0,
      message: "No jobs found"
    };
  }
  
  return jobs.map(job => ({
    company_name: item.json.company_name,
    website: item.json.requested_url,
    job_title: job.title,
    job_company: job.company,
    job_location: job.location,
    job_url: job.url,
    job_salary: job.salary,
    job_type: job.job_type,
    job_description: job.description,
    source_career_page: job.source_url,
    extracted_at: job.extracted_at
  }));
}).flat();
```

## 📊 **Workflow của bạn:**

```
Webhook → Read File → Extract from File → Get Next Map Batch (Supabase) → 
Edit Fields → Split Out → Include Map Company ID → 
Scrape Website (crawl_and_extract_contact_info) → 
Next Map (process jobs) → HTTP Request → Aggregate → HTTP Request
```

## 🧪 **Test URLs hiệu quả:**

### **Công ty Việt Nam:**
- `https://fpt.com.vn` - FPT Software
- `https://vng.com.vn` - VNG Corporation
- `https://tma.vn` - TMA Solutions
- `https://cmc.com.vn` - CMC Corporation

### **Job Boards:**
- `https://topcv.vn` - TopCV
- `https://careerbuilder.vn` - CareerBuilder
- `https://vietnamworks.com` - VietnamWorks

## ⚡ **Performance Notes:**

- **Job extraction** được thực hiện **tự động** sau khi tìm career pages
- **Giới hạn**: 10 jobs per career page để tránh timeout
- **Cache**: Kết quả được cache trong 1 giờ
- **Fallback**: Nếu job extraction fail, endpoint vẫn trả về career pages

## 🔍 **Debugging:**

### **Kiểm tra job extraction:**
```bash
curl -X POST "https://crawler-ai.fly.dev/crawl_and_extract_contact_info" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://fpt.com.vn"}'
```

### **Kiểm tra stats:**
```bash
curl "https://crawler-ai.fly.dev/stats"
```

## ✅ **Kết quả mong đợi:**

Sau khi cập nhật, workflow N8N của bạn sẽ:
- ✅ Tìm thấy career pages (như trước)
- ✅ **Tự động extract jobs** từ career pages
- ✅ Trả về job details trong field `jobs`
- ✅ Hoạt động với **Get Next Map Batch** (Supabase)
- ✅ Không cần thay đổi workflow hiện tại!

## 🚀 **Bắt đầu ngay:**

1. **Deploy** code đã cập nhật
2. **Test** với một URL công ty
3. **Kiểm tra** field `jobs` trong response
4. **Cập nhật** Next Map node để xử lý jobs
5. **Chạy** workflow và xem kết quả!

Bây giờ endpoint `/crawl_and_extract_contact_info` sẽ extract được **cả career pages VÀ jobs cụ thể**! 🎉 