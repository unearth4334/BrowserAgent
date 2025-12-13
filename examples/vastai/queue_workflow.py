#!/usr/bin/env python3
"""
Queue workflow executions in ComfyUI.

This script sets the batch count and clicks the run button to queue executions.
"""
from pathlib import Path
import sys
import time

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from browser_agent.server.browser_client import BrowserClient


def queue_workflow(client: BrowserClient, num_iterations: int = 1):
    """Queue workflow executions by setting batch count and clicking run."""
    print(f"🎬 Queueing {num_iterations} workflow execution(s)")
    
    # Step 1: Set the batch count if not 1
    if num_iterations != 1:
        print(f"   1. Setting batch count to {num_iterations}...")
        
        # First, clear the current value and set the new one
        set_batch_js = f"""
        (function() {{
            const input = document.querySelector('.batch-count input.p-inputnumber-input');
            if (!input) return 'Batch count input not found';
            
            // Clear and set new value
            input.value = '{num_iterations}';
            
            // Trigger input event to update the component
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            
            return 'Set to ' + input.value;
        }})()
        """
        result = client.eval_js(set_batch_js)
        if result.get("status") != "success":
            print(f"   ❌ Failed to set batch count: {result.get('message')}")
            return False
        
        set_result = result.get("result", "")
        if not set_result.startswith("Set to"):
            print(f"   ❌ Failed to set batch count: {set_result}")
            return False
        
        print(f"      {set_result}")
        time.sleep(1)  # Wait for UI to process the input change
    else:
        print(f"   1. Batch count already set to 1, skipping...")
    
    # Step 2: Click the Run button
    print(f"   2. Clicking Run button...")
    run_button_js = """
    (function() {
        const runButton = document.querySelector('.comfyui-queue-button button.p-splitbutton-button');
        if (!runButton) return 'Run button not found';
        
        // Check if button is disabled
        if (runButton.disabled) return 'Run button is disabled';
        
        runButton.click();
        return 'Clicked';
    })()
    """
    result = client.eval_js(run_button_js)
    if result.get("status") != "success":
        print(f"   ❌ Failed to click run button: {result.get('message')}")
        return False
    
    click_result = result.get("result", "")
    if click_result == "Run button is disabled":
        print(f"   ⚠️  Run button is disabled - workflow may need inputs set")
        return False
    elif click_result != "Clicked":
        print(f"   ❌ Failed to click run button: {click_result}")
        return False
    
    # Wait a moment and check if anything was queued
    time.sleep(0.5)
    
    # Step 3: Check for error messages or dialogs
    print(f"   3. Checking for errors or dialogs...")
    check_errors_js = """
    (function() {
        // Check for toast messages, dialogs, or error indicators
        const toast = document.querySelector('.p-toast-message, .p-message, [role="alert"]');
        const dialog = document.querySelector('.p-dialog-visible, [role="dialog"][aria-modal="true"]');
        
        if (toast) {
            return {type: 'toast', text: toast.textContent.trim()};
        }
        if (dialog) {
            return {type: 'dialog', text: dialog.textContent.trim().substring(0, 200)};
        }
        return {type: 'none'};
    })()
    """
    result = client.eval_js(check_errors_js)
    if result.get("status") == "success":
        error_check = result.get("result", {})
        if isinstance(error_check, dict) and error_check.get("type") != "none":
            print(f"      ⚠️  {error_check.get('type').title()}: {error_check.get('text', 'Unknown')[:100]}")
    
    # Step 4: Verify items were queued
    print(f"   4. Verifying queue...")
    verify_queue_js = """
    (function() {
        // Look for queue status indicators in various places
        const selectors = [
            '[data-testid="queue-panel"]',
            '.comfyui-queue-panel', 
            '.queue-panel',
            '#queue',
            '.p-panel:has([data-testid="queue-item"])',
            '.p-datatable'
        ];
        
        for (const sel of selectors) {
            const panel = document.querySelector(sel);
            if (panel) {
                const items = panel.querySelectorAll('[data-testid="queue-item"], .queue-item, .p-datatable-tbody tr, li');
                if (items.length > 0) {
                    return {found: true, selector: sel, count: items.length};
                }
            }
        }
        
        return {found: false, message: 'Queue panel or items not found'};
    })()
    """
    result = client.eval_js(verify_queue_js)
    if result.get("status") == "success":
        verify_result = result.get("result", {})
        if isinstance(verify_result, dict):
            if verify_result.get("found"):
                count = verify_result.get("count", 0)
                selector = verify_result.get("selector", "unknown")
                print(f"      Found {count} item(s) in queue (via {selector})")
            else:
                print(f"      {verify_result.get('message', 'Could not verify queue')}")
    
    print(f"✅ Successfully clicked run button with {num_iterations} iteration(s)")
    print(f"   Note: If workflow has required inputs, they must be set before queuing")
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Queue ComfyUI workflow executions"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9999,
        help="Browser server port (default: %(default)s)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of iterations to queue (default: %(default)s)",
    )
    parser.add_argument(
        "-n",
        type=int,
        dest="iterations",
        help="Shorthand for --iterations",
    )
    
    args = parser.parse_args()
    
    # Create browser client
    client = BrowserClient(port=args.port)
    
    # Check server is running
    ping_result = client.ping()
    if ping_result.get("status") != "success":
        print(f"❌ Browser server not responding on port {args.port}")
        print(f"   Please start the server first: python3 examples/vastai/browser_server.py")
        return 1
    
    # Queue the workflow
    success = queue_workflow(client, args.iterations)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
