#!/usr/bin/env python3
"""
Job extraction module for career pages
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
from typing import Dict, List, Optional

# Job-related keywords in Vietnamese and English
JOB_KEYWORDS = {
    'vi': [
        'tuyển dụng', 'tuyển', 'việc làm', 'cơ hội nghề nghiệp', 'cơ hội việc làm',
        'tuyển nhân viên', 'tuyển dụng nhân viên', 'tuyển dụng developer',
        'tuyển dụng engineer', 'tuyển dụng analyst', 'tuyển dụng manager',
        'tuyển dụng leader', 'tuyển dụng tester', 'tuyển dụng designer',
        'tuyển dụng frontend', 'tuyển dụng backend', 'tuyển dụng fullstack',
        'tuyển dụng mobile', 'tuyển dụng ios', 'tuyển dụng android',
        'tuyển dụng data', 'tuyển dụng ai', 'tuyển dụng machine learning',
        'tuyển dụng devops', 'tuyển dụng qa', 'tuyển dụng ba',
        'tuyển dụng pm', 'tuyển dụng scrum', 'tuyển dụng agile'
    ],
    'en': [
        'hiring', 'recruitment', 'career', 'job', 'position', 'opportunity',
        'developer', 'engineer', 'analyst', 'manager', 'leader', 'tester',
        'designer', 'frontend', 'backend', 'fullstack', 'mobile', 'ios',
        'android', 'data', 'ai', 'machine learning', 'devops', 'qa', 'ba',
        'pm', 'scrum', 'agile', 'senior', 'junior', 'middle'
    ],
    'global': [
        # Universal job keywords
        'apply', 'application', 'open position', 'vacancy', 'employment',
        'work with us', 'join our team', 'we are hiring', 'career opportunities',
        'job openings', 'current openings', 'available positions',
        
        # Common job titles in multiple languages
        'software engineer', 'developer', 'programmer', 'coder',
        'data scientist', 'analyst', 'consultant', 'specialist',
        'manager', 'director', 'lead', 'principal', 'architect',
        'designer', 'researcher', 'coordinator', 'assistant',
        
        # Industry-specific
        'marketing', 'sales', 'finance', 'hr', 'human resources',
        'operations', 'product', 'project', 'business', 'strategy'
    ]
}

# CSS selectors for job listings
JOB_SELECTORS = [
    # Common job listing selectors
    '.job-item', '.job-listing', '.job-card', '.job-post', '.career-item',
    '.position-item', '.vacancy-item', '.job-opportunity', '.job-opening',
    '.job-position', '.job-role', '.job-title', '.career-opportunity',
    
    # Vietnamese specific selectors
    '.tuyen-dung', '.viec-lam', '.co-hoi', '.nhan-vien', '.vi-tri',
    '.tuyen-dung-item', '.viec-lam-item', '.co-hoi-item', '.nhan-vien-item',
    
    # List items that might contain jobs
    'li.job', 'li.career', 'li.position', 'li.vacancy',
    'li.tuyen-dung', 'li.viec-lam', 'li.co-hoi',
    
    # Generic selectors
    '.item', '.listing', '.card', '.post', '.entry',
    'article', 'section', 'div[class*="job"]', 'div[class*="career"]',
    'div[class*="position"]', 'div[class*="vacancy"]',
    
    # FPT specific selectors (based on the image)
    '.job-list', '.job-list-item', '.recruitment-item', '.career-list',
    '.tuyen-dung-list', '.viec-lam-list', '.co-hoi-list'
]

# Job board specific selectors
JOB_BOARD_SELECTORS = {
    'tuyendung.fpt.com': [
        '.job-item', '.job-listing', '.career-item', '.position-item',
        '.tuyen-dung-item', '.viec-lam-item', '.co-hoi-item',
        'li.job', 'li.career', 'li.position', 'li.tuyen-dung',
        '.item', '.listing', '.card', '.post'
    ],
    'career.vng.com.vn': [
        '.job-item', '.job-listing', '.career-item', '.position-item',
        '.tuyen-dung-item', '.viec-lam-item', '.co-hoi-item'
    ],
    'topcv.vn': [
        '.job-item', '.job-listing', '.career-item', '.position-item'
    ]
}

def get_domain(url: str) -> str:
    """Extract domain from URL"""
    return urlparse(url).netloc.lower()

def extract_job_from_element(element, base_url: str) -> Optional[Dict]:
    """Extract job information from a single element"""
    try:
        # Get text content
        text = element.get_text(strip=True)
        if not text or len(text) < 5:
            return None
            
        # Find job title
        title = None
        
        # Look for title in common elements
        title_elements = element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b'])
        for title_elem in title_elements:
            title_text = title_elem.get_text(strip=True)
            if title_text and len(title_text) > 3:
                title = title_text
                break
        
        # If no title found in headers, use the first meaningful text
        if not title:
            # Split by common separators and take the first meaningful part
            parts = re.split(r'[|\-–—•·]', text)
            for part in parts:
                part = part.strip()
                if part and len(part) > 3 and not part.isdigit():
                    title = part
                    break
        
        # If still no title, use the whole text (truncated)
        if not title:
            title = text[:100] if len(text) > 100 else text
        
        # Find job URL
        job_url = None
        link = element.find('a', href=True)
        if link:
            job_url = urljoin(base_url, link.get('href'))
        
        # Extract company name from URL or text
        company = None
        domain = get_domain(base_url)
        if 'fpt' in domain:
            company = 'FPT'
        elif 'vng' in domain:
            company = 'VNG'
        elif 'tma' in domain:
            company = 'TMA Solutions'
        elif 'cmc' in domain:
            company = 'CMC Corporation'
        
        # Extract location (look for common location patterns)
        location = None
        location_patterns = [
            r'(Hà Nội|Hanoi|HN)',
            r'(TP\.?HCM|Ho Chi Minh|HCM|Saigon)',
            r'(Đà Nẵng|Da Nang)',
            r'(Cần Thơ|Can Tho)',
            r'(Hải Phòng|Hai Phong)',
            r'(Bình Dương|Binh Duong)',
            r'(Đồng Nai|Dong Nai)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1)
                break
        
        # Extract salary if present
        salary = None
        salary_patterns = [
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:triệu|million|tr)',
            r'(\$\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:USD|VND)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                salary = match.group(0)
                break
        
        # Determine job type
        job_type = None
        if any(word in text.lower() for word in ['full-time', 'fulltime', 'toàn thời gian']):
            job_type = 'Full-time'
        elif any(word in text.lower() for word in ['part-time', 'parttime', 'bán thời gian']):
            job_type = 'Part-time'
        elif any(word in text.lower() for word in ['intern', 'internship', 'thực tập']):
            job_type = 'Internship'
        elif any(word in text.lower() for word in ['contract', 'hợp đồng']):
            job_type = 'Contract'
        
        # Get description (first 200 characters)
        description = text[:200] + '...' if len(text) > 200 else text
        
        return {
            'title': title,
            'company': company,
            'location': location,
            'url': job_url,
            'salary': salary,
            'job_type': job_type,
            'description': description,
            'source_url': base_url,
            'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"   Error extracting job from element: {e}")
        return None

def extract_jobs_from_page(url: str, max_jobs: int = 50) -> Dict:
    """Extract jobs from a single page"""
    print(f"🔍 Extracting jobs from: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        domain = get_domain(url)
        
        jobs = []
        
        # Try domain-specific selectors first
        if domain in JOB_BOARD_SELECTORS:
            selectors = JOB_BOARD_SELECTORS[domain]
            print(f"   Using domain-specific selectors for {domain}")
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"   Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements[:max_jobs]:
                        job = extract_job_from_element(element, url)
                        if job:
                            jobs.append(job)
                    
                    if jobs:
                        break
        
        # If no jobs found, try generic selectors
        if not jobs:
            print(f"   No jobs found with domain-specific selectors, trying generic selectors...")
            
            for selector in JOB_SELECTORS:
                elements = soup.select(selector)
                if elements:
                    print(f"   Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements[:max_jobs]:
                        job = extract_job_from_element(element, url)
                        if job:
                            jobs.append(job)
                    
                    if jobs:
                        break
        
                # If still no jobs, try text-based job title extraction
        if not jobs:
            print(f"   No jobs found with selectors, trying text-based extraction...")
            
            # Extract job titles directly from page text
            page_text = soup.get_text()
            
            # Common job titles to look for (global)
            job_titles = [
                # English job titles (global)
                r'\.Net Developer', r'DotNet Developer', r'Business Analyst', r'Senior Business Analyst',
                r'iOS Developer', r'IOS Developer', r'Data Scientist', r'Senior Data Scientist',
                r'AI Engineer', r'Frontend Developer', r'Senior Front-end', r'Front-end Developer',
                r'Backend Developer', r'Fullstack Developer', r'Mobile Developer', r'Android Developer',
                r'DevOps Engineer', r'QA Engineer', r'Tester', r'Software Tester',
                r'UI/UX Designer', r'Product Manager', r'Project Manager', r'Scrum Master',
                r'Data Analyst', r'Middle Data Analyst', r'Machine Learning Engineer',
                r'Cloud Engineer', r'Security Engineer', r'System Administrator',
                r'Software Engineer', r'Programmer', r'Coder', r'Consultant', r'Specialist',
                r'Manager', r'Director', r'Lead', r'Principal', r'Architect',
                r'Designer', r'Researcher', r'Coordinator', r'Assistant',
                r'Marketing', r'Sales', r'Finance', r'HR', r'Human Resources',
                r'Operations', r'Product', r'Project', r'Business', r'Strategy',
                
                # Vietnamese job titles
                r'Trưởng nhóm Lập trình', r'Trưởng nhóm', r'Lập trình viên', r'Kỹ sư phần mềm',
                r'Kiểm thử phần mềm', r'Phân tích dữ liệu', r'Thiết kế UI/UX', r'Quản lý dự án',
                r'Quản lý sản phẩm', r'Chuyên viên phân tích', r'Kỹ sư AI', r'Kỹ sư ML',
                r'Kỹ sư DevOps', r'Kỹ sư bảo mật', r'Quản trị hệ thống',
                
                # Generic patterns for any language
                r'\w+\s+(Developer|Engineer|Analyst|Manager|Designer|Specialist|Consultant)',
                r'(Senior|Junior|Lead|Principal)\s+\w+',
                r'\w+\s+(Developer|Engineer|Analyst|Manager)'
            ]
            
            found_job_titles = []
            for pattern in job_titles:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    if match not in found_job_titles:
                        found_job_titles.append(match)
            
            print(f"   Found {len(found_job_titles)} job titles in text")
            
            # Create job objects for found titles
            for title in found_job_titles[:max_jobs]:
                # Try to find a link near this job title
                job_url = None
                
                # Look for links that might be related to this job
                for link in soup.find_all('a', href=True):
                    link_text = link.get_text(strip=True)
                    if title.lower() in link_text.lower() or any(word in link_text.lower() for word in title.lower().split()):
                        job_url = urljoin(url, link.get('href'))
                        break
                
                # If no specific link found, try to find any job-related link
                if not job_url:
                    for link in soup.find_all('a', href=True):
                        link_text = link.get_text(strip=True)
                        href = link.get('href')
                        
                        # Check if this looks like a job application link
                        if any(keyword in link_text.lower() for keyword in ['apply', 'ứng tuyển', 'nộp đơn', 'tuyển dụng', 'career', 'job']):
                            job_url = urljoin(url, href)
                            break
                
                # Extract company name from domain (generic approach)
                company = None
                # Try to extract company name from domain
                domain_parts = domain.split('.')
                if len(domain_parts) >= 2:
                    # Remove common TLDs and get main domain
                    main_domain = domain_parts[-2] if domain_parts[-1] in ['com', 'vn', 'org', 'net', 'co', 'io'] else domain_parts[-1]
                    # Capitalize and clean up
                    company = main_domain.upper()
                    
                    # Handle special cases
                    if 'fpt' in domain:
                        company = 'FPT'
                    elif 'vng' in domain:
                        company = 'VNG'
                    elif 'tma' in domain:
                        company = 'TMA Solutions'
                    elif 'cmc' in domain:
                        company = 'CMC Corporation'
                    elif 'google' in domain:
                        company = 'Google'
                    elif 'microsoft' in domain:
                        company = 'Microsoft'
                    elif 'amazon' in domain:
                        company = 'Amazon'
                    elif 'apple' in domain:
                        company = 'Apple'
                    elif 'meta' in domain or 'facebook' in domain:
                        company = 'Meta'
                    elif 'netflix' in domain:
                        company = 'Netflix'
                    elif 'uber' in domain:
                        company = 'Uber'
                    elif 'airbnb' in domain:
                        company = 'Airbnb'
                
                # Extract location from text near the job title
                location = None
                location_patterns = [
                    r'(Hà Nội|Hanoi|HN|hn)',
                    r'(TP\.?HCM|Ho Chi Minh|HCM|Saigon|hcm)',
                    r'(Đà Nẵng|Da Nang|danang)',
                    r'(Cần Thơ|Can Tho|cantho)',
                    r'(Hải Phòng|Hai Phong|haiphong)',
                    r'(Bình Dương|Binh Duong|binhduong)',
                    r'(Đồng Nai|Dong Nai|dongnai)'
                ]
                
                # Look for location in a window around the job title
                title_index = page_text.find(title)
                if title_index != -1:
                    # Look in a 500 character window around the job title
                    start = max(0, title_index - 250)
                    end = min(len(page_text), title_index + 250)
                    context = page_text[start:end]
                    
                    for pattern in location_patterns:
                        match = re.search(pattern, context, re.IGNORECASE)
                        if match:
                            location = match.group(1)
                            break
                
                # Normalize location names
                if location:
                    location_lower = location.lower()
                    if location_lower in ['hn', 'hanoi']:
                        location = 'Hà Nội'
                    elif location_lower in ['hcm', 'tp.hcm', 'tp hcm', 'ho chi minh', 'saigon']:
                        location = 'TP.HCM'
                    elif location_lower in ['danang', 'da nang']:
                        location = 'Đà Nẵng'
                    elif location_lower in ['cantho', 'can tho']:
                        location = 'Cần Thơ'
                    elif location_lower in ['haiphong', 'hai phong']:
                        location = 'Hải Phòng'
                    elif location_lower in ['binhduong', 'binh duong']:
                        location = 'Bình Dương'
                    elif location_lower in ['dongnai', 'dong nai']:
                        location = 'Đồng Nai'
                
                job = {
                    'title': title,
                    'company': company,
                    'location': location,
                    'url': job_url,
                    'salary': None,
                    'job_type': None,
                    'description': f"Job title found: {title}",
                    'source_url': url,
                    'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                jobs.append(job)
            
            print(f"   Created {len(jobs)} job objects from text extraction")
        
        # If still no jobs, try keyword-based approach
        if not jobs:
            print(f"   No jobs found with text extraction, trying keyword-based approach...")
            
            # Look for links containing job keywords
            for link in soup.find_all('a', href=True):
                link_text = link.get_text(strip=True)
                link_href = link.get('href')
                
                if not link_text or len(link_text) < 3:
                    continue
                
                # Check if link text contains job keywords (global)
                text_lower = link_text.lower()
                is_job_link = False
                
                # Check all language keywords including global
                for lang, keywords in JOB_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword.lower() in text_lower:
                            is_job_link = True
                            break
                    if is_job_link:
                        break
                
                if is_job_link:
                    job_url = urljoin(url, link_href)
                    job = {
                        'title': link_text,
                        'company': None,
                        'location': None,
                        'url': job_url,
                        'salary': None,
                        'job_type': None,
                        'description': link_text,
                        'source_url': url,
                        'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    jobs.append(job)
                    
                    if len(jobs) >= max_jobs:
                        break
        
        # Remove duplicates based on title and URL
        unique_jobs = []
        seen_titles = set()
        seen_urls = set()
        for job in jobs:
            title = job.get('title', '').lower()
            url = job.get('url', '')
            
            # Only remove if both title AND url are duplicates
            is_duplicate = False
            if title in seen_titles and url in seen_urls:
                is_duplicate = True
            elif title in seen_titles and not url:  # If no URL, check title only
                is_duplicate = True
            elif url in seen_urls and not title:  # If no title, check URL only
                is_duplicate = True
            
            if not is_duplicate:
                unique_jobs.append(job)
                seen_titles.add(title)
                if url:
                    seen_urls.add(url)
        
        print(f"   ✅ Extracted {len(unique_jobs)} unique jobs")
        
        return {
            'success': True,
            'total_jobs_found': len(unique_jobs),
            'jobs': unique_jobs,
            'source_url': url
        }
        
    except Exception as e:
        print(f"   ❌ Error extracting jobs: {e}")
        return {
            'success': False,
            'error': str(e),
            'total_jobs_found': 0,
            'jobs': []
        }

def extract_jobs_from_multiple_pages(urls: List[str], max_jobs_per_page: int = 20) -> Dict:
    """Extract jobs from multiple career page URLs"""
    print(f"🚀 Starting job extraction from {len(urls)} pages")
    
    all_jobs = []
    successful_pages = 0
    
    for i, url in enumerate(urls):
        print(f"\n📄 Processing page {i+1}/{len(urls)}: {url}")
        
        try:
            result = extract_jobs_from_page(url, max_jobs_per_page)
            
            if result.get('success'):
                jobs = result.get('jobs', [])
                all_jobs.extend(jobs)
                successful_pages += 1
                print(f"   ✅ Found {len(jobs)} jobs")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Error processing {url}: {e}")
        
        # Small delay between requests
        time.sleep(1)
    
    # Remove duplicates based on URL
    unique_jobs = []
    seen_urls = set()
    for job in all_jobs:
        if job.get('url') and job['url'] not in seen_urls:
            unique_jobs.append(job)
            seen_urls.add(job['url'])
    
    print(f"\n🎉 Job extraction completed!")
    print(f"   📄 Pages processed: {successful_pages}/{len(urls)}")
    print(f"   💼 Total unique jobs: {len(unique_jobs)}")
    
    return {
        'success': True,
        'total_jobs_found': len(unique_jobs),
        'jobs': unique_jobs,
        'pages_processed': successful_pages,
        'total_pages': len(urls)
    }

if __name__ == "__main__":
    # Test the job extractor
    test_urls = [
        "https://career.vng.com.vn/co-hoi-nghe-nghiep",
        "https://fpt.com.vn/vi/co-hoi-nghe-nghiep"
    ]
    
    print("🧪 Testing Job Extractor")
    print("=" * 50)
    
    for url in test_urls:
        print(f"\n🔗 Testing: {url}")
        result = extract_jobs_from_page(url)
        
        if result["success"]:
            print(f"✅ Found {result['total_jobs_found']} jobs")
            for i, job in enumerate(result['jobs'][:3]):  # Show first 3
                print(f"   {i+1}. {job.get('title', 'No title')} - {job.get('company', 'No company')}")
        else:
            print(f"❌ Failed: {result['error']}") 