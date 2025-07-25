# app/services/simple_job_formatter.py
"""
Simple job formatter - only essential fields for user
"""

from typing import Dict, List, Optional


class SimpleJobFormatter:
    """Format job data to essential fields only"""
    
    def format_job(self, job_data: Dict) -> Dict:
        """
        Format job to essential fields only
        
        Args:
            job_data: Raw job data from crawler
            
        Returns:
            Essential job fields
        """
        return {
            "title": job_data.get("title", ""),
            "company": job_data.get("company", ""),
            "location": job_data.get("location", ""),
            "type": job_data.get("job_type", ""),
            "salary": job_data.get("salary", ""),
            "posted_date": job_data.get("posted_date", ""),
            "job_link": job_data.get("job_link", ""),
            "description": job_data.get("description", "")
        }
    
    def format_jobs_list(self, jobs_data: List[Dict]) -> Dict:
        """
        Format multiple jobs to essential fields
        
        Args:
            jobs_data: List of raw job data
            
        Returns:
            List of essential job fields
        """
        formatted_jobs = []
        
        for job_data in jobs_data:
            formatted_job = self.format_job(job_data)
            formatted_jobs.append(formatted_job)
        
        return {
            "jobs": formatted_jobs,
            "total_count": len(formatted_jobs)
        }
    
    def get_job_summary(self, jobs_data: List[Dict]) -> Dict:
        """
        Get simple summary of jobs
        
        Args:
            jobs_data: List of raw job data
            
        Returns:
            Simple summary
        """
        if not jobs_data:
            return {"total_jobs": 0}
        
        # Count by type
        type_counts = {}
        location_counts = {}
        
        for job in jobs_data:
            job_type = job.get("job_type", "Unknown")
            location = job.get("location", "Unknown")
            
            type_counts[job_type] = type_counts.get(job_type, 0) + 1
            location_counts[location] = location_counts.get(location, 0) + 1
        
        return {
            "total_jobs": len(jobs_data),
            "job_types": type_counts,
            "locations": location_counts
        } 