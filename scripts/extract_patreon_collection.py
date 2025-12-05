#!/usr/bin/env python3
"""
Script to extract Patreon collection links with manual authentication.
This version keeps the browser open and waits for user input between steps.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.browser.actions import Navigate, WaitForSelector, ExtractLinks
from rich import print


def main():
    collection_id = sys.argv[1] if len(sys.argv) > 1 else "1611241"
    browser_exe = sys.argv[2] if len(sys.argv) > 2 else "/usr/bin/brave-browser"
    
    print(f"[bold cyan]Patreon Collection Extractor[/bold cyan]")
    print(f"Collection ID: {collection_id}")
    print(f"Browser: {browser_exe}\n")
    
    controller = PlaywrightBrowserController(
        executable_path=browser_exe,
        headless=False,
    )
    
    try:
        # Step 1: Open Patreon
        print("[bold]Step 1:[/bold] Opening Patreon...")
        controller.start()
        controller.perform(Navigate("https://www.patreon.com"))
        
        # Wait for user to authenticate
        input("\n[yellow]Please log in to Patreon in the browser, then press Enter to continue...[/yellow]\n")
        
        # Step 2: Navigate to collection
        print(f"\n[bold]Step 2:[/bold] Navigating to collection {collection_id}...")
        collection_url = f"https://www.patreon.com/collection/{collection_id}?view=expanded"
        controller.perform(Navigate(collection_url))
        
        # Step 3: Wait for content to load
        print("\n[bold]Step 3:[/bold] Waiting for content to load...")
        try:
            controller.perform(WaitForSelector('a[href*="/posts/"]', timeout_ms=15000))
            print("[green]✓ Content loaded[/green]")
        except Exception as e:
            print(f"[yellow]Warning: Timeout waiting for links. Proceeding anyway...[/yellow]")
        
        # Step 4: Extract links
        print(f"\n[bold]Step 4:[/bold] Extracting links...")
        
        # Try specific pattern first
        selector = f'a[href*="/posts/"][href*="collection={collection_id}"]'
        controller.perform(ExtractLinks(selector))
        links = controller.get_extracted_links()
        
        # If no links found, try broader pattern
        if not links:
            print("[yellow]No links found with collection filter, trying broader search...[/yellow]")
            controller.perform(ExtractLinks('a[href*="/posts/"]'))
            links = controller.get_extracted_links()
        
        # Display results
        print(f"\n[bold green]✓ Found {len(links)} links[/bold green]")
        if links:
            print("\n[bold]Links:[/bold]")
            for i, link in enumerate(links[:20], 1):
                print(f"  {i}. {link}")
            if len(links) > 20:
                print(f"  ... and {len(links) - 20} more")
            
            # Save to file
            output_file = f"patreon_collection_{collection_id}.json"
            output_path = Path(output_file)
            
            obs = controller.get_observation()
            data = {
                "collection_id": collection_id,
                "url": obs.url,
                "count": len(links),
                "links": links
            }
            
            with output_path.open('w') as f:
                json.dump(data, f, indent=2)
            
            print(f"\n[bold green]✓ Saved to {output_file}[/bold green]")
        else:
            print("[red]✗ No links found. The page structure may have changed or the collection is empty.[/red]")
            print("\n[dim]Tips:[/dim]")
            print("  - Verify the collection URL is correct")
            print("  - Check if you have access to this collection")
            print("  - Try inspecting the page HTML manually")
        
        # Keep browser open for inspection
        input("\n[dim]Press Enter to close the browser...[/dim]\n")
        
    except KeyboardInterrupt:
        print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        controller.stop()
        print("[dim]Browser closed[/dim]")


if __name__ == "__main__":
    main()
