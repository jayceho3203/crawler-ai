# app/utils/job_constants.py
"""
Constants for job field analysis and validation
"""

# Job Types by Category
JOB_TYPES = {
    # Time-based
    "FULL_TIME": ["full-time", "full time", "permanent", "regular"],
    "PART_TIME": ["part-time", "part time", "casual"],
    "CONTRACT": ["contract", "contractor", "freelance", "consulting"],
    "TEMPORARY": ["temporary", "temp", "seasonal", "project-based"],
    "INTERNSHIP": ["internship", "intern", "trainee", "apprentice"],
    
    # Location-based
    "REMOTE": ["remote", "work from home", "wfh", "virtual", "online"],
    "ON_SITE": ["on-site", "onsite", "office", "in-office", "in person"],
    "HYBRID": ["hybrid", "flexible", "mixed", "combination"],
    "TRAVEL": ["travel", "mobile", "field", "client-site"],
    "RELOCATION": ["relocation", "relocate", "move"],
    
    # Experience-based
    "ENTRY_LEVEL": ["entry-level", "entry level", "junior", "beginner", "fresh"],
    "MID_LEVEL": ["mid-level", "middle", "intermediate", "mid"],
    "SENIOR": ["senior", "experienced", "advanced", "expert"],
    "LEAD": ["lead", "team lead", "technical lead", "senior lead"],
    "PRINCIPAL": ["principal", "architect", "specialist", "consultant"],
    "MANAGER": ["manager", "management", "supervisor", "director"],
    "EXECUTIVE": ["executive", "vp", "c-level", "chief", "head"]
}

# Job Categories/Departments
JOB_CATEGORIES = {
    "ENGINEERING": [
        "software engineer", "developer", "programmer", "coder",
        "frontend developer", "backend developer", "full-stack developer",
        "devops engineer", "data engineer", "machine learning engineer",
        "mobile developer", "qa engineer", "test engineer", "system administrator"
    ],
    "DESIGN": [
        "ui/ux designer", "graphic designer", "product designer", "visual designer",
        "interaction designer", "user researcher", "designer", "creative designer"
    ],
    "MANAGEMENT": [
        "project manager", "product manager", "engineering manager", "team lead",
        "technical lead", "scrum master", "agile coach", "program manager"
    ],
    "MARKETING": [
        "marketing specialist", "digital marketing", "content marketing",
        "social media manager", "seo specialist", "growth hacker", "brand manager"
    ],
    "SALES": [
        "sales representative", "account manager", "business development",
        "sales manager", "customer success", "sales engineer"
    ],
    "DATA": [
        "data scientist", "data analyst", "business analyst", "data engineer",
        "machine learning engineer", "statistician", "research analyst"
    ],
    "HR": [
        "hr manager", "recruiter", "talent acquisition", "hr specialist",
        "people operations", "hr coordinator", "talent manager"
    ],
    "FINANCE": [
        "financial analyst", "accountant", "finance manager", "controller",
        "cfo", "financial advisor", "investment analyst"
    ],
    "OPERATIONS": [
        "operations manager", "operations analyst", "process improvement",
        "supply chain", "logistics", "operations specialist"
    ]
}

# Job Level Patterns
JOB_LEVEL_PATTERNS = {
    "JUNIOR": [
        r"junior\s+\w+", r"entry\s*level", r"beginner", r"fresh", r"graduate",
        r"new\s+grad", r"recent\s+graduate", r"0-2\s+years", r"1-3\s+years"
    ],
    "MIDDLE": [
        r"middle\s+\w+", r"mid\s*level", r"intermediate", r"mid\s+level",
        r"3-5\s+years", r"2-5\s+years", r"3-7\s+years"
    ],
    "SENIOR": [
        r"senior\s+\w+", r"experienced", r"advanced", r"expert",
        r"5\+\s+years", r"5-10\s+years", r"7\+\s+years"
    ],
    "LEAD": [
        r"lead\s+\w+", r"team\s+lead", r"technical\s+lead", r"senior\s+lead",
        r"leadership", r"team\s+leader"
    ],
    "PRINCIPAL": [
        r"principal\s+\w+", r"architect", r"specialist", r"consultant",
        r"expert\s+level", r"senior\s+specialist"
    ]
}

