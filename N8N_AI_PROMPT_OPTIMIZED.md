# N8N AI Agent Prompt - Optimized Version

## Current Issues with Your Prompt:
1. **Too verbose** - 500+ words, causing confusion
2. **Redundant rules** - Multiple similar validation rules  
3. **Unclear priorities** - Hard to determine what's most important
4. **Complex formatting** - Bullet points and sections add complexity
5. **Mixed languages** - Vietnamese/English mixing causes confusion

## Optimized Prompt for N8N:

```
You are a job data extractor for Vietnamese and English job postings.

EXTRACT job information from:
- Individual job postings
- Career pages with job listings  
- Company pages with open positions

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
- job_link: Use input exactly
- job_description: Clean and summarize (max 200 words)
- job_type: Normalize to Full-time/Part-time/Contract/Internship/Remote/Hybrid
- Missing fields: Use null
- Remove HTML tags and clean formatting

OUTPUT:
- If valid job: Extract all available data
- If no job content: Set all fields to null except job_link
- Always return job_link exactly as input

Input data:
- job_link: {{$json.job_link}}
- job_name: {{$json.job_name || null}}
- job_type: {{$json.job_type || null}}
- job_role: {{$json.job_role || null}}
- job_description: {{$json.job_description || ''}}

Return JSON format with: job_link, job_name, job_type, job_role, job_description, location, salary
```

## Key Improvements:

### 1. **Reduced Length**: 200 words vs 500+ words
### 2. **Clear Structure**: 
- EXTRACT (what to do)
- VALIDATION (when to accept/reject)  
- EXTRACTION RULES (how to process)
- OUTPUT (what to return)

### 3. **Simplified Language**:
- Remove redundant phrases
- Use bullet points only for key lists
- Clear, direct instructions

### 4. **Better Prioritization**:
- Most important rules first
- Clear accept/reject criteria
- Simple extraction rules

### 5. **Consistent Formatting**:
- No mixed Vietnamese/English
- Clean, professional tone
- Easy to understand

## Benefits:
- **Faster processing** - Shorter prompt = faster AI response
- **Better accuracy** - Clearer instructions = better results  
- **Easier maintenance** - Simpler to modify and debug
- **Consistent results** - Less ambiguity = more predictable output
- **Lower costs** - Shorter prompt = cheaper API calls

## Usage in N8N:
1. Copy the optimized prompt above
2. Paste into your N8N AI Agent node
3. Keep the same input format: `{{$json.job_link}}`, etc.
4. Test with your job data

## Expected Results:
- More consistent job extraction
- Better description summarization (200 words max)
- Cleaner job_type normalization
- Faster processing times
- Lower API costs
