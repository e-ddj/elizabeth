import fileinput
import sys

# Read the index.py file and fix the blueprint registration
with open('api/index.py', 'r') as f:
    content = f.read()

# Replace /api/hcp with /api/resume-parser
content = content.replace('url_prefix="/api/resume-parser"', 'url_prefix="/api/hcp"')

# Write back
with open('api/index.py', 'w') as f:
    f.write(content)

print("Blueprint registration updated to use /api/hcp")
