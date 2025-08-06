# Updated JSON Schema for Job Data

## Current Schema (needs update):
```json
{
  "jobs": [
    {
      "title": "string",
      "job_link": "string", 
      "company": "string",
      "location": "string",
      "type": "string"
    }
  ]
}
```

## Updated Schema (recommended):
```json
{
  "type": "object",
  "properties": {
    "title": { "type": "string" },
    "job_type": { "type": "string" },
    "job_role": { "type": "string" },
    "description": { "type": "string" },
    "url": { "type": "string" }
  },
  "required": ["title", "description", "url"]
}
```

## Key Changes:
1. **Remove array structure** - AI processes one job at a time
2. **Add `description` field** - Required for AI summarization
3. **Add `job_type` and `job_role`** - Match AI prompt expectations
4. **Change `job_link` to `url`** - Match AI prompt format
5. **Remove `company` and `location`** - Not needed for AI summarization task
6. **Update required fields** - Focus on essential data for AI processing

## Why These Changes:
- **AI Agent expects single job object**, not array
- **`description` field is crucial** for summarization task
- **Simplified structure** focuses on what AI actually needs
- **Consistent naming** with AI prompt expectations 