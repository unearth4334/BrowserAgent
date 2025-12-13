#!/usr/bin/env python3
"""
Debug ComfyUI workflow loading with screenshots at each step.

This script helps identify the correct selectors and DOM structure
by capturing screenshots throughout the workflow loading process.

Usage:
    python3 debug_workflow_with_screenshots.py [workflow_path] [output_dir]
"""
import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from browser_agent.server.browser_server import BrowserServer
from browser_agent.server.browser_client import BrowserClient
import threading


def debug_workflow_loading(
    workflow_path: str,
    output_dir: Path,
    comfyui_url: str = "http://localhost:18188"
):
    """Debug workflow loading with screenshots."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🔍 ComfyUI Workflow Loading Debugger")
    print(f"   URL: {comfyui_url}")
    print(f"   Workflow: {workflow_path}")
    print(f"   Screenshots: {output_dir}\n")
    
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
        return False
    
    print("✅ Connected to browser\n")
    
    # Navigate to ComfyUI
    print("📍 Step 1: Navigate to ComfyUI")
    result = client.goto(comfyui_url)
    if result.get("status") != "success":
        print(f"❌ Navigation failed: {result}")
        return False
    
    time.sleep(2)
    screenshot_path = str(output_dir / "01_initial_page.png")
    client.screenshot(screenshot_path)
    print(f"   📸 Screenshot: {screenshot_path}")
    
    # Find and list all buttons
    print("\n📍 Step 2: Inspect all buttons")
    result = client.eval_js("""
    () => {
        const buttons = Array.from(document.querySelectorAll('button'));
        return buttons.map(b => ({
            text: b.textContent.substring(0, 60).trim(),
            classes: b.className.substring(0, 60)
        }));
    }
    """)
    
    if result.get("status") == "success":
        buttons = result.get("result", [])
        print(f"   Found {len(buttons)} buttons:")
        for i, btn in enumerate(buttons[:15]):  # Show first 15
            print(f"     {i+1}. '{btn['text']}'")
    
    # Click Load button
    print("\n📍 Step 3: Click 'Load' button")
    result = client.eval_js("""
    () => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const loadBtn = buttons.find(b => b.textContent.trim() === 'Load');
        if (!loadBtn) {
            return {error: 'Load button not found'};
        }
        loadBtn.click();
        return {clicked: true};
    }
    """)
    
    if result.get("status") != "success" or "error" in result.get("result", {}):
        print(f"   ❌ Failed: {result}")
        return False
    
    print("   ✅ Clicked Load button")
    time.sleep(2)
    
    screenshot_path = str(output_dir / "02_after_load_click.png")
    client.screenshot(screenshot_path)
    print(f"   📸 Screenshot: {screenshot_path}")
    
    # Check what dialog/modal opened
    print("\n📍 Step 4: Inspect opened dialog/modal")
    result = client.eval_js("""
    () => {
        return {
            dialogs: Array.from(document.querySelectorAll('dialog, [role=dialog], .dialog, .modal')).map(d => ({
                tag: d.tagName,
                classes: d.className,
                visible: d.offsetParent !== null
            })),
            overlays: Array.from(document.querySelectorAll('.overlay, .backdrop, [class*="overlay"]')).length,
            all_visible_divs: Array.from(document.querySelectorAll('div')).filter(d => {
                const rect = d.getBoundingClientRect();
                return rect.width > 200 && rect.height > 200 && d.offsetParent !== null;
            }).map(d => ({
                classes: d.className.substring(0, 80),
                width: Math.round(d.getBoundingClientRect().width),
                height: Math.round(d.getBoundingClientRect().height)
            })).slice(0, 10)
        };
    }
    """)
    
    if result.get("status") == "success":
        data = result.get("result", {})
        print(f"   Dialogs found: {len(data.get('dialogs', []))}")
        print(f"   Overlays found: {data.get('overlays', 0)}")
        print(f"   Large visible divs: {len(data.get('all_visible_divs', []))}")
        for div in data.get('all_visible_divs', [])[:5]:
            print(f"     - {div}")
    
    # Look for file browser elements
    print("\n📍 Step 5: Look for file browser UI")
    result = client.eval_js("""
    () => {
        // Look for buttons with data attributes or file-like elements
        const allButtons = Array.from(document.querySelectorAll('button, [role=button], .file-item, li'));
        const fileElements = allButtons.filter(el => {
            const text = el.textContent;
            const hasDataAttr = el.hasAttribute('data-name') || el.hasAttribute('data-path') || el.hasAttribute('data-file');
            const looksLikeFile = text.includes('.json') || text.includes('Workflow');
            return hasDataAttr || looksLikeFile;
        }).slice(0, 20);
        
        return {
            count: fileElements.length,
            elements: fileElements.map(el => ({
                tag: el.tagName,
                text: el.textContent.substring(0, 50).trim(),
                classes: el.className.substring(0, 50),
                attrs: Array.from(el.attributes).map(a => `${a.name}=${a.value.substring(0, 30)}`).slice(0, 3)
            }))
        };
    }
    """)
    
    if result.get("status") == "success":
        data = result.get("result", {})
        print(f"   Found {data.get('count', 0)} file-related elements:")
        for elem in data.get('elements', [])[:10]:
            print(f"     - {elem}")
    
    screenshot_path = str(output_dir / "03_dialog_inspection.png")
    client.screenshot(screenshot_path)
    print(f"   📸 Screenshot: {screenshot_path}")
    
    # Try to find and click workflow folder
    print(f"\n📍 Step 6: Look for workflow path: {workflow_path}")
    parts = workflow_path.split("/")
    print(f"   Parts: {parts}")
    
    if len(parts) > 0:
        folder_name = parts[0]
        print(f"   Looking for folder: {folder_name}")
        
        result = client.eval_js(f"""
        () => {{
            // Try multiple strategies to find the folder
            const allElements = Array.from(document.querySelectorAll('*'));
            
            const byDataName = allElements.filter(el => el.getAttribute('data-name') === '{folder_name}');
            const byText = allElements.filter(el => el.textContent.trim() === '{folder_name}');
            const byPartialText = allElements.filter(el => el.textContent.includes('{folder_name}'));
            
            return {{
                by_data_name: byDataName.map(el => ({{
                    tag: el.tagName,
                    classes: el.className,
                    attrs: Array.from(el.attributes).map(a => `${{a.name}}=${{a.value}}`).join(' ')
                }})),
                by_exact_text: byText.map(el => ({{
                    tag: el.tagName,
                    classes: el.className
                }})),
                by_partial_text: byPartialText.slice(0, 5).map(el => ({{
                    tag: el.tagName,
                    text: el.textContent.substring(0, 50),
                    classes: el.className.substring(0, 50)
                }}))
            }};
        }}
        """)
        
        if result.get("status") == "success":
            data = result.get("result", {})
            print(f"   By data-name: {len(data.get('by_data_name', []))}")
            print(f"   By exact text: {len(data.get('by_exact_text', []))}")
            print(f"   By partial text: {len(data.get('by_partial_text', []))}")
            
            for key, items in data.items():
                if items:
                    print(f"\n   {key}:")
                    for item in items[:3]:
                        print(f"     - {item}")
    
    screenshot_path = str(output_dir / "04_folder_search.png")
    client.screenshot(screenshot_path)
    print(f"   📸 Screenshot: {screenshot_path}")
    
    print("\n✅ Debug complete! Check screenshots in:", output_dir)
    print("\nNext steps:")
    print("1. Review screenshots to understand UI structure")
    print("2. Identify correct selectors for folder/file navigation")
    print("3. Update workflow loading script with correct selectors\n")
    
    return True


def main():
    workflow_path = sys.argv[1] if len(sys.argv) > 1 else "UmeAiRT/WAN2.2_IMG_to_VIDEO_Base.json"
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/comfyui_debug")
    
    debug_workflow_loading(workflow_path, output_dir)


if __name__ == "__main__":
    main()
