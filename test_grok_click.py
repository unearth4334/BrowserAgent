#!/usr/bin/env python3
"""Test coordinate-based clicking in noVNC browser pane."""

import os
import sys
from pathlib import Path

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.browser.actions import Navigate, ClickAtCoordinates, WaitForUser, ExecuteJS
from browser_agent.config import Settings

def main():
    print("🚀 Starting Grok coordinate click test...")
    
    # Get settings
    env_settings = Settings.from_env()
    
    # Create browser controller
    controller = PlaywrightBrowserController(
        executable_path=env_settings.browser_executable_path,
        headless=False,  # Keep visible for testing
        viewport_width=3840*0.65,  # 4K resolution
        viewport_height=2160*0.65,
    )
    
    try:
        # Start browser
        print("📂 Starting browser...")
        controller.start()
        
        # Navigate to noVNC
        novnc_url = "http://localhost:6080/vnc.html"
        print(f"🌐 Navigating to {novnc_url}...")
        controller.perform(Navigate(novnc_url))
        
        # Wait for user to confirm page is ready
        print("\n⏸️  Browser opened to noVNC...")
        controller.perform(WaitForUser("Press Enter when ready to click in center..."))
        
        # Get viewport dimensions to calculate center
        print("\n📐 Getting viewport dimensions...")
        controller.perform(ExecuteJS(
            "JSON.stringify({width: window.innerWidth, height: window.innerHeight})"
        ))
        viewport_info = controller.get_last_js_result()
        print(f"   Viewport info: {viewport_info}")
        
        # Parse viewport size
        import json
        viewport = json.loads(viewport_info)
        center_x = viewport['width'] // 2
        center_y = viewport['height'] // 2
        
        print(f"\n🎯 Clicking at center coordinates: ({center_x}, {center_y})")
        controller.perform(ClickAtCoordinates(x=center_x, y=center_y, button="left"))
        
        print("✅ Click executed successfully!")
        print("\nCheck the VNC session to see if the click was registered.")
        print("(You should see a click event in the containerized browser)")
        
        # Keep browser open for a moment to observe
        print("\n⏸️  Keeping browser open for observation...")
        controller.perform(WaitForUser("Press Enter to close browser..."))
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Stop browser
        print("\n🛑 Stopping browser...")
        controller.stop()

if __name__ == "__main__":
    sys.exit(main())
