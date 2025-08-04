# Crawler AI API

A powerful web scraping and job extraction API built with FastAPI, designed to extract career pages, job listings, and contact information from company websites.

## 🚀 Live Demo

**API Base URL:** https://crawler-ai.onrender.com

**Interactive Documentation:** https://crawler-ai.onrender.com/docs

## ✨ Features

### 🔍 Career Page Detection
- **Enhanced filtering** with strict validation rules
- **Multi-dimensional analysis** for accurate career page identification
- **Early rejection** of non-career pages
- **Subdomain search** capabilities

### 💼 Job Extraction
- **Hidden job detection** using 10 different techniques
- **Dynamic content crawling** with Playwright
- **Job quality scoring** and filtering
- **Simplified output format** for end-users

### 📞 Contact Information Extraction
- **Email addresses** and phone numbers
- **Social media links**
- **Contact page detection**
- **Structured contact data**

### 🎯 Advanced Job Finding
- **Comprehensive job analysis**
- **Role classification**
- **Location detection**
- **Job type identification**

## 📋 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/detect_career_pages` | POST | Detect career pages from company websites |
| `/api/v1/extract_jobs` | POST | Extract job listings from career pages |
| `/api/v1/extract_contact_info` | POST | Extract contact information from websites |
| `/api/v1/find_jobs_advanced` | POST | Advanced job finding with comprehensive analysis |
| `/api/v1/crawl_and_extract_contact_info` | POST | All-in-one crawling and extraction (backward compatible) |
| `/api/v1/batch_crawl_and_extract` | POST | Batch processing for multiple URLs |

### Utility Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint with API info |
| `/health` | GET | Health check endpoint |
| `/api/v1/stats` | GET | Get crawling statistics |
| `/api/v1/clear_cache` | GET | Clear application cache |

## 🔧 Request Format

### Basic Request
```json
{
  "url": "https://example.com"
}
```

### Advanced Request (Career Page Detection)
```json
{
  "url": "https://example.com",
  "include_subdomain_search": true,
  "max_pages_to_scan": 50,
  "strict_filtering": true,
  "include_job_boards": false
}
```

## 📊 Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    "career_pages": [...],
    "jobs": [...],
    "contacts": {...},
    "formatted_jobs": [...],
    "job_summary": {...}
  },
  "message": "Success"
}
```

### Job Data Structure
```json
{
  "title": "Software Engineer",
  "job_link": "https://example.com/jobs/123",
  "company": "Example Corp",
  "location": "Ho Chi Minh City",
  "type": "Full-time"
}
```

## 🛠️ Technology Stack

- **Framework:** FastAPI
- **Web Scraping:** Playwright, BeautifulSoup4
- **HTTP Client:** Requests
- **Data Validation:** Pydantic
- **Deployment:** Render

## 🚀 Deployment

### Environment Variables
```bash
PLAYWRIGHT_BROWSERS_PATH=/opt/render/project/src/.cache/ms-playwright
PYTHONUNBUFFERED=1
```

### Build Commands
```bash
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

### Start Command
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## 📦 Dependencies

```
fastapi==0.111.0
uvicorn==0.32.0
requests==2.32.3
beautifulsoup4==4.12.3
pydantic>=2.7.0
playwright
```

## 🔄 n8n Integration

### Node Mapping for n8n Workflow

| n8n Node | API Endpoint | Purpose |
|----------|-------------|---------|
| Scrape website1 | `/api/v1/detect_career_pages` | Detect career pages from company domains |
| Scrape website2 | `/api/v1/detect_career_pages` | Validate and process known career URLs |
| Scrape website3 | `/api/v1/extract_jobs` | Extract jobs from career pages |
| Scrape website | `/api/v1/extract_contact_info` | Extract contact information |
| HTTP Request4 | `/api/v1/find_jobs_advanced` | Advanced job analysis |

### n8n Configuration
- **Base URL:** `https://crawler-ai.onrender.com`
- **Method:** POST
- **Headers:** `Content-Type: application/json`
- **Body:** `{"url": "{{$json.url}}"}`

## 🎯 Use Cases

1. **Company Research:** Extract career pages and job listings from company websites
2. **Job Market Analysis:** Collect job data for market research
3. **Contact Database:** Build contact information databases
4. **Recruitment:** Automate job posting discovery
5. **Competitive Analysis:** Monitor competitor job postings

## 🔒 Features

- **Rate limiting** and request validation
- **Error handling** with detailed error messages
- **Caching** for improved performance
- **Structured output** for easy integration
- **Comprehensive logging** for debugging

## 📈 Performance

- **Fast response times** with optimized scraping
- **Concurrent processing** capabilities
- **Memory efficient** data handling
- **Scalable architecture** for high load

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the [API Documentation](https://crawler-ai.onrender.com/docs)
- Review the [Swagger UI](https://crawler-ai.onrender.com/docs)
- Open an issue on GitHub

---

**Version:** 2.0.0  
**Status:** Production Ready  
**Last Updated:** August 2024
