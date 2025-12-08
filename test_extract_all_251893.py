#!/usr/bin/env python3
"""Extract all posts from collection 251893 by scrolling to load more."""

from browser_agent.server import BrowserClient
import json
import time

def extract_all_posts():
    """Extract all posts by scrolling to load more content."""
    client = BrowserClient(port=9999)
    
    print("Testing connection...")
    result = client.ping()
    if result.get("status") != "success":
        print("ERROR: Could not connect to browser server!")
        return
    
    print("\nScrolling to load all posts...")
    
    # JavaScript to scroll and extract links
    scroll_and_extract_js = """
    (async () => {
        const scrollDelay = 1000;  // Wait 1 second between scrolls
        const maxScrolls = 50;      // Maximum number of scrolls
        let lastHeight = document.body.scrollHeight;
        let scrollCount = 0;
        let noChangeCount = 0;
        
        // Initial scroll to bottom
        window.scrollTo(0, document.body.scrollHeight);
        
        while (scrollCount < maxScrolls && noChangeCount < 3) {
            await new Promise(resolve => setTimeout(resolve, scrollDelay));
            
            let newHeight = document.body.scrollHeight;
            if (newHeight === lastHeight) {
                noChangeCount++;
            } else {
                noChangeCount = 0;
                lastHeight = newHeight;
            }
            
            window.scrollTo(0, document.body.scrollHeight);
            scrollCount++;
        }
        
        // Extract all unique post links
        const links = Array.from(document.querySelectorAll('a[href*="/posts/"]'))
            .map(a => a.href)
            .filter(href => href.match(/\\/posts\\/\\d+/))
            .filter((href, index, self) => self.indexOf(href) === index);
        
        return {
            scrollCount: scrollCount,
            linksFound: links.length,
            links: links
        };
    })();
    """
    
    print("Executing scroll and extract script (this may take a minute)...")
    result = client.eval_js(scroll_and_extract_js)
    
    if result.get("status") == "success":
        data = result.get("result", {})
        links = data.get("links", [])
        scroll_count = data.get("scrollCount", 0)
        
        print(f"\n✓ Scrolled {scroll_count} times")
        print(f"✓ Found {len(links)} unique post links")
        
        # Save to file
        output_file = "outputs/patreon_collection_251893.json"
        with open(output_file, "w") as f:
            json.dump(links, f, indent=2)
        print(f"✓ Saved links to {output_file}")
        
        # Show some sample links
        print("\nFirst 5 links:")
        for i, link in enumerate(links[:5], 1):
            print(f"  {i}. {link}")
        
        if len(links) > 5:
            print(f"\n... and {len(links) - 5} more")
        
        return links
    else:
        print(f"ERROR: {result.get('message')}")
        return None

if __name__ == "__main__":
    links = extract_all_posts()
    if links:
        print(f"\n🎉 Successfully extracted {len(links)} posts from collection 251893")
    else:
        print("\n✗ Failed to extract collection")
