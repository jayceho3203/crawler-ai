#!/usr/bin/env python3
"""
Test script for Simple Job Formatter
Demonstrates essential job fields only
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.simple_job_formatter import SimpleJobFormatter


def test_simple_formatter():
    """Test the SimpleJobFormatter with sample job data"""
    
    # Initialize formatter
    formatter = SimpleJobFormatter()
    
    # Sample job data based on the image
    sample_jobs = [
        {
            "title": "Software Engineer",
            "job_type": "Full-time",
            "location": "Ho Chi Minh City, Vietnam",
            "company": "TechCorp",
            "description": "We are looking for a Software Engineer to join our growing team. You will develop and maintain web applications using modern technologies.",
            "salary": "$50,000 - $80,000 per year",
            "posted_date": "2 days ago",
            "job_link": "https://techcorp.com/jobs/software-engineer",
            "requirements": "3+ years experience with JavaScript, React, Node.js",
            "benefits": "Health insurance, remote work, flexible hours"
        },
        {
            "title": "Middle PHP Developer (Laravel)",
            "job_type": "Remote",
            "location": "Remote",
            "company": "StartupXYZ",
            "description": "Develop and optimize backend systems using PHP and Laravel framework. Work with a distributed team on exciting projects.",
            "salary": "40,000,000 - 60,000,000 VND per month",
            "posted_date": "1 week ago",
            "job_link": "https://startupxyz.com/careers/php-developer",
            "requirements": "2+ years PHP experience, Laravel framework knowledge",
            "benefits": "Competitive salary, learning opportunities, team events"
        },
        {
            "title": "Senior Frontend Developer",
            "job_type": "Full-time",
            "location": "Hanoi, Vietnam",
            "company": "DigitalAgency",
            "description": "Lead frontend development initiatives and mentor junior developers. Build scalable React applications.",
            "salary": "$70,000 - $100,000 annually",
            "posted_date": "3 days ago",
            "job_link": "https://digitalagency.com/jobs/frontend-developer",
            "requirements": "5+ years React experience, leadership skills",
            "benefits": "Stock options, health benefits, professional development"
        }
    ]
    
    print("🎯 Simple Job Formatter Demo")
    print("=" * 50)
    print("Chỉ trả về các trường cần thiết cho người dùng")
    print()
    
    # Test single job formatting
    print("📋 Single Job Format:")
    print("-" * 30)
    single_job = formatter.format_job(sample_jobs[0])
    for key, value in single_job.items():
        print(f"{key}: {value}")
    print()
    
    # Test multiple jobs formatting
    print("📋 Multiple Jobs Format:")
    print("-" * 30)
    formatted_jobs = formatter.format_jobs_list(sample_jobs)
    print(f"Total jobs: {formatted_jobs['total_count']}")
    print()
    
    for i, job in enumerate(formatted_jobs['jobs'], 1):
        print(f"Job #{i}:")
        print(f"  Title: {job['title']}")
        print(f"  Company: {job['company']}")
        print(f"  Location: {job['location']}")
        print(f"  Type: {job['type']}")
        print(f"  Salary: {job['salary']}")
        print(f"  Posted: {job['posted_date']}")
        print(f"  Link: {job['job_link']}")
        print()
    
    # Test job summary
    print("📊 Job Summary:")
    print("-" * 30)
    summary = formatter.get_job_summary(sample_jobs)
    print(f"Total jobs: {summary['total_jobs']}")
    print("Job types:")
    for job_type, count in summary['job_types'].items():
        print(f"  - {job_type}: {count}")
    print("Locations:")
    for location, count in summary['locations'].items():
        print(f"  - {location}: {count}")
    print()


def demonstrate_essential_fields():
    """Demonstrate what essential fields mean"""
    
    print("🎯 Essential Fields Only")
    print("=" * 50)
    print("Người dùng chỉ cần:")
    print()
    print("✅ Cần thiết:")
    print("  - title: Tên công việc")
    print("  - job_link: Link để click vào xem chi tiết")
    print("  - company: Tên công ty")
    print("  - location: Địa điểm")
    print("  - type: Loại công việc (Full-time, Remote, etc.)")
    print("  - salary: Lương (nếu có)")
    print("  - posted_date: Ngày đăng")
    print("  - description: Mô tả ngắn gọn")
    print()
    print("❌ KHÔNG cần:")
    print("  - Phân tích kỹ thuật phức tạp")
    print("  - Quality scores")
    print("  - Technology extraction")
    print("  - Job level analysis")
    print("  - Recommendation engine")
    print("  - Star ratings")
    print("  - Match percentages")
    print()
    print("🎯 Nguyên tắc: Đơn giản, rõ ràng, dễ sử dụng!")


def show_api_output_example():
    """Show example API output"""
    
    print("🚀 API Output Example")
    print("=" * 50)
    
    example_output = {
        "success": True,
        "url": "https://example.com/careers",
        "formatted_jobs": {
            "jobs": [
                {
                    "title": "Software Engineer",
                    "company": "TechCorp",
                    "location": "Ho Chi Minh City, Vietnam",
                    "type": "Full-time",
                    "salary": "$50,000 - $80,000 per year",
                    "posted_date": "2 days ago",
                    "job_link": "https://techcorp.com/jobs/software-engineer",
                    "description": "We are looking for a Software Engineer..."
                }
            ],
            "total_count": 1
        },
        "job_summary": {
            "total_jobs": 1,
            "job_types": {"Full-time": 1},
            "locations": {"Ho Chi Minh City, Vietnam": 1}
        }
    }
    
    print("API Response Structure:")
    print("├── success: True/False")
    print("├── url: URL được crawl")
    print("├── formatted_jobs: Jobs đã format")
    print("│   ├── jobs: List các job")
    print("│   └── total_count: Tổng số job")
    print("└── job_summary: Tóm tắt")
    print("    ├── total_jobs: Tổng số")
    print("    ├── job_types: Phân loại theo type")
    print("    └── locations: Phân loại theo location")
    print()
    print("🎯 Người dùng chỉ cần:")
    print("1. Lấy danh sách jobs từ formatted_jobs.jobs")
    print("2. Hiển thị title, company, location, type")
    print("3. Tạo link click vào job_link")
    print("4. Hiển thị summary từ job_summary")


def main():
    """Main function"""
    
    print("🎯 Simple Job Formatter - Essential Fields Only")
    print("=" * 60)
    print("Nguyên tắc: Chỉ trả về những gì người dùng thực sự cần!")
    print()
    
    # Run demonstrations
    test_simple_formatter()
    demonstrate_essential_fields()
    show_api_output_example()
    
    print("\n✅ Demo completed!")
    print("\n💡 Key Benefits:")
    print("   - Đơn giản, dễ hiểu")
    print("   - Chỉ trả về thông tin cần thiết")
    print("   - Người dùng tự click link để xem chi tiết")
    print("   - Không có phân tích phức tạp")
    print("   - Performance tốt hơn")
    print("   - Dễ maintain và debug")


if __name__ == "__main__":
    main() 