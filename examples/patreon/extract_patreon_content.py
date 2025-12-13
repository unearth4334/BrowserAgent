#!/usr/bin/env python3
"""
Script to extract content from individual Patreon collection posts.
This script visits each post link from a collection and extracts the description HTML.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.browser.actions import Navigate, WaitForSelector, ExtractHTML, WaitForUser
from rich import print


def load_collection_data(collection_id: str) -> dict:
    """Load the collection links from the JSON file."""
    output_dir = Path("outputs/patreon")
    output_file = output_dir / f"patreon_collection_{collection_id}.json"
    
    if not output_file.exists():
        raise FileNotFoundError(
            f"Collection data not found: {output_file}\n"
            f"Please run extract_patreon_collection.py first to get the collection links."
        )
    
    with output_file.open('r') as f:
        return json.load(f)


def extract_post_title(controller: PlaywrightBrowserController) -> str:
    """Extract the post title from the current page."""
    if not controller._page:
        return "unknown"
    
    try:
        # Try to find the post title element
        title_element = controller._page.query_selector('h1')
        if title_element:
            return title_element.inner_text().strip()
    except Exception:
        pass
    
    # Fallback to page title
    obs = controller.get_observation()
    return obs.title or "unknown"


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be used as a filename."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    # Limit length
    if len(name) > 100:
        name = name[:100]
    
    return name.strip()


def extract_collection_name(controller: PlaywrightBrowserController, collection_id: str) -> str:
    """Extract the collection name from the collection page."""
    try:
        if controller._page:
            # Try to find collection title
            title_element = controller._page.query_selector('h1')
            if title_element:
                title = title_element.inner_text().strip()
                if title:
                    return sanitize_filename(title)
    except Exception:
        pass
    
    # Fallback to collection ID
    return f"collection_{collection_id}"


def main():
    if len(sys.argv) < 2:
        print("[red]Usage: extract_patreon_content.py <collection_id> [browser_exe] [post_index_or_url][/red]")
        print("\nExamples:")
        print("  # Extract from first post in collection")
        print("  python scripts/extract_patreon_content.py 1611241")
        print("")
        print("  # Extract from specific post index (0-based)")
        print("  python scripts/extract_patreon_content.py 1611241 /usr/bin/brave-browser 0")
        print("")
        print("  # Extract from specific post URL")
        print("  python scripts/extract_patreon_content.py 1611241 /usr/bin/brave-browser https://www.patreon.com/posts/144726506")
        sys.exit(1)
    
    collection_id = sys.argv[1]
    browser_exe = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].isdigit() else "/usr/bin/brave-browser"
    post_selector = sys.argv[3] if len(sys.argv) > 3 else (sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].isdigit() else "0")
    
    print(f"[bold cyan]Patreon Content Extractor[/bold cyan]")
    print(f"Collection ID: {collection_id}")
    print(f"Browser: {browser_exe}\n")
    
    # Load collection data
    try:
        collection_data = load_collection_data(collection_id)
    except FileNotFoundError as e:
        print(f"[red]{e}[/red]")
        sys.exit(1)
    
    links = collection_data.get("links", [])
    if not links:
        print("[red]No links found in collection data[/red]")
        sys.exit(1)
    
    # Determine which post to extract
    if post_selector.startswith("http"):
        post_url = post_selector
        print(f"Extracting from URL: {post_url}")
    else:
        try:
            post_index = int(post_selector)
            if post_index < 0 or post_index >= len(links):
                print(f"[red]Invalid post index: {post_index}. Valid range: 0-{len(links)-1}[/red]")
                sys.exit(1)
            post_url = links[post_index]
            print(f"Extracting post {post_index + 1}/{len(links)}: {post_url}")
        except ValueError:
            print(f"[red]Invalid post selector: {post_selector}[/red]")
            sys.exit(1)
    
    # Start browser
    controller = PlaywrightBrowserController(
        executable_path=browser_exe,
        headless=False,
    )
    
    try:
        # Step 1: Open Patreon
        print("\n[bold]Step 1:[/bold] Opening Patreon...")
        controller.start()
        controller.perform(Navigate("https://www.patreon.com"))
        
        # Wait for user to authenticate
        input("\n[yellow]Please log in to Patreon in the browser, then press Enter to continue...[/yellow]\n")
        
        # Step 2: Navigate to post
        print(f"\n[bold]Step 2:[/bold] Navigating to post...")
        controller.perform(Navigate(post_url))
        
        # Step 3: Wait for content to load
        print("\n[bold]Step 3:[/bold] Waiting for content to load...")
        try:
            # Wait for the description content div
            controller.perform(WaitForSelector('div[class*="cm-"]', timeout_ms=10000))
            print("[green]✓ Content loaded[/green]")
        except Exception as e:
            print(f"[yellow]Warning: Timeout waiting for content. Proceeding anyway...[/yellow]")
        
        # Step 4: Extract description HTML
        print("\n[bold]Step 4:[/bold] Extracting description HTML...")
        
        # The description is typically in a div with classes like "cm-LIiDtl cm-wHoaYV cm-mhTrbr cm-LsBaRW"
        # Try multiple selectors to find the description
        description_selectors = [
            'div[class*="cm-LIiDtl"]',  # Main content div
            'div[data-tag="post-content"]',  # Alternative
            'article div[class*="cm-"]',  # Article content
        ]
        
        html_content = ""
        for selector in description_selectors:
            try:
                controller.perform(ExtractHTML(selector))
                html_content = controller.get_extracted_html()
                if html_content:
                    print(f"[green]✓ Found content using selector: {selector}[/green]")
                    break
            except Exception as e:
                print(f"[dim]  Selector {selector} failed: {e}[/dim]")
                continue
        
        if not html_content:
            print("[red]✗ Could not extract description HTML[/red]")
            print("\n[dim]Tips:[/dim]")
            print("  - The page structure may have changed")
            print("  - Try inspecting the page HTML manually")
            print("  - Look for div elements with class names starting with 'cm-'")
            input("\n[dim]Press Enter to close the browser...[/dim]\n")
            return
        
        print(f"[green]✓ Extracted {len(html_content)} characters of HTML[/green]")
        
        # Get post title and extract post name
        post_title = extract_post_title(controller)
        post_name = post_title.split("|")[0].strip() if "|" in post_title else post_title
        
        # Extract post ID from URL
        post_id = post_url.split("/posts/")[1].split("?")[0] if "/posts/" in post_url else "unknown"
        
        # Step 5: Save to file
        print("\n[bold]Step 5:[/bold] Saving to file...")
        
        # Create folder name: POST_<POST_ID>_<POST_NAME>
        folder_name = f"POST_{post_id}_{sanitize_filename(post_name)}"
        output_dir = Path("outputs/patreon") / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save HTML file
        output_file = output_dir / f"{post_id}-desc.html"
        with output_file.open('w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[bold green]✓ Saved to {output_file}[/bold green]")
        
        # Also save metadata
        metadata = {
            "post_id": post_id,
            "post_url": post_url,
            "collection_id": collection_id,
            "post_name": post_name,
            "title": post_title,
            "html_length": len(html_content)
        }
        
        metadata_file = output_dir / f"{post_id}-meta.json"
        with metadata_file.open('w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"[dim]✓ Saved metadata to {metadata_file}[/dim]")
        
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


if __name__ == "__main__":
    main()
