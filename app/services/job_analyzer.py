# app/services/job_analyzer.py
"""
Job field analyzer service for extracting and analyzing job information
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.utils.job_constants import (
    JOB_TYPES, JOB_CATEGORIES, JOB_LEVEL_PATTERNS, TECHNOLOGY_KEYWORDS,
    JOB_DESCRIPTION_PATTERNS, LOCATION_PATTERNS, SALARY_PATTERNS,
    JOB_VALIDATION_RULES, QUALITY_SCORING_WEIGHTS, COMPLETENESS_SCORING,
    RELEVANCE_KEYWORDS, FRESHNESS_SCORING, NORMALIZATION_RULES
)


class JobAnalyzer:
    """Analyze job fields and calculate quality scores"""
    
    def __init__(self):
        self.job_types_flat = [item for sublist in JOB_TYPES.values() for item in sublist]
        self.categories_flat = [item for sublist in JOB_CATEGORIES.values() for item in sublist]
    
    def analyze_job(self, job_data: Dict) -> Dict:
        """
        Analyze a job and return comprehensive analysis
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "job_title": self.analyze_job_title(job_data.get("title", "")),
            "job_type": self.analyze_job_type(job_data.get("job_type", "")),
            "location": self.analyze_location(job_data.get("location", "")),
            "company": self.analyze_company(job_data.get("company", "")),
            "description": self.analyze_description(job_data.get("description", "")),
            "salary": self.analyze_salary(job_data.get("salary", "")),
            "posted_date": self.analyze_posted_date(job_data.get("posted_date", "")),
            "requirements": self.analyze_requirements(job_data.get("requirements", "")),
            "benefits": self.analyze_benefits(job_data.get("benefits", "")),
            "technologies": self.extract_technologies(job_data.get("description", "")),
            "level": self.extract_job_level(job_data.get("title", "")),
            "category": self.categorize_job(job_data.get("title", "")),
            "quality_scores": self.calculate_quality_scores(job_data),
            "validation": self.validate_job(job_data),
            "normalized_data": self.normalize_job_data(job_data)
        }
        
        return analysis
    
    def analyze_job_title(self, title: str) -> Dict:
        """Analyze job title"""
        if not title:
            return {"valid": False, "score": 0, "issues": ["Title is empty"]}
        
        analysis = {
            "original": title,
            "normalized": self.normalize_text(title),
            "length": len(title),
            "word_count": len(title.split()),
            "valid": True,
            "score": 1.0,
            "issues": []
        }
        
        # Check length
        if len(title) < JOB_VALIDATION_RULES["TITLE"]["min_length"]:
            analysis["issues"].append("Title too short")
            analysis["score"] -= 0.3
        elif len(title) > JOB_VALIDATION_RULES["TITLE"]["max_length"]:
            analysis["issues"].append("Title too long")
            analysis["score"] -= 0.2
        
        # Check pattern
        if not re.match(JOB_VALIDATION_RULES["TITLE"]["patterns"][0], title):
            analysis["issues"].append("Title contains invalid characters")
            analysis["score"] -= 0.2
        
        # Check if it's a real job title
        if not any(category in title.lower() for category in self.categories_flat):
            analysis["issues"].append("Title doesn't match common job categories")
            analysis["score"] -= 0.1
        
        analysis["score"] = max(0, analysis["score"])
        return analysis
    
    def analyze_job_type(self, job_type: str) -> Dict:
        """Analyze job type"""
        if not job_type:
            return {"valid": False, "score": 0, "issues": ["Job type is empty"]}
        
        normalized_type = self.normalize_text(job_type)
        analysis = {
            "original": job_type,
            "normalized": normalized_type,
            "valid": normalized_type in self.job_types_flat,
            "score": 1.0 if normalized_type in self.job_types_flat else 0.0,
            "issues": []
        }
        
        if not analysis["valid"]:
            analysis["issues"].append(f"Invalid job type: {job_type}")
        
        return analysis
    
    def analyze_location(self, location: str) -> Dict:
        """Analyze job location"""
        if not location:
            return {"valid": False, "score": 0, "issues": ["Location is empty"]}
        
        normalized_location = self.normalize_text(location)
        analysis = {
            "original": location,
            "normalized": normalized_location,
            "valid": True,
            "score": 1.0,
            "issues": [],
            "is_remote": False,
            "is_hybrid": False,
            "country": None,
            "city": None
        }
        
        # Check for remote indicators
        if any(indicator in normalized_location for indicator in LOCATION_PATTERNS["REMOTE_INDICATORS"]):
            analysis["is_remote"] = True
            analysis["score"] += 0.1  # Bonus for remote
        
        # Check for hybrid indicators
        if any(indicator in normalized_location for indicator in LOCATION_PATTERNS["HYBRID_INDICATORS"]):
            analysis["is_hybrid"] = True
            analysis["score"] += 0.05  # Bonus for hybrid
        
        # Extract country and city
        for city in LOCATION_PATTERNS["VIETNAM_CITIES"]:
            if city in normalized_location:
                analysis["city"] = city
                analysis["country"] = "Vietnam"
                break
        
        for city in LOCATION_PATTERNS["ASIA_CITIES"]:
            if city in normalized_location:
                analysis["city"] = city
                analysis["country"] = "Asia"
                break
        
        return analysis
    
    def analyze_company(self, company: str) -> Dict:
        """Analyze company information"""
        if not company:
            return {"valid": False, "score": 0, "issues": ["Company is empty"]}
        
        analysis = {
            "original": company,
            "normalized": self.normalize_text(company),
            "length": len(company),
            "valid": True,
            "score": 1.0,
            "issues": []
        }
        
        # Check length
        if len(company) < JOB_VALIDATION_RULES["COMPANY"]["min_length"]:
            analysis["issues"].append("Company name too short")
            analysis["score"] -= 0.3
        elif len(company) > JOB_VALIDATION_RULES["COMPANY"]["max_length"]:
            analysis["issues"].append("Company name too long")
            analysis["score"] -= 0.2
        
        return analysis
    
    def analyze_description(self, description: str) -> Dict:
        """Analyze job description"""
        if not description:
            return {"valid": False, "score": 0, "issues": ["Description is empty"]}
        
        analysis = {
            "original": description,
            "normalized": self.normalize_text(description),
            "length": len(description),
            "word_count": len(description.split()),
            "valid": True,
            "score": 1.0,
            "issues": [],
            "has_opening_phrase": False,
            "has_action_verbs": False,
            "has_requirements": False,
            "has_responsibilities": False,
            "has_benefits": False
        }
        
        # Check length
        if len(description) < JOB_VALIDATION_RULES["DESCRIPTION"]["min_length"]:
            analysis["issues"].append("Description too short")
            analysis["score"] -= 0.4
        elif len(description) > JOB_VALIDATION_RULES["DESCRIPTION"]["max_length"]:
            analysis["issues"].append("Description too long")
            analysis["score"] -= 0.1
        
        # Check for opening phrases
        for pattern in JOB_DESCRIPTION_PATTERNS["OPENING_PHRASES"]:
            if re.search(pattern, description.lower()):
                analysis["has_opening_phrase"] = True
                analysis["score"] += 0.1
                break
        
        # Check for action verbs
        action_verbs_found = []
        for verb in JOB_DESCRIPTION_PATTERNS["ACTION_VERBS"]:
            if verb in description.lower():
                action_verbs_found.append(verb)
        
        if action_verbs_found:
            analysis["has_action_verbs"] = True
            analysis["score"] += 0.1
            analysis["action_verbs"] = action_verbs_found
        
        # Check for requirements
        for pattern in JOB_DESCRIPTION_PATTERNS["REQUIREMENTS_PHRASES"]:
            if re.search(pattern, description.lower()):
                analysis["has_requirements"] = True
                analysis["score"] += 0.1
                break
        
        # Check for responsibilities
        for pattern in JOB_DESCRIPTION_PATTERNS["RESPONSIBILITIES_PHRASES"]:
            if re.search(pattern, description.lower()):
                analysis["has_responsibilities"] = True
                analysis["score"] += 0.1
                break
        
        # Check for benefits
        for pattern in JOB_DESCRIPTION_PATTERNS["BENEFITS_PHRASES"]:
            if re.search(pattern, description.lower()):
                analysis["has_benefits"] = True
                analysis["score"] += 0.1
                break
        
        analysis["score"] = min(1.0, analysis["score"])
        return analysis
    
    def analyze_salary(self, salary: str) -> Dict:
        """Analyze salary information"""
        if not salary:
            return {"valid": False, "score": 0, "issues": ["Salary not provided"]}
        
        analysis = {
            "original": salary,
            "normalized": self.normalize_text(salary),
            "valid": True,
            "score": 1.0,
            "issues": [],
            "currency": None,
            "period": None,
            "range": None,
            "min_amount": None,
            "max_amount": None
        }
        
        # Extract currency
        for currency, symbols in SALARY_PATTERNS["CURRENCIES"].items():
            if any(symbol in salary.lower() for symbol in symbols):
                analysis["currency"] = currency
                break
        
        # Extract period
        for period, indicators in SALARY_PATTERNS["PERIODS"].items():
            if any(indicator in salary.lower() for indicator in indicators):
                analysis["period"] = period
                break
        
        # Extract range
        for pattern in SALARY_PATTERNS["RANGE_PATTERNS"]:
            match = re.search(pattern, salary)
            if match:
                analysis["range"] = match.group()
                # Try to extract min/max amounts
                numbers = re.findall(r'[\d,]+', match.group())
                if len(numbers) >= 2:
                    analysis["min_amount"] = numbers[0].replace(',', '')
                    analysis["max_amount"] = numbers[1].replace(',', '')
                break
        
        return analysis
    
    def analyze_posted_date(self, posted_date: str) -> Dict:
        """Analyze posted date"""
        if not posted_date:
            return {"valid": False, "score": 0, "issues": ["Posted date not provided"]}
        
        analysis = {
            "original": posted_date,
            "valid": True,
            "score": 1.0,
            "issues": [],
            "days_ago": None,
            "freshness_score": 0.0
        }
        
        # Try to extract days ago
        days_match = re.search(r'(\d+)\s*days?\s*ago', posted_date.lower())
        if days_match:
            days = int(days_match.group(1))
            analysis["days_ago"] = days
            
            # Calculate freshness score
            if days <= FRESHNESS_SCORING["VERY_RECENT"]:
                analysis["freshness_score"] = 1.0
            elif days <= FRESHNESS_SCORING["RECENT"]:
                analysis["freshness_score"] = 0.8
            elif days <= FRESHNESS_SCORING["MODERATE"]:
                analysis["freshness_score"] = 0.6
            elif days <= FRESHNESS_SCORING["OLD"]:
                analysis["freshness_score"] = 0.4
            else:
                analysis["freshness_score"] = 0.2
        
        return analysis
    
    def analyze_requirements(self, requirements: str) -> Dict:
        """Analyze job requirements"""
        if not requirements:
            return {"valid": False, "score": 0, "issues": ["Requirements not provided"]}
        
        analysis = {
            "original": requirements,
            "normalized": self.normalize_text(requirements),
            "length": len(requirements),
            "valid": True,
            "score": 1.0,
            "issues": []
        }
        
        return analysis
    
    def analyze_benefits(self, benefits: str) -> Dict:
        """Analyze job benefits"""
        if not benefits:
            return {"valid": False, "score": 0, "issues": ["Benefits not provided"]}
        
        analysis = {
            "original": benefits,
            "normalized": self.normalize_text(benefits),
            "length": len(benefits),
            "valid": True,
            "score": 1.0,
            "issues": []
        }
        
        return analysis
    
    def extract_technologies(self, text: str) -> List[str]:
        """Extract technology keywords from text"""
        technologies = []
        text_lower = text.lower()
        
        for category, tech_list in TECHNOLOGY_KEYWORDS.items():
            for tech in tech_list:
                if tech in text_lower:
                    technologies.append(tech)
        
        return list(set(technologies))  # Remove duplicates
    
    def extract_job_level(self, title: str) -> str:
        """Extract job level from title"""
        title_lower = title.lower()
        
        for level, patterns in JOB_LEVEL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, title_lower):
                    return level
        
        return "UNKNOWN"
    
    def categorize_job(self, title: str) -> str:
        """Categorize job based on title"""
        title_lower = title.lower()
        
        for category, keywords in JOB_CATEGORIES.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return category
        
        return "OTHER"
    
    def calculate_quality_scores(self, job_data: Dict) -> Dict:
        """Calculate various quality scores for the job"""
        scores = {
            "completeness": self.calculate_completeness_score(job_data),
            "relevance": self.calculate_relevance_score(job_data),
            "freshness": self.calculate_freshness_score(job_data),
            "overall": 0.0
        }
        
        # Calculate overall score using custom weights for quality metrics
        quality_weights = {
            "completeness": 0.4,
            "relevance": 0.4,
            "freshness": 0.2
        }
        
        overall_score = 0.0
        for metric, weight in quality_weights.items():
            if metric in scores:
                overall_score += scores[metric] * weight
        
        scores["overall"] = min(1.0, overall_score)
        return scores
    
    def calculate_completeness_score(self, job_data: Dict) -> float:
        """Calculate completeness score"""
        required_fields = COMPLETENESS_SCORING["REQUIRED_FIELDS"]
        optional_fields = COMPLETENESS_SCORING["OPTIONAL_FIELDS"]
        
        required_score = 0.0
        optional_score = 0.0
        
        # Check required fields
        for field in required_fields:
            if job_data.get(field) and str(job_data[field]).strip():
                required_score += 1.0
        
        required_score = required_score / len(required_fields)
        
        # Check optional fields
        for field in optional_fields:
            if job_data.get(field) and str(job_data[field]).strip():
                optional_score += 1.0
        
        optional_score = optional_score / len(optional_fields)
        
        # Calculate weighted score
        completeness = (
            required_score * COMPLETENESS_SCORING["WEIGHTS"]["required"] +
            optional_score * COMPLETENESS_SCORING["WEIGHTS"]["optional"]
        )
        
        return completeness
    
    def calculate_relevance_score(self, job_data: Dict) -> float:
        """Calculate relevance score"""
        title = job_data.get("title", "").lower()
        description = job_data.get("description", "").lower()
        text = f"{title} {description}"
        
        score = 0.0
        max_possible_score = 0.0
        
        # Check high priority keywords (weight: 3)
        for keyword in RELEVANCE_KEYWORDS["HIGH_PRIORITY"]:
            if keyword in text:
                score += 3.0
            max_possible_score += 3.0
        
        # Check medium priority keywords (weight: 2)
        for keyword in RELEVANCE_KEYWORDS["MEDIUM_PRIORITY"]:
            if keyword in text:
                score += 2.0
            max_possible_score += 2.0
        
        # Check low priority keywords (weight: 1)
        for keyword in RELEVANCE_KEYWORDS["LOW_PRIORITY"]:
            if keyword in text:
                score += 1.0
            max_possible_score += 1.0
        
        if max_possible_score > 0:
            return min(1.0, score / max_possible_score)
        
        return 0.0
    
    def calculate_freshness_score(self, job_data: Dict) -> float:
        """Calculate freshness score"""
        posted_date = job_data.get("posted_date", "")
        if not posted_date:
            return 0.0
        
        # Extract days ago
        days_match = re.search(r'(\d+)\s*days?\s*ago', posted_date.lower())
        if not days_match:
            return 0.5  # Default score if can't parse
        
        days = int(days_match.group(1))
        
        if days <= FRESHNESS_SCORING["VERY_RECENT"]:
            return 1.0
        elif days <= FRESHNESS_SCORING["RECENT"]:
            return 0.8
        elif days <= FRESHNESS_SCORING["MODERATE"]:
            return 0.6
        elif days <= FRESHNESS_SCORING["OLD"]:
            return 0.4
        else:
            return 0.2
    
    def validate_job(self, job_data: Dict) -> Dict:
        """Validate job data against rules"""
        validation = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        for field, rules in JOB_VALIDATION_RULES.items():
            if field.lower() in job_data:
                value = job_data[field.lower()]
                
                if rules["required"] and (not value or not str(value).strip()):
                    validation["issues"].append(f"{field} is required")
                    validation["valid"] = False
                
                if value and "min_length" in rules:
                    if len(str(value)) < rules["min_length"]:
                        validation["warnings"].append(f"{field} is too short")
                
                if value and "max_length" in rules:
                    if len(str(value)) > rules["max_length"]:
                        validation["warnings"].append(f"{field} is too long")
        
        return validation
    
    def normalize_job_data(self, job_data: Dict) -> Dict:
        """Normalize job data using normalization rules"""
        normalized = {}
        
        for field, value in job_data.items():
            if not value:
                continue
            
            normalized_value = str(value)
            
            # Apply normalization rules
            if field == "job_type":
                normalized_value = self.normalize_text(normalized_value)
                for old, new in NORMALIZATION_RULES["JOB_TYPE"].items():
                    if old in normalized_value:
                        normalized_value = normalized_value.replace(old, new)
            
            elif field == "location":
                normalized_value = self.normalize_text(normalized_value)
                for old, new in NORMALIZATION_RULES["LOCATION"].items():
                    if old in normalized_value:
                        normalized_value = normalized_value.replace(old, new)
            
            elif field == "title":
                normalized_value = self.normalize_text(normalized_value)
                for old, new in NORMALIZATION_RULES["LEVEL"].items():
                    if old in normalized_value:
                        normalized_value = normalized_value.replace(old, new)
            
            normalized[field] = normalized_value
        
        return normalized
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""
        
        # Convert to lowercase and remove extra whitespace
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        return normalized
    
    def get_job_summary(self, analysis: Dict) -> Dict:
        """Get a summary of job analysis"""
        return {
            "title": analysis["job_title"]["normalized"],
            "type": analysis["job_type"]["normalized"],
            "location": analysis["location"]["normalized"],
            "company": analysis["company"]["normalized"],
            "level": analysis["level"],
            "category": analysis["category"],
            "technologies": analysis["technologies"],
            "quality_scores": analysis["quality_scores"],
            "is_valid": analysis["validation"]["valid"],
            "issues": analysis["validation"]["issues"],
            "warnings": analysis["validation"]["warnings"]
        } 