# API Endpoints Reference

## 3 Main Endpoints for Job Crawler

### 1. Scrapy Career Page Detection
- **Endpoint**: `/api/v1/detect_career_pages_scrapy`
- **Method**: POST
- **Purpose**: Uses Scrapy to detect career pages from a company website
- **Input**: `{"url": "https://company.com/"}`
- **Output**: List of career pages found

### 2. Job URLs Extraction
- **Endpoint**: `/api/v1/extract_job_urls`
- **Method**: POST
- **Purpose**: Extracts job URLs from career pages (individual URLs or embedded jobs)
- **Input**: `{"url": "https://company.com/career/", "max_jobs": 50}`
- **Output**: Job URLs and/or direct job data

### 3. Job Details Extraction
- **Endpoint**: `/api/v1/extract_job_details`
- **Method**: POST
- **Purpose**: Extracts detailed job information from individual job URLs
- **Input**: `{"url": "https://company.com/job-title/"}`
- **Output**: Complete job details (title, description, type, etc.)

## Workflow
1. Start with company homepage → Scrapy detect career pages
2. Use career page URL → Extract job URLs
3. Use individual job URLs → Extract job details

## For N8N Integration
These 3 endpoints form the complete pipeline for job crawling and can be chained together in n8n workflows.
