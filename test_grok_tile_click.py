#!/usr/bin/env python3
"""Test automated tile clicking in Grok via noVNC."""

import sys
from pathlib import Path

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.browser.actions import Navigate, Screenshot, ClickAtCoordinates, WaitForUser
from browser_agent.config import Settings
from detect_grok_tiles import TileDetector


def main():
    screenshot_dir = Path("./grok_test_screenshots")
    screenshot_dir.mkdir(exist_ok=True)
    screenshot_path = screenshot_dir / "click_test.png"
    
    print("🚀 Starting automated tile clicking test...")
    
    # Get settings
    env_settings = Settings.from_env()
    
    # Create browser controller
    # Viewport scaled to 0.65 of 4K (3840x2160)
    controller = PlaywrightBrowserController(
        executable_path=env_settings.browser_executable_path,
        headless=False,
        viewport_width=2496,  # 3840 * 0.65
        viewport_height=1404,  # 2160 * 0.65
    )
    
    try:
        # Start browser
        print("📂 Starting browser...")
        controller.start()
        
        # Navigate to noVNC
        novnc_url = "http://localhost:6080/vnc.html"
        print(f"🌐 Navigating to {novnc_url}...")
        controller.perform(Navigate(novnc_url))
        
        # Wait for user confirmation
        print("\n⏸️  Browser opened to noVNC...")
        controller.perform(WaitForUser("Press Enter once the Grok tileview is visible..."))
        
        # Take screenshot
        print(f"\n📸 Taking screenshot: {screenshot_path}")
        controller.perform(Screenshot(path=str(screenshot_path), full_page=False))
        print(f"✅ Screenshot saved")
        
        # Detect tiles
        print("\n🔍 Detecting tiles...")
        detector = TileDetector(str(screenshot_path))
        tiles = detector.detect_tiles(bg_color_hex="fcfcfc", method="grid")
        
        if not tiles:
            print("❌ No tiles detected. Exiting.")
            return 1
        
        print(f"\n✨ Found {len(tiles)} tiles")
        
        # Get tile 1 (first tile)
        tile_num = 1
        if tile_num > len(tiles):
            print(f"❌ Tile {tile_num} does not exist (only {len(tiles)} tiles detected)")
            return 1
        
        x, y, w, h = tiles[tile_num - 1]
        # Convert to regular Python int (from numpy.int32) for JSON serialization
        center_x = int(x + w // 2)
        center_y = int(y + h // 2)
        
        print(f"\n🎯 Tile {tile_num} details:")
        print(f"   Position: ({x}, {y})")
        print(f"   Size: {w}x{h}")
        print(f"   Center: ({center_x}, {center_y})")
        
        # Confirm before clicking
        controller.perform(WaitForUser(f"\nPress Enter to click tile {tile_num} at center ({center_x}, {center_y})..."))
        
        # Click the tile center
        print(f"\n🖱️  Clicking tile {tile_num}...")
        controller.perform(ClickAtCoordinates(x=center_x, y=center_y, button="left"))
        print("✅ Click executed!")
        
        # Keep browser open to observe result
        print("\n⏸️  Check the VNC session to see if tile was clicked correctly...")
        controller.perform(WaitForUser("Press Enter to close browser..."))
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        print("\n🛑 Stopping browser...")
        controller.stop()


if __name__ == "__main__":
    sys.exit(main())
