# Job Extraction Rules

## Universal Job Extraction Patterns

### General Job Title Patterns
- `([A-Z][a-zA-Z\s]+(?:Developer|Engineer|Manager|Analyst|Specialist|Assistant|Designer)).*?(?:Apply|View|See|Learn|Details)`
- `([A-Z][a-zA-Z\s]+(?:Developer|Engineer|Manager|Analyst|Specialist|Assistant|Designer)).*?(?:Fulltime|Part-time|Contract|Only|Remote)`
- `([A-Z][a-zA-Z\s]+(?:Developer|Engineer|Manager|Analyst|Specialist|Assistant|Designer))[^.\n]*?See Details`
- `([A-Z][a-zA-Z\s]+(?:Developer|Engineer|Manager|Analyst|Specialist|Assistant|Designer))[^.\n]*?(?:Singapore|Remote|Fully Remote)`

### Location Patterns
- `Singapore Only` - Singapore-based jobs
- `Fully Remote` - Remote work
- `Remote` - Remote work
- `nơi làm việc[:\s]+([^\n]+)` - Vietnamese location
- `location[:\s]+([^\n]+)` - English location
- `địa điểm[:\s]+([^\n]+)` - Vietnamese location
- `work location[:\s]+([^\n]+)` - English work location

### Job Type Patterns
- `Full-time` - Full-time employment
- `Part-time` - Part-time employment
- `Contract` - Contract work
- `Full Time` - Full-time employment (alternative)
- `Part Time` - Part-time employment (alternative)

### Action Button Patterns
- `See Details` - Common for job cards
- `Apply now` - Apply button
- `View` - View details
- `Learn` - Learn more
- `Xem Thêm` - Vietnamese "See more"

## Site-Specific Patterns (Legacy - Should be removed)

### Migitek Patterns
- `Java Web Developer.*?Apply now`
- `Full Stack Developer.*?Apply now`
- `C\+\+ Developer.*?Apply now`
- `Java Developer Spring Boot.*?Apply now`
- `Tester.*?Apply now`
- `Business Analyst.*?Apply now`
- `Human Resource.*?Apply now`

### Co-well Patterns
- `Java Developer \(Onsite\).*?Xem Thêm`
- `Senior Sales IT \(Người Nhật\).*?Xem Thêm`
- `Senior Sales IT.*?Xem Thêm`
- `AI Engineer \(Part-time\).*?Xem Thêm`
- `Java Developer.*?Full Time.*?Xem Thêm`
- `Senior Sales.*?Full Time.*?Xem Thêm`
- `AI Engineer.*?Part Time.*?Xem Thêm`

### Code Tốt Patterns
- `\[Remote-HN\]\s+([^-\n]+)`
- `\[Remote\]\s+([^-\n]+)`
- `Tuyển dụng.*?(\d{2}/\d{2}/\d{4}):\s*([^-\n]+)`
- `(\d{2}/\d{2}/\d{4}):\s*([^-\n]+)`
- `([A-Z][^-\n]*(?:Developer|Engineer|Manager|Analyst|Specialist|Marketing|Test|Freelancer|Assistant|Intern))`

## Universal Job Card Selectors

### HTML Selectors
- `article` - Common for job cards
- `.job-card`, `.jobcard`, `.job-item`, `.jobitem`
- `.career-item`, `.career-card`, `.position-item`
- `.vacancy-item`, `.opportunity-item`
- `[class*="job"]`, `[class*="career"]`, `[class*="position"]`
- `[class*="vacancy"]`, `[class*="opportunity"]`

### Title Selectors
- `h1`, `h2`, `h3`, `h4`
- `.title`, `.job-title`, `.position-title`

### Description Selectors
- `.description`, `.job-description`, `.content`
- `p` - Paragraph text

## Best Practices

1. **No Hardcoding**: Never hardcode company-specific patterns
2. **Universal Patterns**: Use general patterns that work across sites
3. **Fallback Logic**: Always have fallback patterns for unknown sites
4. **Pattern Testing**: Test patterns against multiple sites before deployment
5. **Maintainability**: Keep patterns in external configuration files

## Pattern Testing

Before adding new patterns:
1. Test against known working sites
2. Test against new sites
3. Verify no false positives
4. Ensure patterns are generic enough
5. Document pattern purpose and usage
