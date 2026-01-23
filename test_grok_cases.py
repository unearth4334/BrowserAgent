#!/usr/bin/env python3
"""
Test script to capture image-only and video+image cases from Grok tileview.
Displays ASCII tile layout and saves screenshots for each case type.
"""

import sys
from pathlib import Path
import requests
import time

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.browser.actions import Navigate, Screenshot, WaitForUser, ClickAtCoordinates
from browser_agent.config import Settings
from detect_grok_tiles import TileDetector


def print_ascii_tile_layout(tiles):
    """Print ASCII approximation of detected tile layout."""
    if not tiles:
        print("No tiles detected")
        return
    
    # Get dimensions
    all_tiles = [(x, y, x+w, y+h, i+1) for i, (x, y, w, h) in enumerate(tiles)]
    max_x = max(x2 for _, _, x2, _, _ in all_tiles)
    max_y = max(y2 for _, _, _, y2, _ in all_tiles)
    
    # Create grid (scale down to terminal size)
    grid_width = 80
    grid_height = 40
    scale_x = max_x / grid_width
    scale_y = max_y / grid_height
    
    # Initialize grid
    grid = [[' ' for _ in range(grid_width)] for _ in range(grid_height)]
    
    # Draw tiles
    for x1, y1, x2, y2, tile_num in all_tiles:
        # Scale coordinates
        gx1 = int(x1 / scale_x)
        gy1 = int(y1 / scale_y)
        gx2 = min(int(x2 / scale_x), grid_width - 1)
        gy2 = min(int(y2 / scale_y), grid_height - 1)
        
        # Fill tile area
        for gy in range(gy1, gy2 + 1):
            for gx in range(gx1, gx2 + 1):
                if gy < grid_height and gx < grid_width:
                    # Draw borders
                    if gy == gy1 or gy == gy2:
                        grid[gy][gx] = '─'
                    elif gx == gx1 or gx == gx2:
                        grid[gy][gx] = '│'
                    else:
                        grid[gy][gx] = '·'
        
        # Draw tile number in center
        center_y = (gy1 + gy2) // 2
        center_x = (gx1 + gx2) // 2
        tile_str = str(tile_num)
        start_x = center_x - len(tile_str) // 2
        
        if 0 <= center_y < grid_height:
            for i, char in enumerate(tile_str):
                x = start_x + i
                if 0 <= x < grid_width:
                    grid[center_y][x] = char
    
    # Print grid
    print("\n" + "=" * grid_width)
    print("Detected Tile Layout:")
    print("=" * grid_width)
    for row in grid:
        print(''.join(row))
    print("=" * grid_width + "\n")


def send_back_command():
    """Send back command to VNC browser using API."""
    try:
        response = requests.post("http://localhost:5000/macro/back", timeout=5)
        if response.status_code == 200:
            print("✅ Sent 'back' command via API")
            return True
        else:
            print(f"⚠️  API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send back command: {e}")
        return False


