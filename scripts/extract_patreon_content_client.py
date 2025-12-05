#!/usr/bin/env python3
"""
Extract Patreon post content using the persistent browser server.
This script extracts the description HTML from individual posts in a collection.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from browser_client import BrowserClient
from rich import print


def load_collection_data(collection_id: str) -> dict:
    """Load the collection links from the JSON file."""
    output_dir = Path("outputs")
    output_file = output_dir / f"patreon_collection_{collection_id}.json"
    
    if not output_file.exists():
        raise FileNotFoundError(
            f"Collection data not found: {output_file}\n"
            f"Please run extract_patreon_collection.py or extract_patreon_client.py first."
        )
    
    with output_file.open('r') as f:
        return json.load(f)


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be used as a filename."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    if len(name) > 100:
        name = name[:100]
    
    return name.strip()


def extract_collection_name(client: BrowserClient, collection_id: str) -> str:
    """Extract the collection name from the collection page."""
    collection_url = f"https://www.patreon.com/collection/{collection_id}?view=expanded"
    
    # Navigate to collection page
    result = client.goto(collection_url)
    if result.get("status") != "success":
        return f"collection_{collection_id}"
    
    time.sleep(2)  # Wait for page to load
    
    # Try to get page title which usually contains collection name
    info = client.info()
    if info.get("status") == "success":
        title = info.get("title", "")
        if title and "Patreon" in title:
            # Extract collection name from title (format: "Collection Name | Patreon")
            name = title.split("|")[0].strip()
            if name:
                return sanitize_filename(name)
    
    return f"collection_{collection_id}"


def extract_post_content(client: BrowserClient, post_url: str, collection_name: str) -> dict | None:
    """Extract description HTML from a post."""
    print(f"\n[cyan]→[/cyan] Navigating to post...")
    result = client.goto(post_url)
    if result.get("status") != "success":
        print(f"[red]✗ Navigation failed: {result.get('message')}[/red]")
        return None
    
    print(f"[dim]  Title: {result.get('title', 'Unknown')}[/dim]")
    
    # Wait for content to load
    print(f"[cyan]→[/cyan] Waiting for content...")
    result = client.wait('div[class*="cm-"]', timeout=10000)
    if result.get("status") != "success":
        print(f"[yellow]⚠ Timeout waiting for content (proceeding anyway)[/yellow]")
    
    # Try multiple selectors to extract description HTML
    description_selectors = [
        'div[class*="cm-LIiDtl"]',  # Main content div
        'div[data-tag="post-content"]',  # Alternative
        'article div[class*="cm-"]',  # Article content
        '[data-tag="post-card"] div[class*="cm-"]',  # Post card content
        'div[class*="cm-wHoaYV"]',  # Another common content class
        'article',  # Fallback to article
    ]
    
    html_content = ""
    for selector in description_selectors:
        print(f"[dim]  Trying selector: {selector}[/dim]")
        result = client.extract_html(selector)
        if result.get("status") == "success":
            html_content = result.get("html", "")
            if html_content and len(html_content) > 100:  # Must have substantial content
                print(f"[green]✓ Found content using selector: {selector}[/green]")
                print(f"[dim]  Length: {len(html_content)} characters[/dim]")
                break
            elif html_content:
                print(f"[dim]  Found minimal content ({len(html_content)} chars), trying next selector[/dim]")
        else:
            print(f"[dim]  Selector failed: {result.get('message', 'unknown error')}[/dim]")
    
    if not html_content or len(html_content) < 100:
        print(f"[red]✗ Could not extract HTML content[/red]")
        print(f"[yellow]Debug info:[/yellow]")
        # Get page info for debugging
        info = client.info()
        if info.get("status") == "success":
            print(f"  Current URL: {info.get('url')}")
            print(f"  Page title: {info.get('title')}")
        print(f"[yellow]Tip: Manually inspect the page to find the correct selector[/yellow]")
        return None
    
    # Get page info for metadata
    info = client.info()
    
    return {
        "html": html_content,
        "title": info.get("title", "Unknown") if info.get("status") == "success" else "Unknown",
        "url": info.get("url", post_url) if info.get("status") == "success" else post_url
    }


def save_post_content(post_id: str, post_name: str, post_url: str, collection_id: str, content: dict):
    """Save post content to files."""
    # Create folder name: POST_<POST_ID>_<POST_NAME>
    folder_name = f"POST_{post_id}_{sanitize_filename(post_name)}"
    output_dir = Path("outputs") / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save HTML file
    html_file = output_dir / f"{post_id}-desc.html"
    with html_file.open('w', encoding='utf-8') as f:
        f.write(content["html"])
    
    print(f"[green]✓ Saved HTML to {html_file}[/green]")
    
    # Save metadata
    metadata = {
        "post_id": post_id,
        "post_url": post_url,
        "collection_id": collection_id,
        "post_name": post_name,
        "title": content["title"],
        "html_length": len(content["html"])
    }
    
    metadata_file = output_dir / f"{post_id}-meta.json"
    with metadata_file.open('w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"[dim]✓ Saved metadata to {metadata_file}[/dim]")


def main():
    if len(sys.argv) < 2:
        print("[red]Usage: extract_patreon_content_client.py <collection_id> [post_index_or_url][/red]")
        print("\nExamples:")
        print("  # Extract from first post")
        print("  python scripts/extract_patreon_content_client.py 1611241")
        print("")
        print("  # Extract from specific post index (0-based)")
        print("  python scripts/extract_patreon_content_client.py 1611241 5")
        print("")
        print("  # Extract from specific post URL")
        print("  python scripts/extract_patreon_content_client.py 1611241 https://www.patreon.com/posts/144726506")
        print("")
        print("[yellow]Note: The browser server must be running first![/yellow]")
        print("  python scripts/browser_server.py /usr/bin/brave-browser")
        sys.exit(1)
    
    collection_id = sys.argv[1]
    post_selector = sys.argv[2] if len(sys.argv) > 2 else "0"
    
    print(f"[bold cyan]Patreon Content Extractor (Client Mode)[/bold cyan]")
    print(f"Collection ID: {collection_id}\n")
    
    # Connect to browser server
    client = BrowserClient()
    
    print("[bold]Step 1:[/bold] Connecting to browser server...")
    result = client.ping()
    if result.get("status") != "success":
        print(f"[red]✗ Could not connect to browser server[/red]")
        print("[yellow]Start the server first:[/yellow]")
        print("  python scripts/browser_server.py /usr/bin/brave-browser")
        return
    print("[green]✓ Connected to browser server[/green]")
    
    # Load collection data
    print("\n[bold]Step 2:[/bold] Loading collection data...")
    try:
        collection_data = load_collection_data(collection_id)
    except FileNotFoundError as e:
        print(f"[red]✗ {e}[/red]")
        return
    
    links = collection_data.get("links", [])
    if not links:
        print("[red]✗ No links found in collection data[/red]")
        return
    
    print(f"[green]✓ Loaded {len(links)} posts[/green]")
    
    # Determine which post to extract
    if post_selector.startswith("http"):
        post_url = post_selector
        print(f"[dim]  Using URL: {post_url}[/dim]")
    else:
        try:
            post_index = int(post_selector)
            if post_index < 0 or post_index >= len(links):
                print(f"[red]✗ Invalid post index: {post_index}. Valid range: 0-{len(links)-1}[/red]")
                return
            post_url = links[post_index]
            print(f"[dim]  Using post {post_index + 1}/{len(links)}: {post_url}[/dim]")
        except ValueError:
            print(f"[red]✗ Invalid post selector: {post_selector}[/red]")
            return
    
    # Extract post ID from URL
    post_id = post_url.split("/posts/")[1].split("?")[0] if "/posts/" in post_url else "unknown"
    
    # Extract post content first to get the post name/title
    print(f"\n[bold]Step 3:[/bold] Extracting post content...")
    content = extract_post_content(client, post_url, "")
    
    if not content:
        print("[red]✗ Failed to extract content[/red]")
        return
    
    # Extract post name from title (remove " | Patreon" suffix)
    post_title = content.get("title", "Unknown")
    post_name = post_title.split("|")[0].strip() if "|" in post_title else post_title
    
    # Save content
    print(f"\n[bold]Step 4:[/bold] Saving content...")
    save_post_content(post_id, post_name, post_url, collection_id, content)
    
    print(f"\n[bold green]✓ Extraction complete![/bold green]")
    folder_name = f"POST_{post_id}_{sanitize_filename(post_name)}"
    print(f"[dim]Output: outputs/{folder_name}/{post_id}-desc.html[/dim]")


if __name__ == "__main__":
    # Add parent directory to path to import browser_client
    sys.path.insert(0, str(Path(__file__).parent))
    main()
