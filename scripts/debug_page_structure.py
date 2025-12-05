#!/usr/bin/env python3
"""
Debug script to inspect the current page structure in the browser server.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from browser_client import BrowserClient
from rich import print


def main():
    client = BrowserClient()
    
    # Check connection
    result = client.ping()
    if result.get("status") != "success":
        print("[red]✗ Could not connect to browser server[/red]")
        print("[yellow]Start the server first:[/yellow]")
        print("  python scripts/browser_server.py /usr/bin/brave-browser")
        return
    
    print("[green]✓ Connected to browser server[/green]\n")
    
    # Get page info
    info = client.info()
    if info.get("status") == "success":
        print(f"[cyan]Current Page:[/cyan]")
        print(f"  URL: {info.get('url')}")
        print(f"  Title: {info.get('title')}")
        print(f"  Buttons: {info.get('buttons')}")
        print(f"  Inputs: {info.get('inputs')}\n")
    
    # Try to find content divs with various selectors
    print("[cyan]Testing Selectors:[/cyan]\n")
    
    selectors_to_test = [
        'div[class*="cm-LIiDtl"]',
        'div[class*="cm-wHoaYV"]',
        'div[data-tag="post-content"]',
        'article div[class*="cm-"]',
        '[data-tag="post-card"]',
        'article',
        'main',
        'div[class*="post"]',
    ]
    
    for selector in selectors_to_test:
        result = client.eval_js(f"""
            const el = document.querySelector('{selector}');
            if (el) {{
                return {{
                    found: true,
                    tag: el.tagName,
                    classes: el.className,
                    childCount: el.children.length,
                    textLength: el.innerText ? el.innerText.length : 0,
                    htmlLength: el.innerHTML ? el.innerHTML.length : 0
                }};
            }}
            return {{ found: false }};
        """)
        
        if result.get("status") == "success":
            data = result.get("result", {})
            if data.get("found"):
                print(f"[green]✓[/green] {selector}")
                print(f"  Tag: {data.get('tag')}")
                print(f"  Classes: {data.get('classes', 'none')[:80]}...")
                print(f"  Children: {data.get('childCount')}")
                print(f"  Text: {data.get('textLength')} chars")
                print(f"  HTML: {data.get('htmlLength')} chars")
            else:
                print(f"[red]✗[/red] {selector} - not found")
        else:
            print(f"[yellow]?[/yellow] {selector} - error: {result.get('message')}")
        print()
    
    # Try to get all divs with cm- classes
    print("[cyan]Finding all elements with 'cm-' classes:[/cyan]\n")
    result = client.eval_js("""
        const elements = document.querySelectorAll('div[class*="cm-"]');
        return Array.from(elements).slice(0, 10).map(el => ({
            tag: el.tagName,
            classes: el.className,
            textLength: el.innerText ? el.innerText.length : 0,
            htmlLength: el.innerHTML ? el.innerHTML.length : 0,
            hasContent: el.innerText && el.innerText.length > 100
        }));
    """)
    
    if result.get("status") == "success":
        elements = result.get("result", [])
        print(f"Found {len(elements)} elements (showing first 10):\n")
        for i, el in enumerate(elements, 1):
            content_marker = "📝" if el.get("hasContent") else "  "
            print(f"{content_marker} {i}. {el.get('tag')}")
            print(f"   Classes: {el.get('classes', '')[:80]}...")
            print(f"   Text: {el.get('textLength')} chars, HTML: {el.get('htmlLength')} chars")
            print()
    
    # Suggest the best selector
    print("[cyan]Suggested Selector:[/cyan]")
    result = client.eval_js("""
        const elements = document.querySelectorAll('div[class*="cm-"]');
        let best = null;
        let maxLength = 0;
        
        Array.from(elements).forEach(el => {
            const textLen = el.innerText ? el.innerText.length : 0;
            if (textLen > maxLength && textLen > 500) {
                maxLength = textLen;
                best = el;
            }
        });
        
        if (best) {
            // Try to create a specific selector
            const classes = best.className.split(' ').filter(c => c.startsWith('cm-'));
            return {
                found: true,
                selector: 'div.' + classes[0],
                classes: best.className,
                textLength: best.innerText.length
            };
        }
        return { found: false };
    """)
    
    if result.get("status") == "success":
        data = result.get("result", {})
        if data.get("found"):
            print(f"[green]Best match:[/green] {data.get('selector')}")
            print(f"  Classes: {data.get('classes')}")
            print(f"  Content length: {data.get('textLength')} chars")
            print(f"\n[yellow]Try this command:[/yellow]")
            print(f"  python scripts/extract_patreon_content_client.py 1611241 0")
        else:
            print("[yellow]Could not find a good selector automatically[/yellow]")
            print("[dim]The page might still be loading or have a different structure[/dim]")


if __name__ == "__main__":
    main()