# Technology Keywords
TECHNOLOGY_KEYWORDS = {
    "PROGRAMMING_LANGUAGES": [
        "javascript", "js", "typescript", "ts", "python", "java", "c#", "c++",
        "php", "ruby", "go", "rust", "swift", "kotlin", "scala", "r", "matlab"
    ],
    "FRONTEND_FRAMEWORKS": [
        "react", "angular", "vue", "svelte", "next.js", "nuxt", "gatsby",
        "ember", "backbone", "jquery", "bootstrap", "tailwind"
    ],
    "BACKEND_FRAMEWORKS": [
        "node.js", "express", "django", "flask", "laravel", "spring",
        "asp.net", "rails", "fastapi", "gin", "echo"
    ],
    "DATABASES": [
        "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "firebase", "supabase", "sqlite"
    ],
    "CLOUD_PLATFORMS": [
        "aws", "azure", "google cloud", "gcp", "heroku", "digitalocean",
        "linode", "vultr", "cloudflare", "vercel", "netlify"
    ],
    "DEVOPS_TOOLS": [
        "docker", "kubernetes", "jenkins", "gitlab", "github actions",
        "terraform", "ansible", "prometheus", "grafana", "elk stack"
    ],
    "MOBILE_FRAMEWORKS": [
        "react native", "flutter", "xamarin", "ionic", "cordova",
        "native android", "native ios", "swift", "kotlin"
    ]
}

# Job Description Patterns
JOB_DESCRIPTION_PATTERNS = {
    "OPENING_PHRASES": [
        r"we\s+are\s+looking\s+for",
        r"join\s+our\s+team",
        r"we\s+are\s+hiring",
        r"we\s+need",
        r"we\s+seek",
        r"we\s+want",
        r"looking\s+for",
        r"seeking",
        r"hiring"
    ],
    "ACTION_VERBS": [
        "develop", "build", "create", "design", "implement", "maintain",
        "optimize", "scale", "improve", "enhance", "lead", "manage",
        "coordinate", "collaborate", "support", "analyze", "research",
        "investigate", "evaluate", "assess", "deploy", "test", "debug"
    ],
    "REQUIREMENTS_PHRASES": [
        r"requirements", r"qualifications", r"skills", r"experience",
        r"must\s+have", r"should\s+have", r"nice\s+to\s+have",
        r"minimum", r"preferred", r"required"
    ],
    "RESPONSIBILITIES_PHRASES": [
        r"responsibilities", r"duties", r"tasks", r"role", r"will",
        r"you\s+will", r"you\s+are", r"key\s+responsibilities"
    ],
    "BENEFITS_PHRASES": [
        r"benefits", r"perks", r"advantages", r"we\s+offer", r"you\s+get",
        r"compensation", r"salary", r"bonus", r"equity", r"stock"
    ]
}

# Location Patterns
LOCATION_PATTERNS = {
    "VIETNAM_CITIES": [
        "ho chi minh city", "hcm", "hcmc", "saigon", "hanoi", "ha noi",
        "da nang", "danang", "can tho", "cantho", "hai phong", "haiphong",
        "nha trang", "nhatrang", "vung tau", "vungtau", "buon ma thuot"
    ],
    "ASIA_CITIES": [
        "singapore", "bangkok", "jakarta", "manila", "kuala lumpur",
        "seoul", "tokyo", "hong kong", "hongkong", "taipei", "shanghai"
    ],
    "REMOTE_INDICATORS": [
        "remote", "work from home", "wfh", "virtual", "online",
        "anywhere", "worldwide", "global", "distributed"
    ],
    "HYBRID_INDICATORS": [
        "hybrid", "flexible", "mixed", "combination", "part remote",
        "part onsite", "some remote", "some onsite"
    ]
}

