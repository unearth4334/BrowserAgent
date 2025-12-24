#!/usr/bin/env python3
"""
Simple sidebar button clicker - uses Playwright's built-in click functionality.
"""

import sys
from pathlib import Path
# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.browser_agent.server.browser_client import BrowserClient
import time

client = BrowserClient(port=9999)

print("="*70)
print("ComfyUI Sidebar Button Automation Test")
print("="*70)

# List of sidebar buttons to test (by aria-label or text)
buttons = ["Menu", "Assets", "Nodes", "Models", "Workflows", "NodesMap"]

print("\nThis script will programmatically click sidebar buttons.")
print("Watch the browser to see the popovers open and close.\n")

input("Press Enter to start automated clicking...")

for button_name in buttons:
    print(f"\n[{button_name}]")
    print("  Trying to click...")
    
    # Try multiple selector strategies
    selectors = [
        f'button[aria-label*="{button_name}"]',
        f'button[title*="{button_name}"]',
        f'.sidebar-button:has-text("{button_name}")',
        f'button:has-text("{button_name}")'
    ]
    
    clicked = False
    for selector in selectors:
        click_js = f"""
        (() => {{
            const btn = document.querySelector('{selector}');
            if (btn) {{
                btn.click();
                return {{success: true, selector: '{selector}'}};
            }}
            return {{success: false}};
        }})()
        """
        
        result = client.eval_js(click_js)
        if result.get('status') == 'success':
            data = result.get('result', {})
            if data.get('success'):
                print(f"  ✓ Clicked using: {selector}")
                clicked = True
                time.sleep(1)
                
                # Click again to close
                result2 = client.eval_js(click_js)
                print(f"  ✓ Clicked again to close")
                time.sleep(0.5)
                break
    
    if not clicked:
        print(f"  ✗ Could not find button")
    
    # Delay before next button
    time.sleep(1)

print("\n" + "="*70)
print("Complete! Check if the popovers opened and closed correctly.")
print("="*70)
