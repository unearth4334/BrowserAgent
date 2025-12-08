#!/usr/bin/env python3
"""
Quick helper to navigate and extract specific elements from Civitai pages.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from browser_agent.server.browser_client import BrowserClient

from rich import print


def main():
    if len(sys.argv) < 3:
        print("[red]Usage: quick_extract.py <url> <selector>[/red]")
        print("\nExample:")
        print("  python examples/civitai/quick_extract.py \\")
        print("    'https://civitai.com/models/277058?modelVersionId=1920523' \\")
        print("    '[class*=\"accordion\"]'")
        sys.exit(1)
    
    url = sys.argv[1]
    selector = sys.argv[2]
    
    client = BrowserClient()
    
    # Navigate
    print(f"[cyan]Navigating to:[/cyan] {url}")
    result = client.goto(url)
    if result.get("status") != "success":
        print(f"[red]Error:[/red] {result.get('message')}")
        sys.exit(1)
    
    # Wait a moment
    import time
    time.sleep(2)
    
    # Extract
    print(f"[cyan]Extracting:[/cyan] {selector}")
    result = client.extract_html(selector)
    if result.get("status") == "success":
        html = result.get("html", "")
        print(f"[green]Success![/green] Extracted {len(html)} characters")
        print("\n" + "="*60)
        print(html)
        print("="*60)
        
        # Save to file
        from pathlib import Path
        output_dir = Path("outputs/civitai")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize selector for filename
        safe_selector = selector.replace('[', '').replace(']', '').replace('"', '').replace('*', 'star').replace('=', 'eq')
        output_file = output_dir / f"extract_{safe_selector}.html"
        output_file.write_text(html)
        print(f"\n[dim]Saved to: {output_file}[/dim]")
    else:
        print(f"[red]Error:[/red] {result.get('message')}")


if __name__ == "__main__":
    main()
