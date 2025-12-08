#!/usr/bin/env python3
"""
Extract Patreon collection using the persistent browser server.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from browser_client import BrowserClient
from rich import print


def main():
    collection_id = sys.argv[1] if len(sys.argv) > 1 else "1611241"
    
    print(f"[bold cyan]Patreon Collection Extractor (Client Mode)[/bold cyan]")
    print(f"Collection ID: {collection_id}\n")
    
    client = BrowserClient()
    
    # Check server connection
    print("[bold]Step 1:[/bold] Connecting to browser server...")
    result = client.ping()
    if result.get("status") != "success":
        print(f"[red]✗ Could not connect to browser server[/red]")
        print("[yellow]Start the server first:[/yellow]")
        print("  python scripts/browser_server.py /usr/bin/brave-browser")
        return
    print("[green]✓ Connected to browser server[/green]")
    
    # Navigate to collection
    print(f"\n[bold]Step 2:[/bold] Navigating to collection {collection_id}...")
    collection_url = f"https://www.patreon.com/collection/{collection_id}?view=expanded"
    result = client.goto(collection_url)
    if result.get("status") == "success":
        print(f"[green]✓ Navigated to collection[/green]")
        print(f"[dim]  Title: {result.get('title', 'Unknown')}[/dim]")
    else:
        print(f"[red]✗ Navigation failed: {result.get('message')}[/red]")
        return
    
    # Wait for initial content
    print("\n[bold]Step 3:[/bold] Waiting for content to load...")
    result = client.wait('a[href*="/posts/"]', timeout=15000)
    if result.get("status") == "success":
        print("[green]✓ Content loaded[/green]")
    else:
        print(f"[yellow]⚠ Timeout waiting for content (proceeding anyway)[/yellow]")
    
    # Click "Load more" button repeatedly
    print("\n[bold]Step 4:[/bold] Loading all collection items...")
    load_more_count = 0
    max_loads = 50
    
    while load_more_count < max_loads:
        # Try different selectors for the Load more button
        load_more_selectors = [
            'button:has-text("Load more")',
            'button.cm-dupTbP:has-text("Load more")',
            'button[aria-disabled="false"]:has-text("Load more")',
        ]
        
        button_clicked = False
        for selector in load_more_selectors:
            result = client.click(selector, timeout=5000)
            if result.get("status") == "success":
                load_more_count += 1
                print(f"[dim]  Clicked 'Load more' button ({load_more_count} times)[/dim]")
                time.sleep(2)  # Wait for content to load
                button_clicked = True
                break
        
        if not button_clicked:
            # No more buttons found
            break
    
    if load_more_count > 0:
        print(f"[green]✓ Loaded {load_more_count} additional pages[/green]")
    else:
        print("[dim]  No 'Load more' button found or all content already visible[/dim]")
    
    # Extract links
    print(f"\n[bold]Step 5:[/bold] Extracting links...")
    selector = f'a[href*="/posts/"][href*="collection={collection_id}"]'
    result = client.extract(selector)
    
    if result.get("status") == "success":
        links = result.get("links", [])
        print(f"[bold green]✓ Found {len(links)} links[/bold green]")
        
        if links:
            print("\n[bold]Links:[/bold]")
            for i, link in enumerate(links[:20], 1):
                print(f"  {i}. {link}")
            if len(links) > 20:
                print(f"  ... and {len(links) - 20} more")
            
            # Save to file
            output_dir = Path("outputs/patreon")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = f"patreon_collection_{collection_id}.json"
            output_path = output_dir / output_file
            
            info_result = client.info()
            data = {
                "collection_id": collection_id,
                "url": info_result.get("url", collection_url),
                "count": len(links),
                "links": links
            }
            
            with output_path.open('w') as f:
                json.dump(data, f, indent=2)
            
            print(f"\n[bold green]✓ Saved to {output_file}[/bold green]")
        else:
            print("[yellow]⚠ No links found[/yellow]")
    else:
        print(f"[red]✗ Extraction failed: {result.get('message')}[/red]")


if __name__ == "__main__":
    # Add parent directory to path to import browser_client
    sys.path.insert(0, str(Path(__file__).parent))
    main()
