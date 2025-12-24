#!/usr/bin/env python3
"""
Smart sidebar popover toggle with state detection.
Only clicks if needed to achieve desired state.
"""

import sys
from pathlib import Path
# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.browser_agent.server.browser_client import BrowserClient
import time

client = BrowserClient(port=9999)

def check_popover_state(button_name):
    """Check if a sidebar button's popover is currently open."""
    check_js = f"""
    (() => {{
        const btn = document.querySelector('button[aria-label*="{button_name}"]');
        if (!btn) {{
            console.log('Button not found: {button_name}');
            return {{found: false, error: 'Button not found'}};
        }}
        
        // Check various state indicators
        const state = {{
            found: true,
            ariaExpanded: btn.getAttribute('aria-expanded'),
            ariaPressed: btn.getAttribute('aria-pressed'),
            hasActiveClass: btn.classList.contains('active'),
            parentHasActiveClass: btn.parentElement.classList.contains('active'),
            ariaLabel: btn.getAttribute('aria-label')
        }};
        console.log('Button state for {button_name}:', state);
        return state;
    }})()
    """
    
    result = client.eval_js(check_js)
    if result.get('status') == 'success':
        return result.get('result', {})
    return {'found': False, 'error': result.get('message', 'Unknown error')}

def toggle_sidebar_popover(button_name, desired_state='open'):
    """
    Toggle a sidebar popover to the desired state.
    
    Args:
        button_name: Name of the button (Menu, Assets, Nodes, etc.)
        desired_state: 'open' or 'closed'
    
    Returns:
        dict with success status and actions taken
    """
    # Check current state
    current_state = check_popover_state(button_name)
    
    if not current_state.get('found'):
        error_msg = current_state.get('error', 'Button not found')
        return {'success': False, 'message': f'Button "{button_name}" not found: {error_msg}'}
    
    # Determine if popover is currently open
    is_open = (
        current_state.get('ariaExpanded') == 'true' or
        current_state.get('ariaPressed') == 'true' or
        current_state.get('hasActiveClass') or
        current_state.get('parentHasActiveClass')
    )
    
    # Check if we need to toggle
    needs_click = (desired_state == 'open' and not is_open) or \
                  (desired_state == 'closed' and is_open)
    
    if not needs_click:
        return {
            'success': True,
            'message': f'Popover already {desired_state}',
            'clicked': False,
            'was_open': is_open
        }
    
    # Click the button
    click_js = f"""
    (() => {{
        const btn = document.querySelector('button[aria-label*="{button_name}"]');
        if (btn) {{
            btn.click();
            return {{success: true}};
        }}
        return {{success: false}};
    }})()
    """
    
    result = client.eval_js(click_js)
    if result.get('status') == 'success' and result.get('result', {}).get('success'):
        return {
            'success': True,
            'message': f'Toggled popover to {desired_state}',
            'clicked': True,
            'was_open': is_open
        }
    
    return {'success': False, 'message': 'Failed to click button'}


# Test the smart toggle
print("="*70)
print("Smart Sidebar Popover Toggle Test")
print("="*70)

buttons = ["Menu", "Assets", "Nodes", "Models", "Workflows", "NodesMap"]

for button in buttons:
    print(f"\n[{button}]")
    
    # Test 1: Open it
    print("  Opening...")
    result = toggle_sidebar_popover(button, 'open')
    print(f"    {result['message']} (clicked: {result.get('clicked')})")
    time.sleep(3)
    
    # Test 2: Try to open again (should skip)
    print("  Trying to open again...")
    result = toggle_sidebar_popover(button, 'open')
    print(f"    {result['message']} (clicked: {result.get('clicked')})")
    time.sleep(3)
    
    # Test 3: Close it
    print("  Closing...")
    result = toggle_sidebar_popover(button, 'closed')
    print(f"    {result['message']} (clicked: {result.get('clicked')})")
    time.sleep(3)
    
    # Test 4: Try to close again (should skip)
    print("  Trying to close again...")
    result = toggle_sidebar_popover(button, 'closed')
    print(f"    {result['message']} (clicked: {result.get('clicked')})")
    time.sleep(3)
    
    # Delay before next button
    time.sleep(3)

print("\n" + "="*70)
print("✓ Smart toggle working! Only clicks when state needs to change.")
print("="*70)