def main():
    print("🚀 Starting Grok case detection test...")
    print("This script will help identify image-only vs video+image cases\n")
    
    # Create screenshots directory
    screenshots_dir = Path("grok_test_screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    # Load environment settings
    env_settings = Settings.from_env()
    
    # Create browser controller with scaled viewport
    print("📂 Starting browser...")
    controller = PlaywrightBrowserController(
        executable_path=env_settings.browser_executable_path,
        headless=False,
        viewport_width=int(3840 * 0.65),  # Scaled viewport
        viewport_height=int(2160 * 0.65),
    )
    
    try:
        # Start browser
        controller.start()
        
        # Navigate to noVNC
        print("🌐 Navigating to noVNC...")
        controller.perform(Navigate(url="http://localhost:6080/vnc.html"))
        
        # Wait for user to show tileview
        print("\n⏸️  Please navigate to the Grok tileview in the VNC session...")
        controller.perform(WaitForUser("Press Enter once the Grok tileview is visible..."))
        
        # Take initial screenshot
        initial_screenshot = screenshots_dir / "tileview_layout.png"
        print(f"\n📸 Taking screenshot: {initial_screenshot}")
        controller.perform(Screenshot(path=str(initial_screenshot)))
        print("✅ Screenshot saved")
        
        # Detect tiles
        print("\n🔍 Detecting tiles...")
        detector = TileDetector(str(initial_screenshot))
        tiles = detector.detect_tiles(method="grid")
        
        if not tiles:
            print("❌ No tiles detected. Exiting.")
            return 1
        
        print(f"✅ Detected {len(tiles)} tiles")
        
        # Print ASCII layout
        print_ascii_tile_layout(tiles)
        
        # Print tile details
        print("Tile Details:")
        for i, (x, y, w, h) in enumerate(tiles, 1):
            center_x = int(x + w // 2)
            center_y = int(y + h // 2)
            print(f"  [{i}] Position: ({x}, {y}), Size: {w}x{h}, Center: ({center_x}, {center_y})")
        
        # === CASE 1: Image Only ===
        print("\n" + "="*80)
        print("CASE 1: IMAGE ONLY")
        print("="*80)
        tile_input = input("\nEnter tile number for IMAGE ONLY case (or 'skip' to skip): ").strip()
        
        if tile_input.lower() != 'skip':
            try:
                tile_num = int(tile_input)
                if 1 <= tile_num <= len(tiles):
                    x, y, w, h = tiles[tile_num - 1]
                    center_x = int(x + w // 2)
                    center_y = int(y + h // 2)
                    
                    print(f"\n🖱️  Clicking tile {tile_num} at ({center_x}, {center_y})...")
                    controller.perform(ClickAtCoordinates(x=center_x, y=center_y, button="left"))
                    time.sleep(0.5)  # Brief pause for page load
                    
                    print("\n⏸️  Please verify the image opened correctly in VNC...")
                    controller.perform(WaitForUser("Press Enter once the image is fully loaded..."))
                    
                    # Take screenshot
                    image_screenshot = screenshots_dir / "case_image_only.png"
                    print(f"\n📸 Taking screenshot: {image_screenshot}")
                    controller.perform(Screenshot(path=str(image_screenshot)))
                    print("✅ Screenshot saved")
                    
                    # Navigate back
                    print("\n⬅️  Navigating back to tileview...")
                    send_back_command()
                    time.sleep(1)  # Wait for navigation
                    
                    print("⏸️  Verify we're back at the tileview...")
                    controller.perform(WaitForUser("Press Enter once back at tileview..."))
                else:
                    print(f"❌ Invalid tile number. Must be 1-{len(tiles)}")
            except ValueError:
                print("❌ Invalid input. Must be a number or 'skip'")
        
        # === CASE 2: Video + Image ===
        print("\n" + "="*80)
        print("CASE 2: VIDEO + IMAGE")
        print("="*80)
        tile_input = input("\nEnter tile number for VIDEO+IMAGE case (or 'skip' to skip): ").strip()
        
        if tile_input.lower() != 'skip':
            try:
                tile_num = int(tile_input)
                if 1 <= tile_num <= len(tiles):
                    x, y, w, h = tiles[tile_num - 1]
                    center_x = int(x + w // 2)
                    center_y = int(y + h // 2)
                    
                    print(f"\n🖱️  Clicking tile {tile_num} at ({center_x}, {center_y})...")
                    controller.perform(ClickAtCoordinates(x=center_x, y=center_y, button="left"))
                    time.sleep(0.5)  # Brief pause for page load
                    
                    print("\n⏸️  Please verify the video+image opened correctly in VNC...")
                    controller.perform(WaitForUser("Press Enter once the video/image is fully loaded..."))
                    
                    # Take screenshot
                    video_screenshot = screenshots_dir / "case_video_image.png"
                    print(f"\n📸 Taking screenshot: {video_screenshot}")
                    controller.perform(Screenshot(path=str(video_screenshot)))
                    print("✅ Screenshot saved")
                    
                    # Navigate back
                    print("\n⬅️  Navigating back to tileview...")
                    send_back_command()
                    time.sleep(1)  # Wait for navigation
                    
                    print("⏸️  Verify we're back at the tileview...")
                    controller.perform(WaitForUser("Press Enter once back at tileview..."))
                else:
                    print(f"❌ Invalid tile number. Must be 1-{len(tiles)}")
            except ValueError:
                print("❌ Invalid input. Must be a number or 'skip'")
        
        print("\n✅ Test completed!")
        print(f"\nScreenshots saved in: {screenshots_dir}")
        print("  - tileview_layout.png (initial tile detection)")
        if (screenshots_dir / "case_image_only.png").exists():
            print("  - case_image_only.png")
        if (screenshots_dir / "case_video_image.png").exists():
            print("  - case_video_image.png")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        print("\n🛑 Stopping browser...")
        controller.stop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
