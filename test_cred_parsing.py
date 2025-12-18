#!/usr/bin/env python3
"""Debug script to test credentials file parsing."""

from src.browser_agent.comfyui.cli import parse_credentials_file
from pathlib import Path

cred_file = "vastai_credentials.txt"
print(f"File exists: {Path(cred_file).exists()}")
print(f"File path: {Path(cred_file).absolute()}")

data = parse_credentials_file(cred_file)
print(f"\nParsed data:")
for key, value in data.items():
    print(f"  {key}: {value}")

print(f"\nHas URL: {'url' in data}")
if 'url' in data:
    print(f"URL value: {data['url']}")
