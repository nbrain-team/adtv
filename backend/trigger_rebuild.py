#!/usr/bin/env python3
"""
Script to trigger Render rebuild by making a small change to requirements.txt
This forces Render to reinstall all dependencies including moviepy
"""
import os
import datetime

# Add a comment with timestamp to requirements.txt
requirements_path = 'requirements.txt'

with open(requirements_path, 'r') as f:
    content = f.read()

# Remove any existing rebuild comments
lines = content.split('\n')
filtered_lines = [line for line in lines if not line.startswith('# Rebuild triggered at')]

# Add new rebuild comment
filtered_lines.append(f'# Rebuild triggered at {datetime.datetime.now().isoformat()}')

# Write back
with open(requirements_path, 'w') as f:
    f.write('\n'.join(filtered_lines))

print("Modified requirements.txt to trigger rebuild")
print("Please commit and push this change to trigger Render rebuild") 