#!/usr/bin/env python3
"""
Debug script to monitor workflow loading in the Create tab.

This script waits and checks periodically if workflows appear in the
create-workflows-grid element.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from browser_agent.server.browser_server import BrowserServer
from browser_agent.server.browser_client import BrowserClient


def monitor_workflow_loading(webui_url: str, port: int = 9999, wait_seconds: int = 30):
    """Monitor workflow loading in the Create tab."""
    
    print("🔍 Monitoring Workflow Loading in Create Tab")
    print(f"   WebUI: {webui_url}")
    print(f"   Will check every 2 seconds for {wait_seconds} seconds\n")
    
    server = BrowserServer(port=port, headless=False)
    client = BrowserClient(port=port)
    
    try:
        print("⏳ Starting browser server...")
        server.start(initial_url=webui_url, wait_for_auth=True)
        print("✓ Server ready\n")
        
        # Step 1: Verify page loaded
        info = client.info()
        print(f"📍 Initial page state")
        print(f"   URL: {info.get('url')}")
        print(f"   Title: {info.get('title')}\n")
        
        # Step 2: Click Create tab
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
                break
            except Exception as e:
                continue
        
        if not clicked:
            print("⚠️  Could not click Create tab\n")
            return
        
        time.sleep(1)
        
        # Step 3: Monitor workflow grid for changes
        print("📍 Monitoring create-workflows-grid...")
        print("   Checking every 2 seconds...\n")
        
        check_js = """
        () => {
            const grid = document.querySelector('#create-workflows-grid');
            if (!grid) {
                return {found: false, message: 'Grid not found'};
            }
            
            const emptyState = grid.querySelector('.create-empty-state');
            const workflows = grid.querySelectorAll('.workflow-card, [class*="workflow"]');
            
            return {
                found: true,
                hasEmptyState: !!emptyState,
                emptyMessage: emptyState ? emptyState.textContent.trim() : null,
                workflowCount: workflows.length,
                workflows: Array.from(workflows).slice(0, 5).map(w => ({
                    tag: w.tagName,
                    classes: w.className,
                    text: w.textContent.trim().slice(0, 100)
                })),
                innerHTML: grid.innerHTML.slice(0, 500),
                childCount: grid.children.length,
                childTags: Array.from(grid.children).map(c => c.tagName)
            };
        }
        """
        
        start_time = time.time()
        check_count = 0
        
        while time.time() - start_time < wait_seconds:
            check_count += 1
            result = client.eval_js(check_js)
            data = result.get('result', {})
            
            if not data.get('found'):
                print(f"   Check {check_count}: Grid not found")
            else:
                elapsed = int(time.time() - start_time)
                print(f"   Check {check_count} (t={elapsed}s):")
                print(f"      Empty state: {data.get('hasEmptyState')}")
                if data.get('hasEmptyState'):
                    print(f"      Message: {data.get('emptyMessage')}")
                print(f"      Workflow count: {data.get('workflowCount')}")
                print(f"      Children: {data.get('childCount')} ({data.get('childTags')})")
                
                if data.get('workflowCount') > 0:
                    print(f"\n   ✅ Workflows appeared!")
                    print(f"      Found {data.get('workflowCount')} workflows:")
                    for i, wf in enumerate(data.get('workflows', []), 1):
                        print(f"         {i}. {wf['tag']} - {wf['text'][:50]}")
                    print(f"\n   HTML preview:")
                    print(f"   {data.get('innerHTML')}\n")
                    break
            
            time.sleep(2)
        else:
            print(f"\n   ⏱️  Timeout after {wait_seconds} seconds")
            print("   Workflows did not appear automatically\n")
            
            # Final check of page structure
            print("   Final page inspection:")
            final_result = client.eval_js(check_js)
            final_data = final_result.get('result', {})
            if final_data.get('found'):
                print(f"      innerHTML: {final_data.get('innerHTML')}\n")
        
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
    
    parser = argparse.ArgumentParser(description="Monitor workflow loading in Create tab")
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
    parser.add_argument(
        "--wait",
        type=int,
        default=30,
        help="Seconds to wait for workflows (default: 30)"
    )
    
    args = parser.parse_args()
    
    monitor_workflow_loading(
        webui_url=args.url,
        port=args.port,
        wait_seconds=args.wait
    )
