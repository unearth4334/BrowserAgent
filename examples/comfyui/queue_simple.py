#!/usr/bin/env python3
"""
Queue ComfyUI workflow using Python requests (simplest approach).

This script:
1. Reads the workflow JSON file
2. Posts it directly to ComfyUI's /prompt endpoint via HTTP
3. No browser automation needed!

Usage:
    python3 queue_simple.py [workflow_path] [batch_count]
"""
import sys
import json
import requests
from pathlib import Path


def convert_workflow_to_api_format(workflow_data: dict) -> dict:
    """
    Convert UI format workflow to API format if needed.
    
    UI format: {nodes: [...], links: [...]}
    API format: {node_id: {class_type: ..., inputs: {...}}}
    """
    if 'nodes' not in workflow_data:
        # Already in API format
        return workflow_data
    
    print("   Converting UI format to API format...")
    
    # Simple conversion - extract class_type and inputs from nodes
    api_workflow = {}
    
    for node in workflow_data.get('nodes', []):
        node_id = str(node['id'])
        node_type = node.get('type')
        
        if not node_type:
            continue
        
        api_node = {
            "class_type": node_type,
            "inputs": {}
        }
        
        # Add any properties as inputs
        if 'properties' in node:
            for key, value in node['properties'].items():
                api_node['inputs'][key] = value
        
        api_workflow[node_id] = api_node
    
    return api_workflow


def queue_workflow_http(workflow_path: str, comfyui_url: str = "http://localhost:18188"):
    """Queue workflow via direct HTTP POST."""
    print(f"🚀 Queuing ComfyUI Workflow (HTTP API)")
    print(f"   Workflow: {workflow_path}")
    print(f"   ComfyUI: {comfyui_url}\n")
    
    # Read workflow
    print("📄 Reading workflow...")
    with open(workflow_path, 'r') as f:
        workflow_data = json.load(f)
    
    # Check/convert format
    if 'nodes' in workflow_data:
        print("   ⚠️  Workflow is in UI format")
        print("   This may not work correctly with all custom nodes")
        print("   Consider using 'Save (API Format)' in ComfyUI\n")
        
        # Try to use it anyway
        api_workflow = workflow_data
    else:
        print("   ✅ Workflow is in API format")
        api_workflow = workflow_data
    
    # Prepare payload
    payload = {
        "prompt": api_workflow,
        "client_id": "python_queue_script"
    }
    
    # Post to ComfyUI
    print(f"\n⚡ Posting to {comfyui_url}/prompt...")
    
    try:
        response = requests.post(
            f"{comfyui_url}/prompt",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            prompt_id = result.get("prompt_id")
            print(f"   ✅ Workflow queued successfully!")
            print(f"   Prompt ID: {prompt_id}")
            print(f"\n✨ Check {comfyui_url} to monitor progress\n")
            return True
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:500]}\n")
            
            if response.status_code == 400:
                print("   💡 Tip: Try exporting workflow as 'API Format' in ComfyUI")
                print("      Click 'Save (API Format)' button in ComfyUI interface\n")
            
            return False
    
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False


def main():
    default_workflow = "/workspace/ComfyUI/user/default/workflows/UmeAiRT/WAN2.2_IMG_to_VIDEO_Base.json"
    
    workflow_path = sys.argv[1] if len(sys.argv) > 1 else default_workflow
    comfyui_url = "http://localhost:18188"
    
    if not Path(workflow_path).exists():
        print(f"❌ Workflow file not found: {workflow_path}\n")
        return 1
    
    success = queue_workflow_http(workflow_path, comfyui_url)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
