#!/usr/bin/env python3
"""Quick proof-of-concept test for Grok screenshot functionality."""

import os
import sys
from pathlib import Path

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.browser.actions import Navigate, Screenshot, WaitForSelector, WaitForUser
from browser_agent.config import Settings

def main():
    # Create screenshot directory
    screenshot_dir = Path("./grok_test_screenshots")
    screenshot_dir.mkdir(exist_ok=True)
    
    print("🚀 Starting Grok screenshot proof-of-concept...")
    
    # Get settings
    env_settings = Settings.from_env()
    
    # Create browser controller
    controller = PlaywrightBrowserController(
        executable_path=env_settings.browser_executable_path,
        headless=False,  # Keep visible for POC
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
        controller.perform(WaitForUser("Press Enter once the page has fully loaded..."))
        
        # Take screenshot
        screenshot_path = screenshot_dir / "novnc_poc.png"
        print(f"\n📸 Taking screenshot: {screenshot_path}")
        controller.perform(Screenshot(path=str(screenshot_path), full_page=False))
        
        # Check if screenshot was created
        if screenshot_path.exists():
            size_kb = screenshot_path.stat().st_size / 1024
            print(f"✅ Screenshot saved successfully! ({size_kb:.1f} KB)")
            print(f"   Location: {screenshot_path.absolute()}")
            
            # Get observation to verify
            obs = controller.get_observation()
            print(f"\n📊 Page Info:")
            print(f"   URL: {obs.url}")
            print(f"   Title: {obs.title}")
        else:
            print("❌ Screenshot file was not created")
            return 1
        
        print("\n✨ Proof-of-concept test completed successfully!")
        print("\nNext steps:")
        print("1. Open the screenshot to verify noVNC is visible")
        print("2. Implement vision analysis to detect VNC canvas and tiles")
        print("3. Test coordinate-based clicking on the canvas")
        
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
