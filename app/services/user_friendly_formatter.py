# app/services/user_friendly_formatter.py
"""
Service to convert technical job analysis to user-friendly output
"""

from typing import Dict, List, Optional
from app.services.job_analyzer import JobAnalyzer


class UserFriendlyFormatter:
    """Convert technical job analysis to user-friendly format"""
    
    def __init__(self):
        self.analyzer = JobAnalyzer()
    
    def format_job_for_user(self, job_data: Dict) -> Dict:
        """
        Convert raw job data to user-friendly format
        
        Args:
            job_data: Raw job data from crawler
            
        Returns:
            User-friendly job summary
        """
        # Get technical analysis (hidden from user)
        analysis = self.analyzer.analyze_job(job_data)
        
        # Create user-friendly output
        user_friendly = {
            "title": job_data.get("title", ""),
            "company": job_data.get("company", ""),
            "location": job_data.get("location", ""),
            "type": job_data.get("job_type", ""),
            "salary": job_data.get("salary", ""),
            "posted": job_data.get("posted_date", ""),
            "technologies": self._extract_user_friendly_technologies(job_data.get("description", "")),
            "level": self._get_user_friendly_level(analysis["level"]),
            "remote": self._is_remote(job_data.get("location", "")),
            "quality": self._get_quality_stars(analysis["quality_scores"]["overall"]),
            "match_score": self._calculate_match_percentage(analysis),
            "recommendation": self._generate_recommendation(analysis),
            "urgency": self._get_urgency_level(job_data.get("posted_date", "")),
            "benefits": self._extract_benefits(job_data.get("description", ""))
        }
        
        return user_friendly
    
    def format_jobs_list(self, jobs_data: List[Dict]) -> Dict:
        """
        Format multiple jobs for user display
        
        Args:
            jobs_data: List of raw job data
            
        Returns:
            User-friendly jobs list with summary
        """
        user_friendly_jobs = []
        
        for job_data in jobs_data:
            user_friendly_job = self.format_job_for_user(job_data)
            user_friendly_jobs.append(user_friendly_job)
        
        # Create summary
        summary = self._create_summary(user_friendly_jobs)
        
        return {
            "jobs": user_friendly_jobs,
            "summary": summary
        }
    
    def _extract_user_friendly_technologies(self, description: str) -> List[str]:
        """Extract and format technologies for user display"""
        if not description:
            return []
        
        # Get technical analysis
        technologies = self.analyzer.extract_technologies(description)
        
        # Filter and format for user
        user_techs = []
        for tech in technologies:
            # Skip single letters and very short tech names
            if len(tech) > 2 and tech not in ['r', 'js', 'ts']:
                # Capitalize properly
                if tech == 'node.js':
                    user_techs.append('Node.js')
                elif tech == 'react':
                    user_techs.append('React')
                elif tech == 'vue':
                    user_techs.append('Vue.js')
                elif tech == 'angular':
                    user_techs.append('Angular')
                elif tech == 'python':
                    user_techs.append('Python')
                elif tech == 'java':
                    user_techs.append('Java')
                elif tech == 'php':
                    user_techs.append('PHP')
                elif tech == 'laravel':
                    user_techs.append('Laravel')
                elif tech == 'django':
                    user_techs.append('Django')
                elif tech == 'aws':
                    user_techs.append('AWS')
                elif tech == 'docker':
                    user_techs.append('Docker')
                elif tech == 'kubernetes':
                    user_techs.append('Kubernetes')
                else:
                    user_techs.append(tech.title())
        
        # Return top 5 most relevant
        return user_techs[:5]
    
    def _get_user_friendly_level(self, technical_level: str) -> str:
        """Convert technical level to user-friendly format"""
        level_mapping = {
            "JUNIOR": "Junior",
            "MIDDLE": "Mid-level",
            "SENIOR": "Senior",
            "LEAD": "Lead",
            "PRINCIPAL": "Principal",
            "MANAGER": "Manager",
            "EXECUTIVE": "Executive",
            "UNKNOWN": "Not specified"
        }
        
        return level_mapping.get(technical_level, "Not specified")
    
    def _is_remote(self, location: str) -> bool:
        """Check if job is remote"""
        if not location:
            return False
        
        remote_indicators = [
            "remote", "work from home", "wfh", "virtual", 
            "online", "anywhere", "worldwide", "global"
        ]
        
        return any(indicator in location.lower() for indicator in remote_indicators)
    
    def _get_quality_stars(self, overall_score: float) -> str:
        """Convert quality score to star rating"""
        if overall_score >= 0.9:
            return "⭐⭐⭐⭐⭐"
        elif overall_score >= 0.8:
            return "⭐⭐⭐⭐"
        elif overall_score >= 0.7:
            return "⭐⭐⭐"
        elif overall_score >= 0.6:
            return "⭐⭐"
        else:
            return "⭐"
    
    def _calculate_match_percentage(self, analysis: Dict) -> str:
        """Calculate match percentage for user"""
        overall_score = analysis["quality_scores"]["overall"]
        match_percentage = int(overall_score * 100)
        return f"{match_percentage}%"
    
    def _generate_recommendation(self, analysis: Dict) -> str:
        """Generate user-friendly recommendation"""
        overall_score = analysis["quality_scores"]["overall"]
        completeness = analysis["quality_scores"]["completeness"]
        freshness = analysis["quality_scores"]["freshness"]
        
        if overall_score >= 0.8 and freshness >= 0.8:
            return "🔥 Apply now - Excellent opportunity!"
        elif overall_score >= 0.7:
            return "✅ Good match - Worth applying"
        elif overall_score >= 0.6:
            return "🤔 Consider applying"
        elif completeness < 0.5:
            return "⚠️ Limited information - Research more"
        else:
            return "📋 Basic opportunity"
    
    def _get_urgency_level(self, posted_date: str) -> str:
        """Get urgency level based on posted date"""
        if not posted_date:
            return "Unknown"
        
        # Extract days ago
        import re
        days_match = re.search(r'(\d+)\s*days?\s*ago', posted_date.lower())
        if not days_match:
            return "Unknown"
        
        days = int(days_match.group(1))
        
        if days <= 1:
            return "🔥 Very Urgent"
        elif days <= 3:
            return "⚡ Urgent"
        elif days <= 7:
            return "📅 Recent"
        elif days <= 14:
            return "📆 Moderate"
        else:
            return "⏰ Old"
    
    def _extract_benefits(self, description: str) -> List[str]:
        """Extract benefits from job description"""
        if not description:
            return []
        
        benefits_keywords = [
            "health insurance", "remote work", "flexible hours",
            "stock options", "bonus", "equity", "learning",
            "professional development", "team events", "competitive salary",
            "relocation", "work from home", "flexible schedule"
        ]
        
        found_benefits = []
        description_lower = description.lower()
        
        for benefit in benefits_keywords:
            if benefit in description_lower:
                found_benefits.append(benefit.title())
        
        return found_benefits[:3]  # Return top 3 benefits
    
    def _create_summary(self, user_friendly_jobs: List[Dict]) -> Dict:
        """Create summary statistics for jobs list"""
        if not user_friendly_jobs:
            return {}
        
        total_jobs = len(user_friendly_jobs)
        high_quality = sum(1 for job in user_friendly_jobs if "⭐⭐⭐⭐" in job["quality"] or "⭐⭐⭐⭐⭐" in job["quality"])
        remote_jobs = sum(1 for job in user_friendly_jobs if job["remote"])
        
        # Calculate average salary (simplified)
        salary_jobs = [job for job in user_friendly_jobs if job["salary"]]
        avg_salary = "Not specified"
        if salary_jobs:
            # This is a simplified calculation - in real app would parse actual numbers
            avg_salary = "Various ranges"
        
        # Get top technologies
        all_technologies = []
        for job in user_friendly_jobs:
            all_technologies.extend(job["technologies"])
        
        from collections import Counter
        tech_counter = Counter(all_technologies)
        top_technologies = [tech for tech, count in tech_counter.most_common(5)]
        
        return {
            "total_jobs": total_jobs,
            "high_quality": high_quality,
            "remote_opportunities": remote_jobs,
            "avg_salary": avg_salary,
            "top_technologies": top_technologies,
            "urgency_breakdown": {
                "very_urgent": sum(1 for job in user_friendly_jobs if "🔥 Very Urgent" in job["urgency"]),
                "urgent": sum(1 for job in user_friendly_jobs if "⚡ Urgent" in job["urgency"]),
                "recent": sum(1 for job in user_friendly_jobs if "📅 Recent" in job["urgency"])
            }
        }
    
    def format_for_mobile(self, job_data: Dict) -> str:
        """Format job for mobile display (compact)"""
        user_friendly = self.format_job_for_user(job_data)
        
        title = user_friendly["title"]
        company = user_friendly["company"]
        location = user_friendly["location"]
        salary = user_friendly["salary"]
        posted = user_friendly["posted"]
        technologies = ", ".join(user_friendly["technologies"][:2])
        quality = user_friendly["quality"]
        
        # Short location
        if "ho chi minh city" in location.lower():
            location = "HCM"
        elif "hanoi" in location.lower():
            location = "Hanoi"
        
        # Short salary
        if "$" in salary:
            salary = salary.split("$")[1].split(" ")[0] + "K"
        
        return f"{title} @ {company}\n📍 {location} | 💰 {salary} | ⏰ {posted}\n💻 {technologies} | {quality}"
    
    def format_for_desktop(self, job_data: Dict) -> str:
        """Format job for desktop display (detailed)"""
        user_friendly = self.format_job_for_user(job_data)
        
        lines = [
            f"🏷️ {user_friendly['title']}",
            f"🏢 {user_friendly['company']}",
            f"📍 {user_friendly['location']}",
            f"💰 {user_friendly['salary']}",
            f"⏰ {user_friendly['posted']}",
            f"💻 {', '.join(user_friendly['technologies'])}",
            f"🎯 {user_friendly['level']} | {user_friendly['type']}",
            f"{user_friendly['quality']} ({user_friendly['match_score']} match)",
            f"✅ {user_friendly['recommendation']}"
        ]
        
        if user_friendly['benefits']:
            lines.append(f"🎁 Benefits: {', '.join(user_friendly['benefits'])}")
        
        return "\n".join(lines)
    
    def format_for_dashboard(self, jobs_data: List[Dict]) -> str:
        """Format jobs for dashboard view"""
        formatted = self.format_jobs_list(jobs_data)
        summary = formatted["summary"]
        
        lines = [
            "📈 Job Opportunities Summary",
            f"├── 🔥 Hot Jobs: {summary['urgency_breakdown']['very_urgent']}",
            f"├── 💰 High Quality: {summary['high_quality']}",
            f"├── 🏠 Remote: {summary['remote_opportunities']}",
            f"└── ⭐ Top Quality: {summary['high_quality']}",
            "",
            "📋 Recent Matches:"
        ]
        
        # Add top 3 jobs
        for i, job in enumerate(formatted["jobs"][:3], 1):
            match_score = job["match_score"]
            title = job["title"]
            lines.append(f"├── {title} ({match_score} match)")
        
        return "\n".join(lines) 