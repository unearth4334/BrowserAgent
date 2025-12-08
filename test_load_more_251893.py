#!/usr/bin/env python3
"""Extract collection 251893 using the Load more button approach."""

from browser_agent.server import BrowserClient
import json
import time

def extract_collection_with_load_more(collection_id="251893"):
    """Extract collection by clicking Load more buttons."""
    client = BrowserClient(port=9999)
    
    print("Testing connection...")
    result = client.ping()
    if result.get("status") != "success":
        print("ERROR: Could not connect to browser server!")
        return None
    
    print(f"\n✓ Connected to browser server")
    
    # Get current page info
    info = client.info()
    print(f"Current URL: {info.get('url')}")
    print(f"Page title: {info.get('title')}")
    
    # Wait for initial content
    print("\nWaiting for content to load...")
    result = client.wait('a[href*="/posts/"]', timeout=15000)
    if result.get("status") == "success":
        print("✓ Content loaded")
    else:
        print("⚠ Timeout waiting for content (proceeding anyway)")
    
    # Click "Load more" button repeatedly
    print("\nLoading all collection items by clicking 'Load more'...")
    load_more_count = 0
    max_loads = 100  # Increased limit
    
    while load_more_count < max_loads:
        # Try different selectors for the Load more button
        load_more_selectors = [
            'button:has-text("Load more")',
            'button.cm-dupTbP:has-text("Load more")',
            'button[aria-disabled="false"]:has-text("Load more")',
            'button:text-is("Load more")',
        ]
        
        button_clicked = False
        for selector in load_more_selectors:
            result = client.click(selector, timeout=3000)
            if result.get("status") == "success":
                load_more_count += 1
                print(f"  Clicked 'Load more' button ({load_more_count} times)")
                time.sleep(2)  # Wait for content to load
                button_clicked = True
                break
        
        if not button_clicked:
            # No more buttons found
            print(f"  No more 'Load more' buttons found after {load_more_count} clicks")
            break
    
    if load_more_count > 0:
        print(f"✓ Loaded {load_more_count} additional pages")
    else:
        print("  No 'Load more' button found or all content already visible")
    
    # Extract all post links
    print(f"\nExtracting post links...")
    
    # Use JavaScript to get all unique post links
    extract_js = f"""
    Array.from(document.querySelectorAll('a[href*="/posts/"]'))
        .map(a => a.href)
        .filter(href => href.includes('/posts/'))
        .filter(href => href.includes('collection={collection_id}'))
        .filter((href, index, self) => self.indexOf(href) === index)
    """
    
    result = client.eval_js(extract_js)
    
    if result.get("status") == "success":
        links = result.get("result", [])
        print(f"✓ Found {len(links)} unique post links")
        
        # Save to file
        output_file = f"outputs/patreon_collection_{collection_id}.json"
        with open(output_file, "w") as f:
            json.dump(links, f, indent=2)
        print(f"✓ Saved links to {output_file}")
        
        # Show sample
        print("\nFirst 10 links:")
        for i, link in enumerate(links[:10], 1):
            post_id = link.split("/posts/")[1].split("?")[0]
            print(f"  {i}. Post {post_id}")
        
        if len(links) > 10:
            print(f"  ... and {len(links) - 10} more")
        
        return links
    else:
        print(f"ERROR: {result.get('message')}")
        return None

if __name__ == "__main__":
    links = extract_collection_with_load_more("251893")
    if links:
        print(f"\n🎉 Successfully extracted {len(links)} posts from collection 251893")
    else:
        print("\n✗ Failed to extract collection")
