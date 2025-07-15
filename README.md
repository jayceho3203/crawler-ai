# Crawler AI - FastAPI Service

A FastAPI service for crawling websites and extracting contact information using Playwright.

## 🚀 Quick Deploy to Fly.io

### Prerequisites
- [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) installed
- Fly.io account

### Deploy Steps

1. **Login to Fly.io**
```bash
fly auth login
```

2. **Deploy the app**
```bash
fly launch
fly deploy
```

3. **Set environment variables**
```bash
fly secrets set APIFY_RUN_URL="your_apify_url"
```

4. **Check status**
```bash
fly status
fly logs
```

## 📡 API Endpoints

### POST `/crawl_and_extract_contact_info`
Crawl a website and extract contact information.

**Request:**
```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "requested_url": "https://example.com",
  "success": true,
  "emails": ["contact@example.com"],
  "social_links": ["https://linkedin.com/company/example"],
  "career_pages": ["https://example.com/careers"],
  "fit_markdown": "..."
}
```

### GET `/stats`
Get service status and statistics.

## 🔧 Local Development

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Install Playwright**
```bash
playwright install-deps
playwright install chromium
```

3. **Run locally**
```bash
uvicorn crawl_endpoint:app --host 0.0.0.0 --port 8000
```

## 📊 Features

- ✅ Website crawling with Playwright
- ✅ Email extraction
- ✅ Social media links detection
- ✅ Career page detection
- ✅ Markdown generation
- ✅ Health checks
- ✅ Comprehensive logging

## 🏗️ Architecture

- **FastAPI** - Web framework
- **Playwright** - Browser automation
- **BeautifulSoup** - HTML parsing
- **Fly.io** - Deployment platform

## 📝 License

MIT License

# Test auto-deploy
