# N8N AI Agent Prompt - Schema Optimized

## Required Schema:
```json
{
  "properties": {
    "job_name": {
      "description": "The job title or position name."
    },
    "job_type": {
      "description": "The type of employment (e.g., Full-time, Part-time, Contract)."
    },
    "job_role": {
      "description": "The specific role or position within the company."
    },
    "job_description": {
      "description": "The detailed job description including requirements, responsibilities, and benefits."
    },
    "job_link": {
      "description": "The URL link to the original job posting."
    }
  },
  "required": ["job_name", "job_type", "job_role", "job_link"]
}
```

## Optimized N8N Prompt:

```
You are a job data extractor. Extract job information and return ONLY the required JSON schema.

REQUIRED FIELDS (must be present):
- job_name: Job title or position name
- job_type: Employment type (Full-time/Part-time/Contract/Internship/Remote/Hybrid)
- job_role: Specific role or position
- job_link: Original job posting URL

OPTIONAL FIELDS:
- job_description: Detailed description (max 200 words, clean formatting)

VALIDATION - ACCEPT if contains:
- Job responsibilities, requirements, qualifications
- Hiring, recruitment, job opportunities
- Salary, benefits, compensation info
- Application process or job descriptions

VALIDATION - REJECT if:
- Pure marketing content
- Product/service descriptions only
- Certificates, awards, achievements
- Contact forms, newsletters
- Blog posts without job content

EXTRACTION RULES:
- job_link: Use input exactly (REQUIRED)
- job_name: Extract job title, use "Unknown" if not found (REQUIRED)
- job_type: Normalize to Full-time/Part-time/Contract/Internship/Remote/Hybrid (REQUIRED)
- job_role: Same as job_name or extract specific role (REQUIRED)
- job_description: Clean, summarize to 200 words max (OPTIONAL)

OUTPUT FORMAT:
Return ONLY valid JSON matching the schema. If no valid job content found, return:
{
  "job_name": "Unknown",
  "job_type": "Full-time", 
  "job_role": "Unknown",
  "job_link": "{{$json.job_link}}"
}

Input data:
- job_link: {{$json.job_link}}
- job_name: {{$json.job_name || null}}
- job_type: {{$json.job_type || null}}
- job_role: {{$json.job_role || null}}
- job_description: {{$json.job_description || ''}}
```

## Key Features:

### 1. **Schema Compliance** ✅
- Enforces required fields: job_name, job_type, job_role, job_link
- Optional field: job_description
- Always returns valid JSON

### 2. **Fallback Values** ✅
- job_name: "Unknown" if not found
- job_type: "Full-time" as default
- job_role: Same as job_name or "Unknown"
- job_link: Always preserved from input

### 3. **Clean Output** ✅
- job_description: Max 200 words, clean formatting
- job_type: Normalized to standard values
- Removes HTML tags and unnecessary content

### 4. **Error Handling** ✅
- If no valid job content: Returns minimal valid JSON
- If missing required fields: Uses fallback values
- Always maintains schema structure

## Usage in N8N:
1. Copy the optimized prompt above
2. Paste into your N8N AI Agent node
3. Set response format to JSON
4. Test with your job data

## Expected Output Examples:

### Valid Job:
```json
{
  "job_name": "Software Developer",
  "job_type": "Full-time",
  "job_role": "Software Developer", 
  "job_description": "We are looking for a skilled software developer...",
  "job_link": "https://example.com/job/123"
}
```

### Invalid/No Job Content:
```json
{
  "job_name": "Unknown",
  "job_type": "Full-time",
  "job_role": "Unknown",
  "job_link": "https://example.com/marketing-page"
}
```

## Benefits:
- **Guaranteed Schema Compliance** - Always returns valid JSON
- **Consistent Structure** - Same fields every time
- **Error Resilient** - Handles missing/invalid data gracefully
- **Clean Data** - Normalized and formatted properly
- **Fast Processing** - Concise prompt for quick responses