# Salary Patterns
SALARY_PATTERNS = {
    "CURRENCIES": {
        "USD": ["$", "usd", "dollar", "dollars"],
        "VND": ["vnd", "đồng", "vietnamese dong"],
        "EUR": ["€", "eur", "euro", "euros"],
        "SGD": ["sgd", "singapore dollar"],
        "JPY": ["¥", "jpy", "yen"],
        "KRW": ["krw", "won"]
    },
    "PERIODS": {
        "YEARLY": ["per year", "yearly", "annual", "annually", "/year", "/yr"],
        "MONTHLY": ["per month", "monthly", "/month", "/mo"],
        "HOURLY": ["per hour", "hourly", "/hour", "/hr"]
    },
    "RANGE_PATTERNS": [
        r"\$[\d,]+[\s-]+[\$]?[\d,]+",  # $50,000 - $80,000
        r"[\d,]+[\s-]+[\d,]+",         # 50,000 - 80,000
        r"[\d,]+[\s-]+[\d,]+k",        # 50k - 80k
        r"[\d,]+[\s-]+[\d,]+m",        # 50m - 80m (VND)
    ]
}

# Validation Rules
JOB_VALIDATION_RULES = {
    "TITLE": {
        "min_length": 3,
        "max_length": 100,
        "required": True,
        "patterns": [
            r"^[a-zA-Z\s\(\)\-\+\&]+$"  # Letters, spaces, parentheses, hyphens, plus, ampersand
        ]
    },
    "DESCRIPTION": {
        "min_length": 10,
        "max_length": 5000,
        "required": True
    },
    "LOCATION": {
        "min_length": 2,
        "max_length": 100,
        "required": True
    },
    "COMPANY": {
        "min_length": 2,
        "max_length": 100,
        "required": True
    },
    "JOB_TYPE": {
        "required": True,
        "valid_values": [item for sublist in JOB_TYPES.values() for item in sublist]
    }
}

# Quality Scoring Weights
QUALITY_SCORING_WEIGHTS = {
    "title": 0.25,
    "description": 0.20,
    "location": 0.15,
    "company": 0.15,
    "job_type": 0.10,
    "salary": 0.05,
    "posted_date": 0.05,
    "requirements": 0.05
}

# Completeness Scoring
COMPLETENESS_SCORING = {
    "REQUIRED_FIELDS": ["title", "description", "location", "company", "job_type"],
    "OPTIONAL_FIELDS": ["salary", "posted_date", "requirements", "benefits", "tags"],
    "WEIGHTS": {
        "required": 0.8,  # 80% weight for required fields
        "optional": 0.2   # 20% weight for optional fields
    }
}

# Relevance Scoring Keywords
RELEVANCE_KEYWORDS = {
    "HIGH_PRIORITY": [
        "software engineer", "developer", "programmer", "frontend", "backend",
        "full-stack", "devops", "data engineer", "machine learning"
    ],
    "MEDIUM_PRIORITY": [
        "designer", "manager", "analyst", "specialist", "coordinator",
        "assistant", "consultant", "architect"
    ],
    "LOW_PRIORITY": [
        "intern", "trainee", "junior", "entry level", "fresh graduate"
    ]
}

# Freshness Scoring
FRESHNESS_SCORING = {
    "VERY_RECENT": 7,      # Within 1 week
    "RECENT": 30,          # Within 1 month
    "MODERATE": 90,        # Within 3 months
    "OLD": 180,            # Within 6 months
    "VERY_OLD": 365        # Over 1 year
}

# Normalization Rules
NORMALIZATION_RULES = {
    "JOB_TYPE": {
        "full time": "full-time",
        "part time": "part-time",
        "work from home": "remote",
        "wfh": "remote",
        "on site": "on-site",
        "onsite": "on-site"
    },
    "LOCATION": {
        "hcm": "Ho Chi Minh City",
        "hcmc": "Ho Chi Minh City",
        "saigon": "Ho Chi Minh City",
        "ha noi": "Hanoi",
        "da nang": "Da Nang",
        "can tho": "Can Tho"
    },
    "LEVEL": {
        "mid-level": "middle",
        "mid level": "middle",
        "entry-level": "junior",
        "entry level": "junior"
    }
}

# Export all constants
__all__ = [
    "JOB_TYPES",
    "JOB_CATEGORIES", 
    "JOB_LEVEL_PATTERNS",
    "TECHNOLOGY_KEYWORDS",
    "JOB_DESCRIPTION_PATTERNS",
    "LOCATION_PATTERNS",
    "SALARY_PATTERNS",
    "JOB_VALIDATION_RULES",
    "QUALITY_SCORING_WEIGHTS",
    "COMPLETENESS_SCORING",
    "RELEVANCE_KEYWORDS",
    "FRESHNESS_SCORING",
    "NORMALIZATION_RULES"
] 