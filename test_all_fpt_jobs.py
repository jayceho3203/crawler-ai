#!/usr/bin/env python3
"""
Test script to extract ALL job titles from tuyendung.fpt.com
"""
import sys
import os
import requests
from bs4 import BeautifulSoup
import re

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def extract_all_fpt_jobs():
    """Extract all job titles from tuyendung.fpt.com"""
    url = "https://tuyendung.fpt.com"
    
    print(f"🔍 Extracting ALL jobs from: {url}")
    print("=" * 60)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        
        # Common job titles to look for
        job_titles = [
            # English job titles
            r'\.Net Developer', r'DotNet Developer', r'Business Analyst', r'Senior Business Analyst',
            r'iOS Developer', r'IOS Developer', r'Data Scientist', r'Senior Data Scientist',
            r'AI Engineer', r'Frontend Developer', r'Senior Front-end', r'Front-end Developer',
            r'Backend Developer', r'Fullstack Developer', r'Mobile Developer', r'Android Developer',
            r'DevOps Engineer', r'QA Engineer', r'Tester', r'Software Tester',
            r'UI/UX Designer', r'Product Manager', r'Project Manager', r'Scrum Master',
            r'Data Analyst', r'Middle Data Analyst', r'Machine Learning Engineer',
            r'Cloud Engineer', r'Security Engineer', r'System Administrator',
            
            # Vietnamese job titles
            r'Trưởng nhóm Lập trình', r'Trưởng nhóm', r'Lập trình viên', r'Kỹ sư phần mềm',
            r'Kiểm thử phần mềm', r'Phân tích dữ liệu', r'Thiết kế UI/UX', r'Quản lý dự án',
            r'Quản lý sản phẩm', r'Chuyên viên phân tích', r'Kỹ sư AI', r'Kỹ sư ML',
            r'Kỹ sư DevOps', r'Kỹ sư bảo mật', r'Quản trị hệ thống'
        ]
        
        found_job_titles = []
        for pattern in job_titles:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                if match not in found_job_titles:
                    found_job_titles.append(match)
        
        print(f"✅ Found {len(found_job_titles)} job titles:")
        for i, title in enumerate(found_job_titles, 1):
            print(f"   {i:2d}. {title}")
        
        # Now create job objects
        jobs = []
        for title in found_job_titles:
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
            
            # Extract location from text near the job title
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
            
            job = {
                'title': title,
                'company': 'FPT',
                'location': location,
                'url': job_url,
                'salary': None,
                'job_type': None,
                'description': f"Job title found: {title}",
                'source_url': url,
                'extracted_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            jobs.append(job)
        
        print(f"\n🎉 Created {len(jobs)} job objects:")
        for i, job in enumerate(jobs, 1):
            print(f"   {i:2d}. {job['title']}")
            print(f"       Company: {job['company']}")
            print(f"       Location: {job['location']}")
            print(f"       URL: {job['url']}")
            print()
        
        return {
            'success': True,
            'total_jobs_found': len(jobs),
            'jobs': jobs,
            'source_url': url
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            'success': False,
            'error': str(e),
            'total_jobs_found': 0,
            'jobs': []
        }

if __name__ == "__main__":
    from urllib.parse import urljoin
    import time
    
    print("🚀 Testing ALL FPT Job Extraction")
    print("Extracting every job title found on tuyendung.fpt.com")
    print()
    
    result = extract_all_fpt_jobs()
    
    print(f"\n✅ Test completed!")
    print(f"   Total jobs found: {result.get('total_jobs_found', 0)}") 