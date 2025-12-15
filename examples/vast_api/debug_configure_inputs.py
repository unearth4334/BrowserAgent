#!/usr/bin/env python3
"""
Debug script for vast_api WebUI - Inspect Configure Inputs error.

This script:
1. Opens the vast_api WebUI and navigates to Create tab
2. Looks for workflow tiles
3. Clicks on the first workflow
4. Inspects the Configure Inputs pane for errors
5. Checks for JavaScript errors and missing functions
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
            result = s.connect_ex(('localhost', port))
            return result == 0
        except:
            return False


def debug_configure_inputs(webui_url: str = "http://10.0.78.66:5000/", port: int = 9999):
    """Debug the Configure Inputs error in vast_api WebUI."""
    
    print("🔍 vast_api WebUI Configure Inputs Debugger")
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
        import threading
        def run_server():
            server.start(initial_url=webui_url, wait_for_auth=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(3)
        print("✓ Server started\n")
    
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
        print("📍 Step 1: Clicking Create tab...")
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
        
        # Find and click a workflow tile
        print("📍 Step 2: Looking for workflow tiles...")
        
        find_workflow_js = """
        () => {
            const grid = document.querySelector('#create-workflows-grid');
            if (!grid) return {found: false, message: 'Grid not found'};
            
            const tiles = grid.querySelectorAll('.workflow-card, [class*="workflow"]');
            if (tiles.length === 0) return {found: false, message: 'No workflow tiles found'};
            
            return {
                found: true,
                count: tiles.length,
                tiles: Array.from(tiles).slice(0, 5).map((tile, idx) => ({
                    index: idx,
                    tag: tile.tagName,
                    classes: tile.className,
                    id: tile.id || 'none',
                    text: tile.textContent.trim().slice(0, 100),
                    clickable: tile.tagName === 'BUTTON' || tile.onclick || tile.getAttribute('onclick')
                }))
            };
        }
        """
        
        result = client.eval_js(find_workflow_js)
        workflow_data = result.get('result', {})
        
        if not workflow_data.get('found'):
            print(f"⚠️  {workflow_data.get('message')}\n")
            return
        
        print(f"✅ Found {workflow_data['count']} workflow tiles")
        for tile in workflow_data['tiles']:
            print(f"   Tile {tile['index']}: {tile['text'][:50]}")
        print()
        
        # Click the first workflow tile
        print("📍 Step 3: Clicking first workflow tile...")
        
        click_workflow_js = """
        () => {
            const grid = document.querySelector('#create-workflows-grid');
            const tiles = grid.querySelectorAll('.workflow-card, [class*="workflow"]');
            if (tiles.length > 0) {
                tiles[0].click();
                return {success: true, clicked: tiles[0].textContent.trim().slice(0, 50)};
            }
            return {success: false, message: 'No tiles to click'};
        }
        """
        
        result = client.eval_js(click_workflow_js)
        click_data = result.get('result', {})
        
        if click_data.get('success'):
            print(f"✅ Clicked: {click_data['clicked']}\n")
            time.sleep(2)  # Wait for Configure Inputs to load
        else:
            print(f"⚠️  {click_data.get('message')}\n")
            return
        
        # Inspect the Configure Inputs pane
        print("📍 Step 4: Inspecting Configure Inputs pane...")
        
        inspect_inputs_js = """
        () => {
            // Find the form container
            const formContainer = document.querySelector('#create-form-container');
            if (!formContainer) {
                return {found: false, message: 'Form container not found'};
            }
            
            // Check visibility
            const isVisible = formContainer.style.display !== 'none';
            
            // Look for error messages
            const errorElements = formContainer.querySelectorAll('.error, [class*="error"]');
            const errors = Array.from(errorElements).map(el => ({
                tag: el.tagName,
                classes: el.className,
                text: el.textContent.trim()
            }));
            
            // Get all text content
            const allText = formContainer.textContent.trim();
            
            // Check for renderHelperTools mentions
            const hasRenderHelperError = allText.includes('renderHelperTools');
            
            // Get JavaScript console errors
            const consoleErrors = window.__consoleErrors || [];
            
            return {
                found: true,
                isVisible: isVisible,
                display: formContainer.style.display,
                errorCount: errorElements.length,
                errors: errors,
                hasRenderHelperError: hasRenderHelperError,
                textContent: allText.slice(0, 1000),
                innerHTML: formContainer.innerHTML.slice(0, 2000),
                childCount: formContainer.children.length,
                childTags: Array.from(formContainer.children).map(c => c.tagName)
            };
        }
        """
        
        result = client.eval_js(inspect_inputs_js)
        inputs_data = result.get('result', {})
        
        if not inputs_data.get('found'):
            print(f"⚠️  {inputs_data.get('message')}\n")
            return
        
        print("=" * 70)
        print("CONFIGURE INPUTS PANE ANALYSIS")
        print("=" * 70)
        
        print(f"\n📋 Basic Info:")
        print(f"   Container visible: {inputs_data.get('isVisible')}")
        print(f"   Display style: {inputs_data.get('display')}")
        print(f"   Children: {inputs_data.get('childCount')} elements ({inputs_data.get('childTags')})")
        
        print(f"\n❌ Error Detection:")
        print(f"   Error elements found: {inputs_data.get('errorCount')}")
        print(f"   Has 'renderHelperTools' error: {inputs_data.get('hasRenderHelperError')}")
        
        if inputs_data.get('errors'):
            print(f"\n   Error elements:")
            for i, err in enumerate(inputs_data['errors'], 1):
                print(f"      Error {i}:")
                print(f"         Tag: {err['tag']}")
                print(f"         Classes: {err['classes']}")
                print(f"         Text: {err['text']}")
        
        print(f"\n📄 Text Content (first 1000 chars):")
        print(f"   {inputs_data.get('textContent')}")
        
        print(f"\n🔍 HTML Preview (first 2000 chars):")
        print(f"   {inputs_data.get('innerHTML')}")
        
        # Check for JavaScript errors
        print("\n📍 Step 5: Checking for JavaScript errors...")
        
        js_errors_js = """
        () => {
            // Check if renderHelperTools is defined
            const renderHelperToolsDefined = typeof renderHelperTools !== 'undefined';
            const renderHelperToolsType = typeof renderHelperTools;
            
            // Check where it should be defined
            const inWindow = 'renderHelperTools' in window;
            
            // Look for it in common locations
            let locations = {
                window: typeof window.renderHelperTools,
                document: typeof document.renderHelperTools,
            };
            
            // Get all global functions
            const globalFunctions = Object.keys(window).filter(key => 
                typeof window[key] === 'function' && key.toLowerCase().includes('render')
            );
            
            return {
                renderHelperToolsDefined: renderHelperToolsDefined,
                renderHelperToolsType: renderHelperToolsType,
                inWindow: inWindow,
                locations: locations,
                globalRenderFunctions: globalFunctions.slice(0, 20)
            };
        }
        """
        
        result = client.eval_js(js_errors_js)
        js_data = result.get('result', {})
        
        print(f"\n   renderHelperTools defined: {js_data.get('renderHelperToolsDefined')}")
        print(f"   Type: {js_data.get('renderHelperToolsType')}")
        print(f"   In window: {js_data.get('inWindow')}")
        print(f"\n   Locations checked:")
        for loc, typ in js_data.get('locations', {}).items():
            print(f"      {loc}: {typ}")
        
        print(f"\n   Global render* functions found:")
        for func in js_data.get('globalRenderFunctions', []):
            print(f"      - {func}")
        
        # Search for where renderHelperTools should be defined
        print("\n📍 Step 6: Searching page source for renderHelperTools...")
        
        search_source_js = """
        () => {
            const html = document.documentElement.outerHTML;
            
            // Find all script tags
            const scripts = Array.from(document.querySelectorAll('script')).map(s => ({
                src: s.src || 'inline',
                hasRenderHelper: s.textContent.includes('renderHelperTools'),
                snippet: s.textContent.includes('renderHelperTools') 
                    ? s.textContent.substring(
                        Math.max(0, s.textContent.indexOf('renderHelperTools') - 100),
                        s.textContent.indexOf('renderHelperTools') + 200
                    )
                    : null
            }));
            
            // Count occurrences
            const matches = html.match(/renderHelperTools/g);
            const count = matches ? matches.length : 0;
            
            return {
                scriptCount: scripts.length,
                scriptsWithRenderHelper: scripts.filter(s => s.hasRenderHelper),
                totalOccurrences: count
            };
        }
        """
        
        result = client.eval_js(search_source_js)
        search_data = result.get('result', {})
        
        print(f"\n   Total script tags: {search_data.get('scriptCount')}")
        print(f"   Scripts containing 'renderHelperTools': {len(search_data.get('scriptsWithRenderHelper', []))}")
        print(f"   Total occurrences in page: {search_data.get('totalOccurrences')}")
        
        if search_data.get('scriptsWithRenderHelper'):
            print(f"\n   Scripts with renderHelperTools:")
            for i, script in enumerate(search_data['scriptsWithRenderHelper'], 1):
                print(f"      Script {i}: {script['src']}")
                if script.get('snippet'):
                    print(f"         Context: ...{script['snippet'][:150]}...")
        
        print("\n" + "=" * 70)
        print("END OF ANALYSIS")
        print("=" * 70 + "\n")
        
        print("✅ Debug complete!\n")
        print("💡 Summary:")
        print(f"   - Configure Inputs visible: {inputs_data.get('isVisible')}")
        print(f"   - Error detected: {inputs_data.get('hasRenderHelperError')}")
        print(f"   - renderHelperTools defined: {js_data.get('renderHelperToolsDefined')}")
        print(f"   - Function type: {js_data.get('renderHelperToolsType')}")
        
        if not js_data.get('renderHelperToolsDefined'):
            print("\n⚠️  ISSUE: renderHelperTools is not defined!")
            print("   Possible causes:")
            print("   1. JavaScript file not loaded")
            print("   2. Function defined in wrong scope")
            print("   3. Typo in function name")
            print("   4. Script loading order issue")
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
    
    finally:
        # Only quit if we started the server
        if server and not server_exists:
            print("\n🛑 Stopping browser server...")
            try:
                client.send_command({"action": "quit"})
            except:
                pass


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Debug Configure Inputs renderHelperTools error"
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
    
    debug_configure_inputs(webui_url=args.url, port=args.port)
