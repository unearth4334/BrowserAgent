#!/usr/bin/env python3
"""
Queue ComfyUI workflow - hybrid approach.

1. Use browser to load UI format workflow (uses ComfyUI's own converter)
2. Export as API format via JavaScript
3. Queue the converted workflow via HTTP API

This avoids:
- File picker dialog issues (we inject data directly)
- Socket buffer limits (we use HTTP for final queue)
- Manual conversion bugs (ComfyUI does the conversion)

Usage:
    python3 queue_hybrid.py [workflow_path]
"""
import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from browser_agent.server.browser_server import BrowserServer
from browser_agent.server.browser_client import BrowserClient
import threading
import requests


def load_and_export_workflow(
    client: BrowserClient,
    workflow_file_path: str,
    comfyui_url: str
) -> dict:
    """
    Load UI format workflow in browser and export as API format.
    
    Returns API format workflow dict.
    """
    print(f"\n🔄 Loading and converting workflow via browser")
    print(f"   Input: {workflow_file_path}\n")
    
    # Read UI format workflow
    with open(workflow_file_path, 'r') as f:
        ui_workflow = json.load(f)
    
    print(f"   ✅ Read UI workflow ({len(ui_workflow.get('nodes', []))} nodes)")
    
    # Use ComfyUI's built-in conversion by loading it
    # We'll use localStorage or the app API
    
    ui_json_str = json.dumps(ui_workflow)
    
    # Store in localStorage first to avoid size limits
    print("   📦 Storing workflow in browser localStorage...")
    
    # Split into chunks if needed (localStorage has size limits)
    chunk_size = 50000  # 50KB chunks
    chunks = [ui_json_str[i:i+chunk_size] for i in range(0, len(ui_json_str), chunk_size)]
    
    print(f"   Split into {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        # Escape the chunk for JavaScript
        escaped_chunk = chunk.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
        
        result = client.eval_js(f"""
        () => {{
            localStorage.setItem('workflow_chunk_{i}', '{escaped_chunk}');
            return {{stored: true, chunk: {i}, size: '{len(chunk)}'}};
        }}
        """)
        
        if result.get("status") != "success":
            print(f"   ❌ Failed to store chunk {i}: {result}")
            return None
    
    print("   ✅ Stored all chunks")
    
    # Reassemble and load
    print("   ⚡ Loading workflow into ComfyUI...")
    
    result = client.eval_js(f"""
    async () => {{
        // Reassemble chunks
        let fullJson = '';
        for (let i = 0; i < {len(chunks)}; i++) {{
            const chunk = localStorage.getItem('workflow_chunk_' + i);
            if (!chunk) return {{error: 'Missing chunk ' + i}};
            fullJson += chunk;
        }}
        
        // Clean up localStorage
        for (let i = 0; i < {len(chunks)}; i++) {{
            localStorage.removeItem('workflow_chunk_' + i);
        }}
        
        // Parse workflow
        const workflowData = JSON.parse(fullJson);
        
        // Get ComfyUI app
        const app = window.app;
        if (!app) return {{error: 'ComfyUI app not found'}};
        
        // Load workflow
        try {{
            await app.loadGraphData(workflowData);
            return {{loaded: true}};
        }} catch (e) {{
            return {{error: 'Load failed: ' + e.message}};
        }}
    }}
    """)
    
    if result.get("status") != "success" or "error" in result.get("result", {}):
        print(f"   ❌ Failed to load: {result}")
        return None
    
    print("   ✅ Workflow loaded into ComfyUI")
    
    # Now export as API format
    print("   📤 Exporting as API format...")
    
    result = client.eval_js("""
    async () => {
        const app = window.app;
        if (!app || !app.graph) return {error: 'No graph'};
        
        // Use ComfyUI's graphToPrompt method which converts to API format
        try {
            const prompt = await app.graphToPrompt();
            return {api_format: prompt.workflow};
        } catch (e) {
            return {error: 'graphToPrompt failed: ' + e.message};
        }
    }
    """)
    
    if result.get("status") != "success":
        print(f"   ❌ Export failed: {result}")
        return None
    
    api_workflow = result.get("result", {}).get("api_format")
    
    if not api_workflow:
        print("   ❌ No API format returned")
        return None
    
    print(f"   ✅ Exported API format")
    
    return api_workflow


def queue_workflow_http(api_workflow: dict, comfyui_url: str) -> bool:
    """Queue workflow via HTTP API."""
    print(f"\n⚡ Queuing workflow via HTTP API...")
    
    payload = {
        "prompt": api_workflow,
        "client_id": "hybrid_queue_script"
    }
    
    try:
        response = requests.post(
            f"{comfyui_url}/prompt",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            prompt_id = result.get("prompt_id")
            print(f"   ✅ Queued! Prompt ID: {prompt_id}")
            return True
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text[:300]}")
            return False
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    default_workflow = "/workspace/ComfyUI/user/default/workflows/UmeAiRT/WAN2.2_IMG_to_VIDEO_Base.json"
    
    workflow_path = sys.argv[1] if len(sys.argv) > 1 else default_workflow
    comfyui_url = "http://localhost:18188"
    
    print("🚀 ComfyUI Hybrid Workflow Queue")
    print(f"   Workflow: {workflow_path}")
    print(f"   ComfyUI: {comfyui_url}\n")
    
    if not Path(workflow_path).exists():
        print(f"❌ File not found: {workflow_path}\n")
        return 1
    
    # Start browser
    print("⏳ Starting browser...")
    server = BrowserServer(port=9999, headless=True)
    threading.Thread(target=server.start, daemon=True).start()
    time.sleep(3)
    
    client = BrowserClient(port=9999)
    client.ready()
    
    print("✅ Browser ready\n")
    
    # Navigate
    print("📍 Navigating to ComfyUI...")
    client.goto(comfyui_url)
    time.sleep(3)  # Wait for app to initialize
    print("✅ ComfyUI loaded\n")
    
    # Load and convert
    api_workflow = load_and_export_workflow(client, workflow_path, comfyui_url)
    
    if not api_workflow:
        print("\n❌ Failed to convert workflow\n")
        return 1
    
    # Queue via HTTP
    success = queue_workflow_http(api_workflow, comfyui_url)
    
    if success:
        print(f"\n✨ Done! Check {comfyui_url} to monitor progress\n")
        return 0
    else:
        print("\n❌ Failed to queue\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
