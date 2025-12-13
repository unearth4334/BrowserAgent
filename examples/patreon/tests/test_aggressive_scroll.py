#!/usr/bin/env python3
"""Extract all posts using aggressive scrolling with longer waits."""

from browser_agent.server import BrowserClient
import json
import time

def extract_with_aggressive_scroll():
    """Extract all posts using aggressive scrolling."""
    client = BrowserClient(port=9999)
    
    print("Testing connection...")
    result = client.ping()
    if result.get("status") != "success":
        print("ERROR: Could not connect to browser server!")
        return
    
    print("\nStarting aggressive scroll extraction...")
    
    # More aggressive scrolling with longer waits
    scroll_js = """
    (async () => {
        const scrollDelay = 2000;  // Wait 2 seconds between scrolls
        const maxScrolls = 100;     // More scrolls
        let previousCount = 0;
        let stableCount = 0;
        
        for (let i = 0; i < maxScrolls; i++) {
            // Scroll to bottom
            window.scrollTo(0, document.body.scrollHeight);
            
            // Wait for content to load
            await new Promise(resolve => setTimeout(resolve, scrollDelay));
            
            // Count current links
            const currentLinks = document.querySelectorAll('a[href*="/posts/"]');
            const currentCount = currentLinks.length;
            
            console.log(`Scroll ${i + 1}: Found ${currentCount} links`);
            
            // Check if count has stabilized
            if (currentCount === previousCount) {
                stableCount++;
                if (stableCount >= 5) {
                    console.log("Link count stable for 5 iterations, stopping");
                    break;
                }
            } else {
                stableCount = 0;
            }
            
            previousCount = currentCount;
        }
        
        // Extract all unique post links
        const allLinks = Array.from(document.querySelectorAll('a[href*="/posts/"]'))
            .map(a => a.href)
            .filter(href => href.match(/\\/posts\\/\\d+/))
            .filter((href, index, self) => self.indexOf(href) === index);
        
        return {
            totalLinks: allLinks.length,
            links: allLinks
        };
    })();
    """
    
    print("Executing aggressive scroll (this will take 1-2 minutes)...")
    print("Watch the terminal for progress updates...")
    result = client.eval_js(scroll_js)
    
    if result.get("status") == "success":
        data = result.get("result", {})
        links = data.get("links", [])
        
        print(f"\n✓ Found {len(links)} unique post links")
        
        # Save to file
        output_file = "outputs/patreon/patreon_collection_251893.json"
        with open(output_file, "w") as f:
            json.dump(links, f, indent=2)
        print(f"✓ Saved links to {output_file}")
        
        # Show sample
        print("\nFirst 10 links:")
        for i, link in enumerate(links[:10], 1):
            post_id = link.split("/posts/")[1].split("?")[0]
            print(f"  {i}. Post {post_id}")
        
        if len(links) > 10:
            print(f"\n... and {len(links) - 10} more")
        
        return links
    else:
        print(f"ERROR: {result.get('message')}")
        return None

if __name__ == "__main__":
    links = extract_with_aggressive_scroll()
    if links:
        print(f"\n🎉 Successfully extracted {len(links)} posts from collection 251893")
        print(f"   (Collection claims 160 posts, we found {len(links)})")
    else:
        print("\n✗ Failed to extract collection")
