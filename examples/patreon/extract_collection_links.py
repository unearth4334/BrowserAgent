#!/usr/bin/env python3
"""
Extract collection links using JavaScript evaluation for more reliable extraction.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from browser_client import BrowserClient
from rich import print


def main():
    collection_id = sys.argv[1] if len(sys.argv) > 1 else "251879"
    
    print(f"[bold cyan]Patreon Collection Link Extractor[/bold cyan]")
    print(f"Collection ID: {collection_id}\n")
    
    client = BrowserClient()
    
    # Check server connection
    print("Connecting to browser server...")
    result = client.ping()
    if result.get("status") != "success":
        print(f"[red]✗ Could not connect to browser server[/red]")
        return
    print("[green]✓ Connected[/green]")
    
    # Navigate to collection
    print(f"\nNavigating to collection {collection_id}...")
    collection_url = f"https://www.patreon.com/collection/{collection_id}?view=expanded"
    result = client.goto(collection_url)
    if result.get("status") != "success":
        print(f"[red]✗ Navigation failed[/red]")
        return
    print(f"[green]✓ Navigated[/green]")
    print(f"[dim]  Title: {result.get('title', 'Unknown')}[/dim]")
    
    # Wait for content
    print("\nWaiting for content...")
    time.sleep(5)
    
    # Click "Load more" repeatedly
    print("\nLoading all items...")
    load_count = 0
    max_loads = 100  # Increase max loads for larger collections
    
    while load_count < max_loads:
        # Try to click Load more button
        result = client.click('button:has-text("Load more")', timeout=3000)
        if result.get("status") == "success":
            load_count += 1
            if load_count % 10 == 0:
                print(f"[dim]  Loaded {load_count} pages...[/dim]")
            time.sleep(2)  # Increase wait time
        else:
            break
    
    if load_count > 0:
        print(f"[green]✓ Loaded {load_count} additional pages[/green]")
    
    # Extract links using JavaScript - return count first to debug
    print("\nExtracting links...")
    
    # First, get the count
    js_count = f"""
    (() => {{
        const anchors = document.querySelectorAll('a[href*="/posts/"][href*="collection={collection_id}"]');
        return anchors.length;
    }})()
    """
    
    result = client.eval_js(js_count)
    if result.get("status") == "success":
        count = result.get("result", 0)
        print(f"[dim]  Found {count} post links on page[/dim]")
    
    # Extract just post IDs to avoid URL encoding issues
    js_code = f"""
    (() => {{
        const postIds = [];
        const anchors = document.querySelectorAll('a[href*="/posts/"][href*="collection={collection_id}"]');
        
        anchors.forEach(a => {{
            const href = a.getAttribute('href');
            if (href && href.includes('/posts/')) {{
                const match = href.match(/\\/posts\\/(\\d+)/);
                if (match && !postIds.includes(match[1])) {{
                    postIds.push(match[1]);
                }}
            }}
        }});
        
        return postIds;
    }})()
    """
    
    result = client.eval_js(js_code)
    
    if result.get("status") == "success":
        post_ids = result.get("result", [])
        
        # Reconstruct URLs from post IDs
        links = [f"https://www.patreon.com/posts/{post_id}?collection={collection_id}" for post_id in post_ids]
        
        print(f"[bold green]✓ Found {len(links)} unique posts[/bold green]")
        
        if links:
            print("\n[bold]First 10 posts:[/bold]")
            for i, link in enumerate(links[:10], 1):
                post_id = link.split("/posts/")[1].split("?")[0] if "/posts/" in link else "?"
                print(f"  {i}. Post {post_id}")
            if len(links) > 10:
                print(f"  ... and {len(links) - 10} more")
            
            # Save to file
            output_dir = Path("outputs/patreon")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"patreon_collection_{collection_id}.json"
            
            data = {
                "collection_id": collection_id,
                "url": collection_url,
                "count": len(links),
                "links": links
            }
            
            with output_file.open('w') as f:
                json.dump(data, f, indent=2)
            
            print(f"\n[bold green]✓ Saved to {output_file}[/bold green]")
        else:
            print("[yellow]⚠ No links found[/yellow]")
    else:
        print(f"[red]✗ Extraction failed: {result.get('message')}[/red]")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
