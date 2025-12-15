#!/usr/bin/env python3
"""
Automatic debug script for vast_api WebUI - Inspect Create tab.

This script automatically:
1. Checks if browser server is running (or starts one)
2. Navigates to the Create tab
3. Extracts and displays all content from the workflow-tile
"""

import sys
import time
import socket
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from browser_agent.server.browser_server import BrowserServer
from browser_agent.server.browser_client import BrowserClient


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use by trying to connect to it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            # Try to connect - if successful, server is running
            result = s.connect_ex(('localhost', port))
            return result == 0
        except:
            return False


def debug_create_tab(webui_url: str = "http://10.0.78.66:5000/", port: int = 9999):
    """Debug the Create tab in vast_api WebUI."""
    
    print("🔍 vast_api WebUI Create Tab Debugger")
    print(f"   WebUI: {webui_url}")
    print(f"   Server Port: {port}\n")
    
    # Check if server is already running
    server_exists = is_port_in_use(port)
    server = None
    
    if server_exists:
        print(f"✓ Found existing browser server on port {port}\n")
    else:
        print("⏳ Starting new browser server...")
        server = BrowserServer(port=port, headless=False)
        # Start without wait_for_auth to avoid interactive prompt
        import threading
        def run_server():
            server.start(initial_url=webui_url, wait_for_auth=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(3)  # Wait for server to initialize
        print("✓ Server started\n")
    
    # Connect client
    client = BrowserClient(port=port)
    
    try:
        # Server already navigates to initial_url, just wait a moment
        if not server_exists:
            print("📍 Waiting for page to load...")
            time.sleep(2)
        
        # Get current page info
        info = client.info()
        print(f"📍 Current page:")
        print(f"   URL: {info.get('url')}")
        print(f"   Title: {info.get('title')}\n")
        
        # Click the Create tab
        print("📍 Clicking Create tab...")
        create_selectors = [
            "button:has-text('🎨 Create')",
            "button.tab-button:has-text('Create')",
            ".tab-button[onclick*='create']"
        ]
        
        clicked = False
        for selector in create_selectors:
            try:
                client.click(selector)
                print(f"✅ Clicked using: {selector}\n")
                clicked = True
                time.sleep(1)
                break
            except Exception as e:
                continue
        
        if not clicked:
            print("⚠️  Could not click Create tab\n")
            return
        
        # Inspect the workflow-tile in Create tab
        print("📍 Inspecting Create tab workflow-tile...\n")
        
        inspect_js = """
        () => {
            // Get the Create tab content
            const createTab = document.querySelector('#create-tab');
            if (!createTab) {
                return {found: false, message: 'Create tab not found'};
            }
            
            // Find workflow-tile within Create tab
            const tile = createTab.querySelector('.workflow-tile');
            if (!tile) {
                return {found: false, message: 'workflow-tile not found in Create tab'};
            }
            
            // Get all buttons in the tile
            const buttons = tile.querySelectorAll('button');
            const buttonInfo = Array.from(buttons).map(btn => ({
                text: btn.textContent.trim(),
                classes: btn.className,
                id: btn.id || 'none',
                onclick: btn.getAttribute('onclick') || 'none',
                disabled: btn.disabled
            }));
            
            // Check for empty state
            const emptyState = tile.querySelector('.create-empty-state');
            const emptyIcon = tile.querySelector('.create-empty-state-icon');
            const emptyDesc = tile.querySelector('.create-empty-state-description');
            
            // Check for workflow grid
            const workflowGrid = tile.querySelector('#create-workflows-grid, .workflow-grid');
            const workflowCards = tile.querySelectorAll('.workflow-card');
            
            return {
                found: true,
                tileHeader: tile.querySelector('.tile-header')?.textContent.trim(),
                hasEmptyState: !!emptyState,
                emptyIcon: emptyIcon?.textContent.trim(),
                emptyDescription: emptyDesc?.textContent.trim(),
                hasWorkflowGrid: !!workflowGrid,
                workflowGridId: workflowGrid?.id,
                workflowCardCount: workflowCards.length,
                buttonCount: buttons.length,
                buttons: buttonInfo,
                childCount: tile.children.length,
                childTags: Array.from(tile.children).map(c => c.tagName),
                textContent: tile.textContent.trim().slice(0, 500),
                innerHTML: tile.innerHTML.slice(0, 1500)
            };
        }
        """
        
        result = client.eval_js(inspect_js)
        data = result.get('result', {})
        
        if not data.get('found'):
            print(f"⚠️  {data.get('message', 'Unknown error')}\n")
            return
        
        # Display results
        print("=" * 70)
        print("CREATE TAB WORKFLOW-TILE CONTENT")
        print("=" * 70)
        
        print(f"\n📋 Basic Info:")
        print(f"   Header: {data.get('tileHeader')}")
        print(f"   Children: {data.get('childCount')} elements ({data.get('childTags')})")
        
        print(f"\n📭 Empty State:")
        print(f"   Has empty state: {data.get('hasEmptyState')}")
        if data.get('hasEmptyState'):
            print(f"   Icon: {data.get('emptyIcon')}")
            print(f"   Message: {data.get('emptyDescription')}")
        
        print(f"\n🗂️  Workflow Grid:")
        print(f"   Has workflow grid: {data.get('hasWorkflowGrid')}")
        print(f"   Grid ID: {data.get('workflowGridId')}")
        print(f"   Workflow cards: {data.get('workflowCardCount')}")
        
        print(f"\n🔘 Buttons:")
        print(f"   Found {data.get('buttonCount')} buttons")
        for i, btn in enumerate(data.get('buttons', []), 1):
            print(f"   Button {i}:")
            print(f"      Text: '{btn['text']}'")
            print(f"      ID: {btn['id']}")
            print(f"      Classes: {btn['classes']}")
            print(f"      OnClick: {btn['onclick']}")
            print(f"      Disabled: {btn['disabled']}")
        
        print(f"\n📄 Text Content (first 500 chars):")
        print(f"   {data.get('textContent')}")
        
        print(f"\n🔍 HTML Preview (first 1500 chars):")
        print(f"   {data.get('innerHTML')}")
        
        print("\n" + "=" * 70)
        print("END OF REPORT")
        print("=" * 70 + "\n")
        
        print("✅ Debug complete! Check the report above.\n")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
    
    finally:
        # Only quit if we started the server
        if server and not server_exists:
            print("🛑 Stopping browser server...")
            try:
                client.send_command({"action": "quit"})
            except:
                pass


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Debug vast_api WebUI Create tab (automatic version)"
    )
    parser.add_argument(
        "--url",
        default="http://10.0.78.66:5000/",
        help="WebUI URL (default: http://10.0.78.66:5000/)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9999,
        help="Browser server port (default: 9999)"
    )
    
    args = parser.parse_args()
    
    debug_create_tab(webui_url=args.url, port=args.port)
