#!/usr/bin/env python3
"""
Examine Civitai model page structure to understand the mantime-accordion-root.
This script will help us understand what data is available for extraction.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from browser_agent.server.browser_client import BrowserClient

from rich import print
from rich.console import Console
from rich.panel import Panel

console = Console()


def examine_model_page(model_url: str):
    """Examine a Civitai model page structure."""
    client = BrowserClient()
    
    # Check server connection
    print("[bold]Step 1:[/bold] Connecting to browser server...")
    result = client.ping()
    if result.get("status") != "success":
        print("[red]✗ Could not connect to browser server[/red]")
        print("[yellow]Please start the server first:[/yellow]")
        print("  python examples/civitai/browser_server.py /usr/bin/brave-browser")
        sys.exit(1)
    print("[green]✓ Connected[/green]")
    
    # Navigate to the model page
    print(f"\n[bold]Step 2:[/bold] Navigating to {model_url}...")
    result = client.goto(model_url)
    if result.get("status") != "success":
        print(f"[red]✗ Navigation failed: {result.get('message')}[/red]")
        sys.exit(1)
    
    print(f"[green]✓ Loaded: {result.get('title')}[/green]")
    
    # Wait for page to load
    print("\n[bold]Step 3:[/bold] Waiting for content to load...")
    import time
    time.sleep(3)
    
    # Look for the accordion root
    print("\n[bold]Step 4:[/bold] Searching for mantime-accordion-root...")
    
    # Try to find accordion elements
    selectors = [
        '[class*="accordion"]',
        '[class*="Accordion"]',
        '[data-accordion]',
        '[role="region"]',
        'div[class*="mantime"]',
    ]
    
    for selector in selectors:
        print(f"[dim]  Trying: {selector}[/dim]")
        result = client.extract_html(selector)
        if result.get("status") == "success" and result.get("html"):
            print(f"[green]  ✓ Found content with {selector}[/green]")
            html = result.get("html", "")
            print(f"[dim]    Length: {len(html)} chars[/dim]")
            
            # Save to file for inspection
            output_dir = Path("outputs/civitai")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            safe_selector = selector.replace('[', '').replace(']', '').replace('"', '').replace('*', 'wildcard')
            output_file = output_dir / f"accordion_{safe_selector}.html"
            with output_file.open('w', encoding='utf-8') as f:
                f.write(html)
            print(f"[dim]    Saved to: {output_file}[/dim]")
    
    # Try to get the full page HTML to search for "mantime"
    print("\n[bold]Step 5:[/bold] Extracting full page HTML...")
    result = client.extract_html("body")
    if result.get("status") == "success":
        html = result.get("html", "")
        print(f"[green]✓ Got page HTML ({len(html)} chars)[/green]")
        
        # Search for "mantime" in the HTML
        if "mantime" in html.lower():
            print("[green]  ✓ Found 'mantime' in page HTML[/green]")
            
            # Find all occurrences
            import re
            matches = re.finditer(r'mantime[^"]*', html, re.IGNORECASE)
            unique_matches = set()
            for match in matches:
                unique_matches.add(match.group())
            
            print(f"  Found {len(unique_matches)} unique 'mantime' references:")
            for match in sorted(unique_matches):
                print(f"    - {match}")
        else:
            print("[yellow]  ⚠ 'mantime' not found in HTML[/yellow]")
        
        # Save full HTML for manual inspection
        output_file = Path("outputs/civitai/full_page.html")
        with output_file.open('w', encoding='utf-8') as f:
            f.write(html)
        print(f"[dim]  Saved full HTML to: {output_file}[/dim]")
    
    # Try to extract information from specific sections
    print("\n[bold]Step 6:[/bold] Looking for model information...")
    
    # Try common Civitai selectors
    info_selectors = {
        "Model Name": 'h1',
        "Version Info": '[class*="version"]',
        "Stats": '[class*="stat"]',
        "Description": '[class*="description"]',
        "Model Details": 'dl, [role="list"]',
    }
    
    for name, selector in info_selectors.items():
        result = client.extract_html(selector)
        if result.get("status") == "success" and result.get("html"):
            html = result.get("html", "")
            if len(html) < 500:
                print(f"\n[cyan]{name}:[/cyan]")
                print(f"[dim]{html[:200]}...[/dim]" if len(html) > 200 else f"[dim]{html}[/dim]")
    
    print("\n[bold green]✓ Examination complete![/bold green]")
    print("[dim]Check outputs/civitai/ for saved HTML files[/dim]")


def main():
    if len(sys.argv) < 2:
        print("[red]Usage: examine_civitai.py <model_url>[/red]")
        print("\nExample:")
        print("  python examples/civitai/examine_civitai.py 'https://civitai.com/models/277058?modelVersionId=1920523'")
        print("\n[yellow]Note: The browser server must be running and you must be logged in![/yellow]")
        print("  python examples/civitai/browser_server.py /usr/bin/brave-browser")
        sys.exit(1)
    
    model_url = sys.argv[1]
    examine_model_page(model_url)


if __name__ == "__main__":
    main()
