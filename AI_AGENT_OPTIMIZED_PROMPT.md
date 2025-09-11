# AI Agent Optimized Prompt for Job Data Extraction

## Current Issues with Existing Prompt:
1. **Too verbose** - 500+ words, causing confusion
2. **Redundant rules** - Multiple similar validation rules
3. **Unclear priorities** - Hard to determine what's most important
4. **Complex formatting** - Bullet points and sections add complexity
5. **Mixed languages** - Vietnamese/English mixing causes confusion

## Optimized Prompt (Concise & Effective):

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

## Implementation:

Replace the current AI validation prompt in `_validate_job_with_ai` method with this optimized version.

## Benefits:
- **Faster processing** - Shorter prompt = faster AI response
- **Better accuracy** - Clearer instructions = better results  
- **Easier maintenance** - Simpler to modify and debug
- **Consistent results** - Less ambiguity = more predictable output
