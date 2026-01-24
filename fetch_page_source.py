#!/usr/bin/env python3
"""
Fetch full page source from the API and save it to a file.
This helps identify listitems and other elements in the tileview.
"""

import requests
import json
from datetime import datetime


def fetch_page_source(api_url="http://localhost:5000"):
    """Fetch the full HTML page source from the API."""
    try:
        response = requests.get(f"{api_url}/page-source", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "ok":
            return data.get("html", ""), data.get("length", 0)
        else:
            print(f"❌ API returned error: {data}")
            return None, 0
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch page source: {e}")
        return None, 0


def save_to_file(html_content, filename=None):
    """Save HTML content to a file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"page_source_{timestamp}.html"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Saved page source to: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Failed to save file: {e}")
        return None


def main():
    print("="*80)
    print("FETCH PAGE SOURCE")
    print("="*80)
    
    print("\n🌐 Fetching page source from API...")
    html, length = fetch_page_source()
    
    if html:
        print(f"📊 Received {length:,} bytes of HTML")
        
        # Save to file
        filename = save_to_file(html)
        
        if filename:
            # Print some stats
            lines = html.count('\n') + 1
            print(f"\n📈 File stats:")
            print(f"  - Lines: {lines:,}")
            print(f"  - Size: {length:,} bytes ({length/1024:.1f} KB)")
            
            # Try to count some relevant elements
            print(f"\n🔍 Quick analysis:")
            print(f"  - <div> tags: {html.count('<div')}")
            print(f"  - <li> tags: {html.count('<li')}")
            print(f"  - 'listitem' occurrences: {html.count('listitem')}")
            print(f"  - 'tile' occurrences: {html.count('tile')}")
            print(f"  - 'grid' occurrences: {html.count('grid')}")


if __name__ == "__main__":
    main()
