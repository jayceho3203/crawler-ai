#!/usr/bin/env python3
"""
Quick fix syntax errors
"""

def fix_syntax():
    file_path = "/Users/jayceho/crawler-ai/app/services/job_extraction_service.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix common syntax errors
    fixes = [
        # Fix else without if
        ('                else:\n                logger.warning', '            else:\n                logger.warning'),
        ('                else:\n                return await', '            else:\n                return await'),
        ('                else:\n                container_jobs = []', '            else:\n                container_jobs = []'),
        
        # Fix indentation
        ('                    else:\n                    logger.info', '                else:\n                    logger.info'),
        ('                    else:\n                    return False', '                else:\n                    return False'),
        
        # Fix try without except
        ('        try:\n            # Advanced heuristic validation', '        try:\n            # Advanced heuristic validation'),
    ]
    
    for old, new in fixes:
        content = content.replace(old, new)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Quick syntax fixes applied!")

if __name__ == "__main__":
    fix_syntax()
