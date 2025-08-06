# Job Data JSON Schema

```json
{
  "$id": "https://wehappi.com/job.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Job",
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "The job title or position name."
    },
    "job_type": {
      "type": "string",
      "description": "The type of employment (e.g., Full-time, Part-time, Contract)."
    },
    "job_role": {
      "type": "string", 
      "description": "The specific role or position within the company."
    },
    "description": {
      "type": "string",
      "description": "The detailed job description including requirements, responsibilities, and benefits."
    },
    "url": {
      "type": "string",
      "description": "The URL link to the original job posting."
    }
  },
  "required": ["title", "job_type", "job_role", "description", "url"]
}
```

## Key Features:
- **Standard JSON Schema format** with proper metadata
- **Descriptions** for each field to clarify purpose
- **All fields required** - ensures complete job data
- **Matches AI Agent expectations** from our prompt
- **Clean structure** for job data processing

## Usage in n8n:
Copy this schema into the "Input Schema" field of your Structured Output Parser node. 