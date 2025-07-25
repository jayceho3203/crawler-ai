#!/usr/bin/env python3
"""
Test script for JobAnalyzer service
Demonstrates job field analysis based on the image example
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.job_analyzer import JobAnalyzer


def test_job_analyzer():
    """Test the JobAnalyzer with sample job data"""
    
    # Initialize analyzer
    analyzer = JobAnalyzer()
    
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
            "requirements": "5+ years React experience, leadership skills",
            "benefits": "Stock options, health benefits, professional development"
        },
        {
            "title": "UI/UX Designer",
            "job_type": "Contract",
            "location": "Hybrid (Ho Chi Minh City)",
            "company": "DesignStudio",
            "description": "Create beautiful and functional user interfaces. Collaborate with product and engineering teams.",
            "salary": "30,000,000 - 45,000,000 VND monthly",
            "posted_date": "5 days ago",
            "requirements": "3+ years design experience, Figma proficiency",
            "benefits": "Flexible schedule, creative environment"
        },
        {
            "title": "DevOps Engineer",
            "job_type": "Full-time",
            "location": "Singapore",
            "company": "CloudTech",
            "description": "Manage cloud infrastructure and deployment pipelines. Ensure high availability and performance.",
            "salary": "SGD 8,000 - 12,000 per month",
            "posted_date": "1 day ago",
            "requirements": "AWS experience, Docker, Kubernetes knowledge",
            "benefits": "Relocation support, competitive benefits"
        }
    ]
    
    print("🔍 Job Field Analysis Demo")
    print("=" * 60)
    
    for i, job_data in enumerate(sample_jobs, 1):
        print(f"\n📋 Job #{i}: {job_data['title']}")
        print("-" * 40)
        
        # Analyze the job
        analysis = analyzer.analyze_job(job_data)
        summary = analyzer.get_job_summary(analysis)
        
        # Display results
        print(f"🏷️  Title: {summary['title']}")
        print(f"🏢 Type: {summary['type']}")
        print(f"📍 Location: {summary['location']}")
        print(f"🏢 Company: {summary['company']}")
        print(f"📊 Level: {summary['level']}")
        print(f"🎯 Category: {summary['category']}")
        print(f"💻 Technologies: {', '.join(summary['technologies'][:5])}")
        
        # Quality scores
        scores = summary['quality_scores']
        print(f"📈 Quality Scores:")
        print(f"   - Completeness: {scores['completeness']:.2f}")
        print(f"   - Relevance: {scores['relevance']:.2f}")
        print(f"   - Freshness: {scores['freshness']:.2f}")
        print(f"   - Overall: {scores['overall']:.2f}")
        
        # Validation
        print(f"✅ Valid: {summary['is_valid']}")
        if summary['issues']:
            print(f"❌ Issues: {', '.join(summary['issues'])}")
        if summary['warnings']:
            print(f"⚠️  Warnings: {', '.join(summary['warnings'])}")
        
        print()


def demonstrate_field_extraction():
    """Demonstrate specific field extraction capabilities"""
    
    analyzer = JobAnalyzer()
    
    print("\n🔧 Field Extraction Examples")
    print("=" * 60)
    
    # Job Type Analysis
    print("\n🏷️ Job Type Analysis:")
    job_types = ["Full-time", "Remote", "Part-time", "Contract", "Internship", "Freelance"]
    for job_type in job_types:
        analysis = analyzer.analyze_job_type(job_type)
        print(f"   {job_type}: {'✅' if analysis['valid'] else '❌'} (Score: {analysis['score']:.1f})")
    
    # Location Analysis
    print("\n📍 Location Analysis:")
    locations = [
        "Ho Chi Minh City, Vietnam",
        "Remote",
        "Hanoi, Vietnam", 
        "Singapore",
        "Hybrid (HCM)",
        "Work from home"
    ]
    for location in locations:
        analysis = analyzer.analyze_location(location)
        remote_status = "🖥️ Remote" if analysis['is_remote'] else "🏢 On-site"
        print(f"   {location}: {remote_status} (Score: {analysis['score']:.1f})")
    
    # Technology Extraction
    print("\n💻 Technology Extraction:")
    descriptions = [
        "We need a React developer with Node.js experience",
        "Python developer with Django and PostgreSQL knowledge",
        "DevOps engineer with AWS, Docker, and Kubernetes",
        "Frontend developer with Vue.js and TypeScript"
    ]
    for desc in descriptions:
        techs = analyzer.extract_technologies(desc)
        print(f"   '{desc}': {', '.join(techs)}")
    
    # Job Level Extraction
    print("\n👨‍💼 Job Level Extraction:")
    titles = [
        "Junior Software Engineer",
        "Middle PHP Developer",
        "Senior Frontend Developer", 
        "Lead DevOps Engineer",
        "Principal Architect"
    ]
    for title in titles:
        level = analyzer.extract_job_level(title)
        print(f"   {title}: {level}")


def demonstrate_quality_scoring():
    """Demonstrate quality scoring system"""
    
    analyzer = JobAnalyzer()
    
    print("\n📊 Quality Scoring Examples")
    print("=" * 60)
    
    # Test cases with different quality levels
    test_cases = [
        {
            "name": "High Quality Job",
            "data": {
                "title": "Senior Software Engineer",
                "job_type": "Full-time",
                "location": "Ho Chi Minh City, Vietnam",
                "company": "TechCorp",
                "description": "We are looking for a Senior Software Engineer to develop and maintain web applications using React and Node.js. You will lead technical initiatives and mentor junior developers.",
                "salary": "$80,000 - $120,000 per year",
                "posted_date": "1 day ago",
                "requirements": "5+ years experience, React, Node.js, leadership skills",
                "benefits": "Health insurance, stock options, remote work"
            }
        },
        {
            "name": "Medium Quality Job",
            "data": {
                "title": "Frontend Developer",
                "job_type": "Full-time",
                "location": "Hanoi",
                "company": "Startup",
                "description": "Develop frontend applications using React.",
                "salary": "30,000,000 VND",
                "posted_date": "1 week ago"
            }
        },
        {
            "name": "Low Quality Job",
            "data": {
                "title": "Developer",
                "job_type": "Part-time",
                "location": "Remote",
                "company": "Company",
                "description": "Need developer",
                "posted_date": "1 month ago"
            }
        }
    ]
    
    for case in test_cases:
        print(f"\n📋 {case['name']}:")
        analysis = analyzer.analyze_job(case['data'])
        scores = analysis['quality_scores']
        
        print(f"   Completeness: {scores['completeness']:.2f}")
        print(f"   Relevance: {scores['relevance']:.2f}")
        print(f"   Freshness: {scores['freshness']:.2f}")
        print(f"   Overall: {scores['overall']:.2f}")
        
        # Quality assessment
        if scores['overall'] >= 0.8:
            quality = "🟢 Excellent"
        elif scores['overall'] >= 0.6:
            quality = "🟡 Good"
        elif scores['overall'] >= 0.4:
            quality = "🟠 Fair"
        else:
            quality = "🔴 Poor"
        
        print(f"   Assessment: {quality}")


def show_job_type_categories():
    """Show all available job type categories"""
    
    from app.utils.job_constants import JOB_TYPES, JOB_CATEGORIES
    
    print("\n📋 Available Job Types")
    print("=" * 60)
    
    for category, types in JOB_TYPES.items():
        print(f"\n🏷️ {category.replace('_', ' ').title()}:")
        for job_type in types:
            print(f"   - {job_type}")
    
    print("\n🎯 Job Categories")
    print("=" * 60)
    
    for category, keywords in JOB_CATEGORIES.items():
        print(f"\n🏢 {category}:")
        for keyword in keywords[:5]:  # Show first 5
            print(f"   - {keyword}")
        if len(keywords) > 5:
            print(f"   ... and {len(keywords) - 5} more")


def main():
    """Main function to run all demonstrations"""
    
    print("🚀 Job Field Analysis System Demo")
    print("=" * 60)
    print("Based on the image showing job listings with fields like:")
    print("- Job Name: Software Engineer, Middle PHP Developer")
    print("- Job Type: Full-time, Remote")
    print("- Job Role: Software Engineer, Middle PHP Developer (Laravel)")
    print("- Job Description: We are looking for a Softwar...")
    print("- Job Link: View (clickable link)")
    print()
    
    # Run demonstrations
    test_job_analyzer()
    demonstrate_field_extraction()
    demonstrate_quality_scoring()
    show_job_type_categories()
    
    print("\n✅ Demo completed!")
    print("\n💡 Key Features Demonstrated:")
    print("   - Job field analysis and validation")
    print("   - Technology keyword extraction")
    print("   - Job level and category classification")
    print("   - Quality scoring (completeness, relevance, freshness)")
    print("   - Location analysis (remote, on-site, hybrid)")
    print("   - Salary and date parsing")
    print("   - Data normalization")


if __name__ == "__main__":
    main() 