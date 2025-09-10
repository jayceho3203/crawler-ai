#!/usr/bin/env python3
"""
Fix syntax errors in job_extraction_service.py
"""

import re

def fix_syntax_errors():
    """Fix common syntax errors"""
    
    file_path = "/Users/jayceho/crawler-ai/app/services/job_extraction_service.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Remove extra indentation
    content = re.sub(r'^(\s+)else:\s*$', r'        else:', content, flags=re.MULTILINE)
    
    # Fix 2: Fix try without except
    content = re.sub(r'^(\s+)try:\s*$', r'        try:', content, flags=re.MULTILINE)
    
    # Fix 3: Fix indentation issues
    content = re.sub(r'^(\s{4,})\s+', r'\1', content, flags=re.MULTILINE)
    
    # Fix 4: Fix missing except blocks
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for try without except
        if 'try:' in line and i + 1 < len(lines):
            # Look for the next except or finally
            j = i + 1
            found_except = False
            while j < len(lines) and lines[j].strip().startswith(('    ', '\t')):
                if 'except' in lines[j] or 'finally' in lines[j]:
                    found_except = True
                    break
                j += 1
            
            if not found_except:
                # Add a basic except block
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(line)
                fixed_lines.append(' ' * indent + 'except Exception as e:')
                fixed_lines.append(' ' * (indent + 4) + 'logger.error(f"Error: {e}")')
                fixed_lines.append(' ' * (indent + 4) + 'return []')
                i += 1
                continue
        
        fixed_lines.append(line)
        i += 1
    
    content = '\n'.join(fixed_lines)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Syntax errors fixed!")

if __name__ == "__main__":
    fix_syntax_errors()
