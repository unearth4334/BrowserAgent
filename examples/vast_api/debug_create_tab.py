#!/usr/bin/env python3
"""
Debug script for vast_api WebUI - Inspect Create tab workflow-tile.

This script opens the vast_api WebUI, navigates to the Create tab,
and inspects the workflow-tile element to debug its contents.
"""

import sys
import time
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from browser_agent.server.browser_server import BrowserServer
from browser_agent.server.browser_client import BrowserClient
import threading


def debug_create_tab(webui_url="http://10.0.78.66:5000/", port=9999):
    """
    Open vast_api WebUI and inspect the Create tab workflow-tile.
    
    Args:
        webui_url: URL of the vast_api WebUI
        port: Port for browser server
    """
    print("🔍 vast_api WebUI Create Tab Debugger")
    print(f"   WebUI: {webui_url}")
    print(f"   Server Port: {port}\n")
    
    # Start browser server in background thread
    print("⏳ Starting browser server...")
    server = BrowserServer(port=port, headless=False)
    
    def run_server():
        server.start(initial_url=webui_url, wait_for_auth=True)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(4)
    
    # Connect client
    client = BrowserClient(host="localhost", port=port)
    print("✅ Browser server ready\n")
    
    try:
        # Send ready command to start main loop
        client.send_command({"action": "ready"})
        time.sleep(2)
        
        # Step 1: WebUI already loaded by server
        print("📍 Step 1: WebUI loaded at startup")
        time.sleep(2)
        
        # Get initial page info
        info = client.info()
        print(f"   URL: {info.get('url', 'unknown')}")
        print(f"   Title: {info.get('title', 'unknown')}")
        print("✅ Ready\n")
        
        # Step 2: Click the Create tab
        print("📍 Step 2: Click '🎨 Create' tab...")
        
        # Try multiple selectors to find the Create tab
        create_tab_selectors = [
            "button:has-text('🎨 Create')",
            "button:has-text('Create')",
            "[role='tab']:has-text('Create')",
            ".nav-link:has-text('Create')",
            "a:has-text('Create')"
        ]
        
        clicked = False
        for selector in create_tab_selectors:
            try:
                print(f"   Trying selector: {selector}")
                result = client.click(selector, timeout=2000)
                if result.get("status") == "success":
                    print(f"✅ Clicked Create tab using: {selector}\n")
                    clicked = True
                    break
            except Exception as e:
                print(f"   Failed: {e}")
                continue
        
        if not clicked:
            print("⚠️  Could not find Create tab with known selectors")
            print("   Inspecting page structure...\n")
            
            # Get page info
            info = client.info()
            print(f"   Current URL: {info.get('url', 'unknown')}")
            print(f"   Page Title: {info.get('title', 'unknown')}")
            
            # Try to find buttons
            buttons_js = """
            () => {
                const buttons = document.querySelectorAll('button, [role="tab"], .nav-link');
                return Array.from(buttons).map(btn => ({
                    tag: btn.tagName,
                    text: btn.textContent.trim().slice(0, 50),
                    id: btn.id,
                    classes: btn.className
                }));
            }
            """
            buttons_result = client.eval_js(buttons_js)
            print(f"\n   Found {len(buttons_result.get('result', []))} clickable elements:")
            for btn in buttons_result.get('result', [])[:10]:
                print(f"     - {btn['tag']}: '{btn['text']}' (id={btn['id']}, class={btn['classes']})")
        
        time.sleep(2)
        
        # Step 3: Inspect workflow-tile element IN CREATE TAB
        print("\n📍 Step 3: Inspect workflow-tile element in Create tab...")
        
        # Check if workflow-tile exists and get detailed structure
        workflow_tile_js = """
        () => {
            // Get the Create tab content first
            const createTab = document.querySelector('#create-tab');
            if (!createTab) {
                return {found: false, message: 'Create tab not found'};
            }
            
            // Find workflow-tile within Create tab
            const tile = createTab.querySelector('.workflow-tile');
            if (!tile) {
                return {found: false, message: 'workflow-tile not found in Create tab'};
            }
            
            // Get all buttons inside the tile
            const tabs = tile.querySelectorAll('button');
            const tabInfo = Array.from(tabs).map(tab => ({
                text: tab.textContent.trim(),
                classes: tab.className,
                id: tab.id,
                onclick: tab.onclick ? 'has onclick' : 'no onclick',
                onclickAttr: tab.getAttribute('onclick') || 'none'
            }));
            
            // Get workflow loading status
            const loadingMsg = tile.querySelector('.loading-message, [class*="loading"]');
            const workflowList = tile.querySelector('.workflow-list, [class*="workflow-list"]');
            
            return {
                found: true,
                innerHTML: tile.innerHTML.slice(0, 1000),
                textContent: tile.textContent.trim().slice(0, 300),
                classes: tile.className,
                id: tile.id,
                children: tile.children.length,
                childrenTags: Array.from(tile.children).map(c => c.tagName),
                tabs: tabInfo,
                tabCount: tabs.length,
                hasLoadingMessage: !!loadingMsg,
                loadingText: loadingMsg ? loadingMsg.textContent.trim() : null,
                hasWorkflowList: !!workflowList,
                workflowListItems: workflowList ? workflowList.children.length : 0
            };
        }
        """
        
        result = client.eval_js(workflow_tile_js)
        tile_data = result.get('result', {})
        
        if tile_data.get('found'):
            print("✅ Found workflow-tile element!\n")
            print(f"   ID: {tile_data.get('id', 'none')}")
            print(f"   Classes: {tile_data.get('classes', 'none')}")
            print(f"   Children: {tile_data.get('children', 0)} elements")
            print(f"   Child tags: {tile_data.get('childrenTags', [])}")
            
            # Tab information
            print(f"\n   📑 Buttons in workflow-tile:")
            print(f"   Found {tile_data.get('tabCount', 0)} buttons")
            for i, tab in enumerate(tile_data.get('tabs', []), 1):
                print(f"     Button {i}: '{tab['text']}'")
                print(f"       Classes: {tab['classes']}")
                print(f"       ID: {tab['id'] or 'none'}")
                print(f"       OnClick property: {tab['onclick']}")
                print(f"       OnClick attribute: {tab['onclickAttr']}")
            
            # Loading status
            if tile_data.get('hasLoadingMessage'):
                print(f"\n   ⏳ Loading message: {tile_data.get('loadingText')}")
            
            # Workflow list
            if tile_data.get('hasWorkflowList'):
                print(f"\n   📋 Workflow list: {tile_data.get('workflowListItems')} items")
            
            print(f"\n   Text content preview:")
            print(f"   {tile_data.get('textContent', '')}\n")
            print(f"   HTML preview (first 1000 chars):")
            print(f"   {tile_data.get('innerHTML', '')}\n")
        else:
            print("⚠️  workflow-tile element not found")
            print(f"   {tile_data.get('message', 'Unknown error')}\n")
            
            # Search for similar elements
            print("   Searching for similar elements...")
            search_js = """
            () => {
                const selectors = [
                    '.workflow', '.tile', '[class*="workflow"]', 
                    '[class*="tile"]', '#workflow', '#tile'
                ];
                
                const found = [];
                for (const sel of selectors) {
                    const elements = document.querySelectorAll(sel);
                    if (elements.length > 0) {
                        found.push({
                            selector: sel,
                            count: elements.length,
                            firstClasses: elements[0].className,
                            firstId: elements[0].id
                        });
                    }
                }
                return found;
            }
            """
            search_result = client.eval_js(search_js)
            similar = search_result.get('result', [])
            
            if similar:
                print(f"   Found {len(similar)} similar elements:")
                for item in similar:
                    print(f"     - {item['selector']}: {item['count']} element(s)")
                    print(f"       First: id={item['firstId']}, class={item['firstClasses']}")
            else:
                print("   No similar elements found")
        
        # Step 4: Get FULL page HTML for debugging
        print("\n📍 Step 4: Extract FULL page HTML...")
        
        full_html_js = """
        () => {
            return {
                html: document.documentElement.outerHTML,
                bodyText: document.body.textContent.trim(),
                title: document.title,
                url: window.location.href
            };
        }
        """
        
        result = client.eval_js(full_html_js)
        page_data = result.get('result', {})
        
        if page_data:
            # Save full HTML to file
            output_file = "/tmp/vast_api_page.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(page_data['html'])
            
            print(f"✅ Full page HTML saved to: {output_file}")
            print(f"   Page size: {len(page_data['html'])} characters")
            print(f"   Title: {page_data['title']}")
            print(f"   URL: {page_data['url']}")
            
            # Show first 2000 chars of body text
            body_text = page_data['bodyText'][:2000]
            print(f"\n   📄 Body text preview (first 2000 chars):")
            print(f"   {body_text}\n")
        else:
            print("⚠️  Failed to extract page data\n")
        
        # Keep browser open for manual inspection
        print("🔍 Browser remains open for manual inspection")
        print("   Press Ctrl+C to exit\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n✅ Exiting...")
    
    finally:
        client.send_command({"action": "quit"})
        time.sleep(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Debug vast_api WebUI Create tab")
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
