#!/usr/bin/env python3
"""
Open a ComfyUI workflow via the browser server.

This script sends commands to the browser server to:
1. Click the workflow sidebar button
2. Navigate the workflow tree
3. Open the specified workflow file
"""
from pathlib import Path
import sys
import time

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from browser_agent.server.browser_client import BrowserClient


def load_credentials(credentials_file: Path) -> tuple[str, str, str, str]:
    """Load credentials, URL, and workflow path from the credentials file."""
    if not credentials_file.exists():
        raise FileNotFoundError(f"Credentials file not found: {credentials_file}")
    
    content = credentials_file.read_text().strip()
    non_comment_lines = []
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            non_comment_lines.append(line)
    
    username = password = url = workflow_path = None
    
    if len(non_comment_lines) >= 1 and ":" in non_comment_lines[0]:
        username, password = non_comment_lines[0].split(":", 1)
        username = username.strip()
        password = password.strip()
    
    if len(non_comment_lines) >= 2:
        url = non_comment_lines[1].strip()
    
    if len(non_comment_lines) >= 3:
        workflow_path = non_comment_lines[2].strip()
    
    return username, password, url, workflow_path


def open_workflow(client: BrowserClient, workflow_path: str):
    """Open a workflow in ComfyUI."""
    print(f"🔧 Opening workflow: {workflow_path}")
    
    # Step 1: Check if workflow panel is already open, if not, open it
    print("   1. Checking/opening workflow sidebar panel...")
    check_panel_js = """
    (function() {
        const panel = document.querySelector('.comfyui-workflows-panel');
        if (!panel) return 'closed';
        const style = window.getComputedStyle(panel.closest('.side-bar-panel'));
        if (style.display === 'none') return 'closed';
        return 'open';
    })()
    """
    result = client.eval_js(check_panel_js)
    panel_state = result.get("result", "closed")
    
    if panel_state == "closed":
        print("      Panel is closed, opening it...")
        result = client.click("i.icon-\\[comfy--workflow\\].side-bar-button-icon")
        if result.get("status") != "success":
            print(f"   ❌ Failed to click workflow button: {result.get('message')}")
            return False
        
        # Wait for workflow panel content to load
        print("      Waiting for workflow panel to load...")
        result = client.wait(".comfyui-workflows-panel .p-tree-node", timeout=10000)
        if result.get("status") != "success":
            print(f"   ❌ Workflow panel content did not load: {result.get('message')}")
            return False
        
        time.sleep(0.5)  # Small additional wait for rendering
    else:
        print("      Panel is already open")
    
    # Step 2: Parse workflow path (e.g., "UmeAiRT/WAN2.2_IMG_to_VIDEO_Base.json")
    parts = workflow_path.split("/")
    if len(parts) != 2:
        print(f"   ❌ Invalid workflow path format. Expected: folder/file.json")
        return False
    
    folder_name = parts[0]
    file_name = parts[1]
    
    # Step 3: Check if folder is already expanded, if not, expand it
    print(f"   2. Checking/expanding folder: {folder_name}")
    check_expand_js = f"""
    (function() {{
        // Find all span elements that might contain the folder name
        const allSpans = Array.from(document.querySelectorAll('span'));
        const folderSpan = allSpans.find(s => s.textContent.trim() === '{folder_name}');
        if (!folderSpan) {{
            // Debug: return what we found
            const editable = Array.from(document.querySelectorAll('span.editable-text span')).map(s => s.textContent.trim());
            return 'Folder not found. Found: ' + JSON.stringify(editable);
        }}
        
        // Find the toggle button - go up to tree node and check if expanded
        const treeNode = folderSpan.closest('.p-tree-node');
        if (!treeNode) return 'Tree node not found';
        
        // Check if already expanded (aria-expanded attribute)
        const isExpanded = treeNode.getAttribute('aria-expanded') === 'true';
        if (isExpanded) return 'Already expanded';
        
        const toggleButton = treeNode.querySelector('button.p-tree-node-toggle-button');
        if (!toggleButton) return 'Toggle button not found';
        
        toggleButton.click();
        return 'Clicked';
    }})()
    """
    result = client.eval_js(check_expand_js)
    expand_result = result.get("result", "")
    
    if expand_result.startswith("Folder not found"):
        print(f"   ❌ {expand_result}")
        return False
    elif expand_result == "Already expanded":
        print(f"      Folder is already expanded")
    elif expand_result == "Clicked":
        print(f"      Expanded folder")
        time.sleep(1)  # Wait for folder to expand and show children
    else:
        print(f"   ❌ Unexpected result: {expand_result}")
        return False
    
    # Step 4: Click the workflow file using JavaScript
    print(f"   3. Opening workflow file: {file_name}")
    click_file_js = f"""
    (function() {{
        // Find all span elements with the file name
        const allSpans = Array.from(document.querySelectorAll('span'));
        const fileSpan = allSpans.find(s => s.textContent.trim() === '{file_name}');
        if (!fileSpan) {{
            // Debug: return what we found
            const editable = Array.from(document.querySelectorAll('span.editable-text span')).map(s => s.textContent.trim());
            return 'File not found. Found: ' + JSON.stringify(editable);
        }}
        
        fileSpan.click();
        return 'Clicked';
    }})()
    """
    result = client.eval_js(click_file_js)
    if result.get("status") != "success" or not result.get("result", "").startswith("Clicked"):
        print(f"   ❌ Failed to open workflow file: {result.get('result', result.get('message'))}")
        return False
    
    print(f"✅ Workflow opened successfully!")
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Open a ComfyUI workflow via the browser server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9999,
        help="Browser server port (default: %(default)s)",
    )
    parser.add_argument(
        "--workflow",
        help="Workflow path (e.g., UmeAiRT/WAN2.2_IMG_to_VIDEO_Base.json)",
    )
    parser.add_argument(
        "--credentials-file",
        type=Path,
        default=project_root / "vastai_credentials.txt",
        help="Path to credentials file (default: vastai_credentials.txt)",
    )
    
    args = parser.parse_args()
    
    # Load workflow from credentials if not provided
    workflow_path = args.workflow
    if not workflow_path:
        try:
            _, _, _, workflow_path = load_credentials(args.credentials_file)
            if not workflow_path:
                print("❌ No workflow path specified and none found in credentials file")
                return 1
            print(f"📁 Using workflow from credentials: {workflow_path}")
        except Exception as e:
            print(f"❌ Error loading credentials: {e}")
            return 1
    
    # Create browser client
    client = BrowserClient(port=args.port)
    
    # Check server is running
    ping_result = client.ping()
    if ping_result.get("status") != "success":
        print(f"❌ Browser server not responding on port {args.port}")
        print(f"   Please start the server first: python3 examples/vastai/browser_server.py")
        return 1
    
    # Open the workflow
    success = open_workflow(client, workflow_path)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
