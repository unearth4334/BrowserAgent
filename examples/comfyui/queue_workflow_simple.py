#!/usr/bin/env python3
"""
Queue ComfyUI workflow - simple version without screenshots.

This version includes the same timing delays that were found to work
with screenshots, but without capturing images.
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


def main():
    workflow_path = "/workspace/ComfyUI/user/default/workflows/UmeAiRT/WAN2.2_IMG_to_VIDEO_Base.json"
    comfyui_url = "http://localhost:18188"
    
    print("🚀 ComfyUI Workflow Queue")
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
    print("📍 Step 1: Navigate to ComfyUI...")
    client.goto(comfyui_url)
    time.sleep(3)
    time.sleep(0.5)  # Delay that was at screenshot point
    print("✅ ComfyUI loaded\n")
    
    # Read workflow
    print("📍 Step 2: Read workflow file...")
    with open(workflow_path, 'r') as f:
        ui_workflow = json.load(f)
    print(f"   ✅ Read UI workflow ({len(ui_workflow.get('nodes', []))} nodes)")
    time.sleep(0.5)  # Delay that was at screenshot point
    print()
    
    # Store in localStorage (chunked)
    print("📍 Step 3: Store workflow in browser localStorage...")
    ui_json_str = json.dumps(ui_workflow)
    chunk_size = 50000
    chunks = [ui_json_str[i:i+chunk_size] for i in range(0, len(ui_json_str), chunk_size)]
    print(f"   Split into {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        escaped_chunk = chunk.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
        result = client.eval_js(f"""
        () => {{
            localStorage.setItem('workflow_chunk_{i}', '{escaped_chunk}');
            return {{stored: true, chunk: {i}}};
        }}
        """)
        
        if result.get("status") != "success":
            print(f"   ❌ Failed to store chunk {i}")
            return 1
    
    print("   ✅ Stored all chunks")
    time.sleep(0.5)  # Delay that was at screenshot point
    print()
    
    # Load workflow
    print("📍 Step 4: Load workflow into ComfyUI...")
    result = client.eval_js(f"""
    async () => {{
        let fullJson = '';
        for (let i = 0; i < {len(chunks)}; i++) {{
            const chunk = localStorage.getItem('workflow_chunk_' + i);
            if (!chunk) return {{error: 'Missing chunk ' + i}};
            fullJson += chunk;
            localStorage.removeItem('workflow_chunk_' + i);
        }}
        
        const workflowData = JSON.parse(fullJson);
        const app = window.app;
        if (!app) return {{error: 'ComfyUI app not found'}};
        
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
        return 1
    
    time.sleep(2)
    time.sleep(0.5)  # Delay that was at screenshot point
    print("   ✅ Workflow loaded\n")
    
    # Export as API format
    print("📍 Step 5: Export as API format...")
    result = client.eval_js("""
    async () => {
        const app = window.app;
        const prompt = await app.graphToPrompt();
        return {
            node_count: Object.keys(prompt.output).length,
            sample_nodes: Object.keys(prompt.output).slice(0, 5)
        };
    }
    """)
    
    if result.get("status") == "success":
        info = result.get("result", {})
        print(f"   ✅ API format ready ({info.get('node_count')} nodes)")
        print(f"   Sample node IDs: {info.get('sample_nodes')}\n")
    
    # Get the actual API workflow
    result = client.eval_js("""
    async () => {
        const app = window.app;
        const prompt = await app.graphToPrompt();
        return {api_format: prompt.output};
    }
    """)
    
    if result.get("status") != "success":
        print(f"   ❌ Failed to export: {result}")
        return 1
    
    api_workflow = result["result"]["api_format"]
    time.sleep(0.5)  # Delay that was at screenshot point
    
    # Queue via HTTP API
    print("📍 Step 6: Queue workflow via HTTP API...")
    try:
        response = requests.post(
            f"{comfyui_url}/prompt",
            json={"prompt": api_workflow},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        result = response.json()
        
        if "prompt_id" in result:
            print(f"   ✅ Queued! Prompt ID: {result['prompt_id']}\n")
        else:
            print(f"   ⚠️  Unexpected response: {result}\n")
    except Exception as e:
        print(f"   ❌ Failed to queue: {e}\n")
        return 1
    
    # Navigate to queue page
    client.goto(f"{comfyui_url}/#queue")
    time.sleep(0.5)  # Delay that was at screenshot point
    
    print(f"✨ Success! Check {comfyui_url} to monitor progress")
    return 0


if __name__ == "__main__":
    sys.exit(main())
