#!/usr/bin/env python3
"""
Queue ComfyUI workflow by programmatically loading via file input.

Since the Load button opens a native file dialog (not accessible in headless),
we use Playwright's setInputFiles() to directly set the workflow file.

Usage:
    python3 queue_comfyui_workflow_direct.py [workflow_full_path] [batch_count]
"""
import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from browser_agent.server.browser_server import BrowserServer
from browser_agent.server.browser_client import BrowserClient
import threading


def load_workflow_direct(client: BrowserClient, workflow_file_path: str) -> bool:
    """
    Load workflow by setting file input directly (bypasses file picker dialog).
    
    Args:
        client: Browser client
        workflow_file_path: Absolute path to workflow JSON file on the system
        
    Returns:
        True if successful
    """
    print(f"📂 Loading workflow file: {workflow_file_path}")
    
    # We need to use Playwright's page.setInputFiles() method
    # This requires accessing the page object directly through eval_js
    
    # First, verify the file exists
    if not Path(workflow_file_path).exists():
        print(f"   ❌ File not found: {workflow_file_path}")
        return False
    
    print("   ✅ File exists")
    
    # The challenge: we need to use Playwright's API, not just JavaScript
    # Solution: use a custom command that accesses the page directly
    
    print("   ℹ️  Note: This requires a custom 'load_workflow_file' command")
    print("   ℹ️  Falling back to API-based loading...")
    
    return False


def load_workflow_via_api_call(workflow_file_path: str, comfyui_url: str) -> bool:
    """Load workflow using ComfyUI's loadWorkflow API endpoint."""
    import json
    import requests
    
    print(f"\n📡 Loading workflow via API")
    print(f"   File: {workflow_file_path}")
    
    # Read workflow
    with open(workflow_file_path, 'r') as f:
        workflow_data = json.load(f)
    
    # ComfyUI expects the workflow data to be posted
    # We'll use the /api/workflows endpoint if it exists
    # Otherwise, we can inject it via JavaScript
    
    print("   ℹ️  Direct API loading not available, using JavaScript injection...")
    return False


def queue_workflow_javascript(
    client: BrowserClient,
    workflow_file_path: str,
    batch_count: int = 1
) -> bool:
    """
    Load and queue workflow using JavaScript to inject workflow data.
    
    This reads the workflow JSON and injects it directly into ComfyUI's app state.
    """
    import json
    
    print(f"\n🚀 Loading and queuing workflow via JavaScript injection")
    print(f"   Workflow: {workflow_file_path}")
    print(f"   Batch count: {batch_count}\n")
    
    # Read workflow file
    print("📄 Reading workflow file...")
    with open(workflow_file_path, 'r') as f:
        workflow_data = json.load(f)
    
    # Convert to JSON string for JavaScript (with proper escaping)
    workflow_json = json.dumps(workflow_data)
    # Escape for embedding in JavaScript string
    workflow_json_escaped = workflow_json.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
    
    print(f"   ✅ Loaded workflow with {len(workflow_data.get('nodes', []))} nodes")
    
    # Inject workflow into ComfyUI
    print("\n⚡ Injecting workflow into ComfyUI...")
    
    result = client.eval_js(f"""
    async () => {{
        // Get the ComfyUI app instance
        const app = window.app || window.comfyAPI?.app;
        
        if (!app) {{
            return {{error: 'ComfyUI app instance not found'}};
        }}
        
        // Load the workflow data (parse from JSON string to avoid escaping issues)
        const workflowData = JSON.parse(`{workflow_json_escaped}`);
        
        try {{
            // Use ComfyUI's loadGraphData method
            if (app.loadGraphData) {{
                await app.loadGraphData(workflowData);
                return {{loaded: true, method: 'loadGraphData'}};
            }} else if (app.graph && app.graph.configure) {{
                app.graph.configure(workflowData);
                return {{loaded: true, method: 'graph.configure'}};
            }} else {{
                return {{error: 'No load method found', app_methods: Object.keys(app).slice(0, 20)}};
            }}
        }} catch (e) {{
            return {{error: 'Load failed: ' + e.message}};
        }}
    }}
    """)
    
    if result.get("status") != "success":
        print(f"   ❌ JavaScript execution failed: {result}")
        return False
    
    res_data = result.get("result", {})
    
    if "error" in res_data:
        print(f"   ❌ Failed to load workflow: {res_data}")
        return False
    
    print(f"   ✅ Workflow loaded using: {res_data.get('method', 'unknown')}")
    time.sleep(2)
    
    # Set batch count and queue
    print(f"\n⚡ Queuing workflow (batch: {batch_count})...")
    
    result = client.eval_js(f"""
    () => {{
        // Set batch count
        const inputs = Array.from(document.querySelectorAll('input[type="number"]'));
        const batchInput = inputs.find(i => {{
            const parent = i.closest('.comfy-queue-batch-container');
            return parent !== null;
        }}) || inputs[0];
        
        if (batchInput) {{
            batchInput.value = '{batch_count}';
            batchInput.dispatchEvent(new Event('input', {{bubbles: true}}));
        }}
        
        // Click Queue Prompt
        const buttons = Array.from(document.querySelectorAll('button'));
        const queueBtn = buttons.find(b => b.textContent.includes('Queue Prompt'));
        
        if (!queueBtn) {{
            return {{error: 'Queue button not found'}};
        }}
        
        queueBtn.click();
        return {{queued: true}};
    }}
    """)
    
    if result.get("status") != "success":
        print(f"   ❌ Failed to queue: {result}")
        return False
    
    res_data = result.get("result", {})
    
    if "error" in res_data:
        print(f"   ❌ {res_data}")
        return False
    
    print("   ✅ Workflow queued successfully!")
    return True


def main():
    # Default path on vast.ai
    default_workflow = "/workspace/ComfyUI/user/default/workflows/UmeAiRT/WAN2.2_IMG_to_VIDEO_Base.json"
    
    workflow_path = sys.argv[1] if len(sys.argv) > 1 else default_workflow
    batch_count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    comfyui_url = "http://localhost:18188"
    
    print("🚀 ComfyUI Workflow Queue (JavaScript Injection Method)")
    print(f"   Workflow: {workflow_path}")
    print(f"   Batch count: {batch_count}")
    print(f"   ComfyUI: {comfyui_url}\n")
    
    # Start browser server
    print("⏳ Starting browser server...")
    server = BrowserServer(port=9999, headless=True)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    time.sleep(3)
    
    # Connect client
    client = BrowserClient(port=9999)
    result = client.ready()
    
    if result.get("status") != "success":
        print(f"❌ Failed to connect: {result}")
        return 1
    
    print("✅ Connected to browser\n")
    
    # Navigate to ComfyUI
    print("📍 Navigating to ComfyUI...")
    result = client.goto(comfyui_url)
    if result.get("status") != "success":
        print(f"❌ Navigation failed: {result}")
        return 1
    
    print(f"✅ Navigated to {comfyui_url}")
    time.sleep(3)  # Wait for ComfyUI app to initialize
    
    # Load and queue workflow
    if not queue_workflow_javascript(client, workflow_path, batch_count):
        print("\n❌ Failed to queue workflow")
        return 1
    
    print(f"\n✨ Done! Check ComfyUI at {comfyui_url} to monitor progress\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
