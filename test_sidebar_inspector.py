#!/usr/bin/env python3
"""Interactive sidebar inspector for ComfyUI."""

from src.browser_agent.server.browser_client import BrowserClient
import time
import sys

print("Connecting to browser server on port 9999...")
try:
    client = BrowserClient(port=9999)
    ping_result = client.ping()
    if ping_result.get('status') != 'success':
        print(f"Server not responding: {ping_result}")
        sys.exit(1)
    print("✓ Connected to browser server\n")
except Exception as e:
    print(f"✗ Failed to connect: {e}")
    sys.exit(1)

print("="*70)
print("ComfyUI Sidebar Button Inspector")
print("="*70)
print("\nThis script will help you inspect sidebar buttons and popovers.")
print("Follow the prompts to click buttons so we can observe their behavior.\n")

input("Press Enter when ready to start inspection...")

print("\n[1] Finding sidebar buttons...")
sidebar_js = """
(() => {
    const sidebar = document.querySelector('.side-toolbar-container');
    if (!sidebar) return {error: 'Sidebar not found'};
    
    const buttons = [];
    sidebar.querySelectorAll('.sidebar-button').forEach((btn, idx) => {
        buttons.push({
            index: idx,
            title: btn.getAttribute('title') || btn.textContent.trim(),
            id: btn.id || null,
            classes: Array.from(btn.classList)
        });
    });
    
    return {found: true, count: buttons.length, buttons: buttons};
})()
"""

try:
    result = client.eval_js(sidebar_js)
    if result.get('status') == 'success':
        data = result.get('result', {})
        if 'error' in data:
            print(f"❌ {data['error']}")
        else:
            print(f"✓ Found {data.get('count', 0)} sidebar buttons")
            for btn in data.get('buttons', []):
                print(f"  - {btn['title']} (ID: {btn['id']})")
    else:
        print(f"❌ Error: {result.get('message')}")
except Exception as e:
    print(f"❌ Exception: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("[2] Interactive Testing")
print("="*70)

buttons_to_test = ["Menu", "Assets", "Nodes", "Models", "Workflows", "NodesMap"]

for button_name in buttons_to_test:
    print(f"\n\nTesting: {button_name}")
    print("-"*40)
    input(f"👉 Click the '{button_name}' button, then press Enter...")
    
    time.sleep(0.3)
    
    # Check what's visible
    check_js = """
    (() => {
        const visible = [];
        document.querySelectorAll('[class*="popover"], [class*="panel"], [class*="menu"]').forEach(el => {
            if (el.offsetParent !== null) {
                visible.push({
                    tag: el.tagName,
                    classes: Array.from(el.classList).join(' '),
                    id: el.id || 'no-id'
                });
            }
        });
        return {count: visible.length, elements: visible};
    })()
    """
    
    result = client.eval_js(check_js)
    if result.get('status') == 'success':
        data = result.get('result', {})
        print(f"  After opening: {data.get('count', 0)} visible elements")
        for el in data.get('elements', [])[:3]:
            print(f"    - {el['tag']}: {el['classes']}")
    
    input(f"👉 Click '{button_name}' again to close it, then press Enter...")
    time.sleep(0.3)
    
    result = client.eval_js(check_js)
    if result.get('status') == 'success':
        data = result.get('result', {})
        print(f"  After closing: {data.get('count', 0)} visible elements")
    
    # Delay before next button
    time.sleep(1)

print("\n" + "="*70)
print("Inspection Complete!")
print("="*70)
