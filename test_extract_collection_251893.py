#!/usr/bin/env python3
"""Test script to extract collection 251893 using browser server/client."""

from browser_agent.server import BrowserClient
import json
import time

def extract_collection_251893():
    """Extract posts from Patreon collection 251893."""
    client = BrowserClient(port=9999)
    
    # Test ping
    print("Testing connection...")
    result = client.ping()
    print(f"Ping result: {result}")
    
    if result.get("status") != "success":
        print("ERROR: Could not connect to browser server!")
        return
    
    # Get current page info
    print("\nGetting page info...")
    info = client.info()
    print(f"Current URL: {info.get('url')}")
    print(f"Page title: {info.get('title')}")
    
    # Wait for collection to load
    print("\nWaiting for collection content to load...")
    wait_result = client.wait('div[data-tag="post-card"]', timeout=15000)
    print(f"Wait result: {wait_result}")
    
    # Extract post links using JavaScript
    print("\nExtracting post links...")
    js_code = """
    Array.from(document.querySelectorAll('a[href*="/posts/"]'))
        .map(a => a.href)
        .filter(href => href.match(/\\/posts\\/\\d+/))
        .filter((href, index, self) => self.indexOf(href) === index)
    """
    
    result = client.eval_js(js_code)
    
    if result.get("status") == "success":
        links = result.get("result", [])
        print(f"\nFound {len(links)} unique post links")
        
        # Save to file
        output_file = "outputs/patreon/patreon_collection_251893.json"
        with open(output_file, "w") as f:
            json.dump(links, f, indent=2)
        print(f"Saved links to {output_file}")
        
        # Print first few links
        print("\nFirst 5 links:")
        for i, link in enumerate(links[:5], 1):
            print(f"  {i}. {link}")
        
        return links
    else:
        print(f"ERROR: {result.get('message')}")
        return None

if __name__ == "__main__":
    links = extract_collection_251893()
    if links:
        print(f"\n✓ Successfully extracted {len(links)} posts from collection 251893")
    else:
        print("\n✗ Failed to extract collection")
