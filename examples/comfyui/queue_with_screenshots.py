#!/usr/bin/env python3
"""
Queue ComfyUI workflow with screenshots at each step.

This version captures screenshots throughout the process for verification.
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
    screenshot_dir = Path("/tmp/queue_screenshots")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 ComfyUI Workflow Queue with Screenshots")
    print(f"   Workflow: {workflow_path}")
    print(f"   ComfyUI: {comfyui_url}")
    print(f"   Screenshots: {screenshot_dir}\n")
    
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
    
    screenshot_path = str(screenshot_dir / "step1_initial_load.png")
    client.screenshot(screenshot_path)
    print(f"   📸 Screenshot: {screenshot_path}")
    print("✅ ComfyUI loaded\n")
    
    # Read workflow
    print("📍 Step 2: Read workflow file...")
    with open(workflow_path, 'r') as f:
        ui_workflow = json.load(f)
    print(f"   ✅ Read UI workflow ({len(ui_workflow.get('nodes', []))} nodes)\n")
    
    # Store in localStorage (chunked)
    print("📍 Step 3: Store workflow in browser localStorage...")
    ui_json_str = json.dumps(ui_workflow)
    chunk_size = 50000
    chunks = [ui_json_str[i:i+chunk_size] for i in range(0, len(ui_json_str), chunk_size)]
    print(f"   Split into {chunks} chunks")
    
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
    
    print("   ✅ Stored all chunks\n")
    
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
    screenshot_path = str(screenshot_dir / "step4_workflow_loaded.png")
    client.screenshot(screenshot_path)
    print(f"   📸 Screenshot: {screenshot_path}")
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
        print(f"   ❌ Failed to get API format: {result}")
        return 1
    
    api_workflow = result.get("result", {}).get("api_format")
    
    screenshot_path = str(screenshot_dir / "step5_api_export.png")
    client.screenshot(screenshot_path)
    print(f"   📸 Screenshot: {screenshot_path}\n")
    
    # Queue via HTTP
    print("📍 Step 6: Queue workflow via HTTP API...")
    payload = {
        "prompt": api_workflow,
        "client_id": "screenshot_queue_script"
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
            print(f"   ✅ Queued! Prompt ID: {prompt_id}\n")
            
            # Take final screenshot showing queue
            time.sleep(2)
            client.goto(f"{comfyui_url}/#queue")
            time.sleep(2)
            screenshot_path = str(screenshot_dir / "step6_queued_final.png")
            client.screenshot(screenshot_path)
            print(f"   📸 Screenshot: {screenshot_path}\n")
            
            print(f"✨ Success! All screenshots saved to: {screenshot_dir}")
            print(f"   Check {comfyui_url} to monitor progress\n")
            return 0
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text[:300]}")
            return 1
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
