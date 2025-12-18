#!/usr/bin/env python3
"""
Fixed diagnostic test for ComfyUI sidebar buttons with correct selectors.
Tests each button by capturing page state before/after and asking for manual verification.

Fixes:
- Menu: Use .comfy-menu-button-wrapper (ComfyUI logo) instead of aria-label
- Models: Use exact aria-label "Model Library (m)" instead of partial match
"""

import sys
from pathlib import Path
from datetime import datetime
import difflib

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.browser_agent.server.browser_client import BrowserClient

# Button definitions with correct selectors
BUTTONS = {
    "Menu": ".comfy-menu-button-wrapper",  # ComfyUI logo button
    "Assets": 'button[aria-label="Assets"]',
    "Nodes": 'button[aria-label="Node Library (n)"]',
    "Models": 'button[aria-label="Model Library (m)"]',  # Exact match
    "Workflows": 'button[aria-label="Workflows (w)"]',
    "NodesMap": 'button[aria-label="NodesMap"]',
}

def capture_page_state(client):
    """Capture full page HTML"""
    js_code = "(() => document.documentElement.outerHTML)()"
    result = client.eval_js(js_code)
    if result.get("status") == "success":
        return result.get("result", "")
    else:
        print(f"Error capturing page: {result.get('message')}")
        return None

def save_state(content, filepath):
    """Save page state to file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Saved: {filepath}")

def generate_diff(old_content, new_content, old_label, new_label):
    """Generate unified diff between two states"""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=old_label,
        tofile=new_label,
        lineterm=''
    )
    
    return ''.join(diff)

def count_diff_changes(diff_text):
    """Count number of lines changed in diff"""
    changes = 0
    for line in diff_text.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            changes += 1
        elif line.startswith('-') and not line.startswith('---'):
            changes += 1
    return changes

def click_element(client, selector):
    """Click an element using JavaScript"""
    js_code = f"""
    (() => {{
        const el = document.querySelector('{selector}');
        if (!el) {{
            return {{success: false, error: 'Element not found: {selector}'}};
        }}
        el.click();
        return {{success: true}};
    }})()
    """
    
    result = client.eval_js(js_code)
    if result.get("status") == "success":
        return result.get("result", {}).get("success", False)
    return False

def capture_and_diff(client, button_name, action, step_num, prev_state, log_dir):
    """Capture page state, generate diff, and save files"""
    import time
    time.sleep(1)  # Wait for changes to settle
    
    new_state = capture_page_state(client)
    if not new_state:
        return None, False
    
    # Save new state
    state_file = log_dir / f"step_{step_num:02d}_{button_name}_{action}_{timestamp}.html"
    save_state(new_state, state_file)
    
    # Generate and save diff
    diff_text = generate_diff(
        prev_state,
        new_state,
        f"previous",
        f"{button_name}_{action}"
    )
    
    diff_file = log_dir / f"diff_{step_num:02d}_{button_name}_{action}_{timestamp}.txt"
    save_state(diff_text, diff_file)
    
    # Count changes
    changes = count_diff_changes(diff_text)
    print(f"  Changes: {changes} lines")
    
    return new_state, True

def test_button(client, button_name, selector, step_num, current_state, log_dir, results):
    """Test a single button (open and close)"""
    print(f"\n{'='*60}")
    print(f"Testing: {button_name}")
    print(f"Selector: {selector}")
    print(f"{'='*60}")
    
    # Test OPEN
    print(f"\nStep {step_num}: Click {button_name} to OPEN")
    if not click_element(client, selector):
        print(f"  ❌ Failed to click {button_name}")
        results.append((button_name, "open", False, 0))
        return current_state, step_num
    
    new_state, success = capture_and_diff(
        client, button_name, "open", step_num, current_state, log_dir
    )
    
    if not success:
        results.append((button_name, "open", False, 0))
        return current_state, step_num
    
    # Manual verification
    user_input = input(f"  Did the {button_name} popover OPEN? (y/n): ").strip().lower()
    verified = user_input == 'y'
    
    diff_file = log_dir / f"diff_{step_num:02d}_{button_name}_open_{timestamp}.txt"
    with open(diff_file) as f:
        changes = count_diff_changes(f.read())
    
    results.append((button_name, "open", verified, changes))
    print(f"  Result: {'✓ PASS' if verified else '✗ FAIL'}")
    
    step_num += 1
    current_state = new_state
    
    # Test CLOSE
    print(f"\nStep {step_num}: Click {button_name} to CLOSE")
    if not click_element(client, selector):
        print(f"  ❌ Failed to click {button_name}")
        results.append((button_name, "close", False, 0))
        return current_state, step_num
    
    new_state, success = capture_and_diff(
        client, button_name, "close", step_num, current_state, log_dir
    )
    
    if not success:
        results.append((button_name, "close", False, 0))
        return current_state, step_num
    
    # Manual verification
    user_input = input(f"  Did the {button_name} popover CLOSE? (y/n): ").strip().lower()
    verified = user_input == 'y'
    
    diff_file = log_dir / f"diff_{step_num:02d}_{button_name}_close_{timestamp}.txt"
    with open(diff_file) as f:
        changes = count_diff_changes(f.read())
    
    results.append((button_name, "close", verified, changes))
    print(f"  Result: {'✓ PASS' if verified else '✗ FAIL'}")
    
    step_num += 1
    
    return new_state, step_num

def main():
    global timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create log directory
    log_dir = Path("outputs/sidebar_diagnostics_fixed")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting ComfyUI Sidebar Diagnostic (FIXED)")
    print(f"Log directory: {log_dir}")
    print(f"Timestamp: {timestamp}")
    
    # Connect to browser
    client = BrowserClient()
    
    # Capture initial state
    print("\nCapturing initial page state...")
    initial_state = capture_page_state(client)
    if not initial_state:
        print("Failed to capture initial state!")
        return
    
    initial_file = log_dir / f"initial_state_{timestamp}.html"
    save_state(initial_state, initial_file)
    
    current_state = initial_state
    step_num = 1
    results = []
    
    # Test each button
    for button_name, selector in BUTTONS.items():
        current_state, step_num = test_button(
            client, button_name, selector, step_num, current_state, log_dir, results
        )
    
    # Generate summary
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for _, _, verified, _ in results if verified)
    
    summary_lines = [
        f"Results Summary (Success Rate: {passed}/{total} = {passed/total*100:.1f}%):",
        ""
    ]
    
    for button_name, action, verified, changes in results:
        status = "✓" if verified else "✗"
        summary_lines.append(
            f"{status} {button_name:12} {action:5} - {changes} lines changed"
        )
    
    summary_text = "\n".join(summary_lines)
    print(summary_text)
    
    # Save summary
    summary_file = log_dir / f"results_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write(summary_text)
    
    print(f"\nSummary saved to: {summary_file}")
    print(f"\nAll diagnostic files saved to: {log_dir}")

if __name__ == "__main__":
    main()
