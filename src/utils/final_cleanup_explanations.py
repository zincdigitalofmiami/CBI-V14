#!/usr/bin/env python3
import re

# Read the file
with open('CBI_V14_COMPLETE_EXECUTION_PLAN.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove code fragments that are still mixed with explanations
lines = content.split('\n')
cleaned_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    
    # Keep explanations (lines starting with **)
    if stripped.startswith('**') and stripped.endswith('**') or (stripped.startswith('**') and ':' in stripped):
        # Check if there's code mixed in after the explanation
        if '#' in line and not '**' in line.split('#')[0]:
            # Code comment mixed in - extract just the explanation part
            explanation_part = line.split('#')[0].strip()
            if explanation_part:
                cleaned_lines.append(explanation_part)
        else:
            cleaned_lines.append(line)
        i += 1
        continue
    
    # Skip code fragments
    is_code = False
    
    # SQL fragments
    if re.match(r'^\s*(CREATE|SELECT|INSERT|UPDATE|DELETE|ALTER|DROP|FROM|WHERE|GROUP|ORDER|LIMIT|UNION|JOIN|WITH|CASE|WHEN|THEN|ELSE|END|AS|IN|AND|OR|COUNT|AVG|STDDEV|ABS|CORR|TIMESTAMP_DIFF|MIN|MAX|UNPIVOT|HAVING|PERCENTILE_CONT|SUM|CROSS JOIN|LEFT JOIN|PARTITION BY|PRIMARY KEY)\s+', stripped, re.IGNORECASE):
        is_code = True
    # SQL column definitions
    elif re.match(r'^\s*\w+\s+(STRING|INT64|DATE|TIMESTAMP|FLOAT64|ARRAY)', stripped, re.IGNORECASE):
        is_code = True
    # SQL comments
    elif stripped.startswith('--') or (stripped.startswith('#') and not stripped.startswith('##')):
        is_code = True
    # Python/bash code
    elif re.match(r'^\s*(def |class |import |from |if |else|elif |while |for |return |print |self\.|try|except|PROJECT|#!/usr/bin|gcloud|npm|curl|echo)', stripped):
        is_code = True
    # Python docstrings
    elif stripped.startswith('"""') or stripped.endswith('"""'):
        is_code = True
    # Code-like fragments
    elif stripped in [')', ');', '}', '},', ']', '],']:
        is_code = True
    # Incomplete SQL/Python (ends with comma/semicolon, short line)
    elif (stripped.endswith(',') or stripped.endswith(';')) and len(stripped) < 80 and not any(kw in stripped for kw in ['**', '|', '- ', '* ', '✅', '❌']):
        is_code = True
    # Variable assignments that look like code
    elif re.match(r'^\s*\w+\s*=\s*["\']', stripped) or re.match(r'^\s*\w+\s*=\s*\d+', stripped):
        if '**' not in line:
            is_code = True
    # Indented code (4+ spaces, not lists or tables)
    elif re.match(r'^[\s]{4,}', line) and not stripped.startswith('-') and not stripped.startswith('*') and '|' not in line:
        if i > 0:
            prev_context = ''.join(lines[max(0, i-3):i])
            if any(kw in prev_context for kw in ['def ', 'class ', 'import ', 'CREATE', 'SELECT', 'FROM', 'export', 'function', 'const', '@']):
                is_code = True
    
    if is_code:
        i += 1
        continue
    
    # Keep everything else
    cleaned_lines.append(line)
    i += 1

# Join and clean up
content = '\n'.join(cleaned_lines)

# Fix explanations that have code fragments appended
content = re.sub(r'(\*\*[^*]+\*\*\.)#\s+[^\n]+', r'\1', content)
content = re.sub(r'(\*\*[^*]+\*\*\.)\s+[A-Z_]+\s*=', r'\1', content)
content = re.sub(r'(\*\*[^*]+\*\*\.)\s+(CREATE|SELECT|FROM|WHERE|INSERT|UPDATE)', r'\1', content, flags=re.IGNORECASE)

# Clean up excessive blank lines
content = re.sub(r'\n{4,}', '\n\n\n', content)

# Ensure dashes around headers
lines = content.split('\n')
final_lines = []
for i, line in enumerate(lines):
    final_lines.append(line)
    
    # If this is a header (## or more), ensure dashes below
    if re.match(r'^#{2,}', line):
        if i < len(lines) - 1 and lines[i+1].strip() != '---':
            final_lines.append('')
            final_lines.append('---')
        elif i < len(lines) - 1 and lines[i+1].strip() == '---':
            # Already has dashes, skip adding
            pass

content = '\n'.join(final_lines)

# Clean up triple dashes
content = re.sub(r'---\n+---\n+---', '---', content)
content = re.sub(r'---\n+---', '---', content)

with open('CBI_V14_COMPLETE_EXECUTION_PLAN.md', 'w', encoding='utf-8') as f:
    f.write(content)

print('Final cleanup complete - removed code fragments from explanations')


