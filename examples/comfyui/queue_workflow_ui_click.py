#!/usr/bin/env python3
"""
Queue ComfyUI workflow by clicking the Queue button in the UI.

This approach fully preserves all UI metadata and is compatible with
workflows that use UI-dependent nodes like WidgetToString.
"""
import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from browser_agent.server.browser_server import BrowserServer
from browser_agent.server.browser_client import BrowserClient
import threading
import argparse


def main():
    parser = argparse.ArgumentParser(description="Queue ComfyUI workflow via UI button")
    parser.add_argument("--workflow-path", required=True, help="Path to workflow JSON file")
    parser.add_argument("--comfyui-url", default="http://localhost:18188", help="ComfyUI URL")
    args = parser.parse_args()
    
    workflow_path = args.workflow_path
    comfyui_url = args.comfyui_url
    
    print("🚀 ComfyUI Workflow Queue (UI Click Method)")
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
    time.sleep(0.5)
    print("✅ ComfyUI loaded\n")
    
    # Read workflow
    print("📍 Step 2: Read workflow file...")
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    node_count = len(workflow.get("nodes", []))
    print(f"   ✅ Read UI workflow ({node_count} nodes)\n")
    time.sleep(0.5)
    
    # Store in localStorage chunks
    print("📍 Step 3: Store workflow in browser localStorage...")
    ui_json_str = json.dumps(workflow)
    
    chunk_size = 50000
    chunks = [ui_json_str[i:i+chunk_size] for i in range(0, len(ui_json_str), chunk_size)]
    print(f"   Split into {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        escaped = chunk.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
        result = client.eval_js(f"""
        () => {{
            localStorage.setItem('workflow_chunk_{i}', '{escaped}');
            return {{stored: true, chunk: {i}}};
        }}
        """)
        
        if result.get("status") != "success":
            print(f"   ❌ Failed to store chunk {i}: {result}")
            return 1
    
    print("   ✅ Stored all chunks\n")
    time.sleep(0.5)
    
    # Load workflow from localStorage
    print("📍 Step 4: Load workflow into ComfyUI...")
    result = client.eval_js(f"""
    async () => {{
        try {{
            const app = window.app;
            
            // Reconstruct workflow from chunks
            let workflowStr = '';
            let i = 0;
            while (true) {{
                const chunk = localStorage.getItem('workflow_chunk_' + i);
                if (chunk === null) break;
                workflowStr += chunk;
                localStorage.removeItem('workflow_chunk_' + i);
                i++;
            }}
            
            const workflowData = JSON.parse(workflowStr);
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
    time.sleep(0.5)
    print("   ✅ Workflow loaded in UI\n")
    
    # Click the Queue button
    print("📍 Step 5: Click Queue button...")
    
    # First, get the queue button element
    result = client.eval_js("""
    () => {
        const buttons = document.querySelectorAll('button');
        for (let btn of buttons) {
            if (btn.textContent.trim() === 'Queue Prompt') {
                return {found: true, text: btn.textContent};
            }
        }
        return {found: false};
    }
    """)
    
    if not result.get("result", {}).get("found"):
        print("   ❌ Could not find 'Queue Prompt' button")
        return 1
    
    # Click the button
    result = client.eval_js("""
    () => {
        const buttons = document.querySelectorAll('button');
        for (let btn of buttons) {
            if (btn.textContent.trim() === 'Queue Prompt') {
                btn.click();
                return {clicked: true};
            }
        }
        return {clicked: false};
    }
    """)
    
    if not result.get("result", {}).get("clicked"):
        print("   ❌ Failed to click Queue button")
        return 1
    
    time.sleep(0.5)
    print("   ✅ Queue button clicked!\n")
    
    # Wait a moment for the queue to register
    time.sleep(1)
    
    # Try to get the prompt ID from the queue
    print("📍 Step 6: Check queue for prompt ID...")
    result = client.eval_js("""
    async () => {
        try {
            const response = await fetch('/queue');
            const data = await response.json();
            
            // Get the most recent prompt from pending queue
            if (data.queue_pending && data.queue_pending.length > 0) {
                const latest = data.queue_pending[data.queue_pending.length - 1];
                return {prompt_id: latest[1]};  // [number, id, prompt]
            }
            
            // Or from running queue
            if (data.queue_running && data.queue_running.length > 0) {
                const latest = data.queue_running[data.queue_running.length - 1];
                return {prompt_id: latest[1]};
            }
            
            return {no_queue: true};
        } catch (e) {
            return {error: e.message};
        }
    }
    """)
    
    if result.get("status") == "success":
        prompt_info = result.get("result", {})
        if "prompt_id" in prompt_info:
            print(f"   ✅ Queued! Prompt ID: {prompt_info['prompt_id']}\n")
        else:
            print(f"   ⚠️  Queued but couldn't retrieve prompt ID\n")
    else:
        print(f"   ⚠️  Queued but couldn't check queue: {result}\n")
    
    # Navigate to queue page
    client.goto(f"{comfyui_url}/#queue")
    time.sleep(0.5)
    
    print(f"✨ Success! Workflow queued via UI button")
    print(f"   Check {comfyui_url} to monitor progress")
    return 0


if __name__ == "__main__":
    sys.exit(main())
