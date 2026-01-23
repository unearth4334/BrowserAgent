#!/usr/bin/env python3
"""
Interactive test app for Grok browser automation.
Combines tile detection, media pane detection, and browser control.
"""

import sys
import time
from pathlib import Path
import cv2
import numpy as np
from typing import Optional, List, Tuple

from playwright.sync_api import sync_playwright, Page, Browser
from detect_grok_tiles import TileDetector
from detect_widest_region import WidestRegionDetector


class GrokTestApp:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.novnc_url = "http://localhost:6080/vnc.html?autoconnect=true"
        self.detected_tiles: List[Tuple[int, int, int, int]] = []
        self.last_screenshot_path: Optional[str] = None
        
    def start_browser(self):
        """Initialize browser and navigate to noVNC page."""
        print("🌐 Starting browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        context = self.browser.new_context(
            viewport={'width': 2496, 'height': 1404},
            no_viewport=False
        )
        self.page = context.new_page()
        
        print(f"📍 Navigating to {self.novnc_url}")
        self.page.goto(self.novnc_url)
        time.sleep(2)  # Wait for noVNC to initialize
        print("✅ Browser ready")
        
    def close_browser(self):
        """Close browser and cleanup."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("🔒 Browser closed")
    
    def capture_screenshot(self, filename: str = "screenshot.png") -> str:
        """Capture screenshot of current page."""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        screenshot_path = f"grok_test_screenshots/{filename}"
        Path("grok_test_screenshots").mkdir(exist_ok=True)
        
        self.page.screenshot(path=screenshot_path, full_page=False)
        self.last_screenshot_path = screenshot_path
        print(f"📸 Screenshot saved to {screenshot_path}")
        return screenshot_path
    
    def detect_and_display_tiles(self):
        """Detect tiles and display results."""
        print("\n" + "="*80)
        print("TILE DETECTION")
        print("="*80)
        
        # Capture screenshot
        screenshot_path = self.capture_screenshot("tiles_detection.png")
        
        # Detect tiles
        detector = TileDetector(screenshot_path)
        tiles = detector.detect_tiles(method="grid")
        self.detected_tiles = tiles
        
        if not tiles:
            print("⚠️  No tiles detected")
            return
        
        print(f"\n✅ Detected {len(tiles)} tiles")
        
        # Draw rectangles on screenshot
        image = cv2.imread(screenshot_path)
        for idx, (x, y, w, h) in enumerate(tiles, 1):
            # Draw rectangle
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 3)
            
            # Draw tile number
            center_x = x + w // 2
            center_y = y + h // 2
            
            # Background for text
            text = str(idx)
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 2
            thickness = 3
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            
            # Draw white background
            bg_x1 = center_x - text_size[0] // 2 - 10
            bg_y1 = center_y - text_size[1] // 2 - 10
            bg_x2 = center_x + text_size[0] // 2 + 10
            bg_y2 = center_y + text_size[1] // 2 + 10
            cv2.rectangle(image, (bg_x1, bg_y1), (bg_x2, bg_y2), (255, 255, 255), -1)
            
            # Draw number
            text_x = center_x - text_size[0] // 2
            text_y = center_y + text_size[1] // 2
            cv2.putText(image, text, (text_x, text_y), font, font_scale, (0, 0, 255), thickness)
            
            # Print tile info
            area_pct = (w * h) / (image.shape[1] * image.shape[0]) * 100
            print(f"  Tile {idx:2d}: ({x:4d}, {y:4d}) {w:3d}x{h:3d} - center: ({center_x:4d}, {center_y:4d}) - area: {area_pct:4.1f}%")
        
        # Save and display
        output_path = "grok_test_screenshots/tiles_detected.png"
        cv2.imwrite(output_path, image)
        print(f"\n📺 Showing result: {output_path}")
        
        # Display image
        cv2.imshow("Detected Tiles", image)
        print("Press any key to close the window...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def click_tile(self, tile_index: int):
        """Click on a tile by index."""
        if not self.detected_tiles:
            print("⚠️  No tiles detected. Run 'Detect tiles' first.")
            return
        
        if tile_index < 1 or tile_index > len(self.detected_tiles):
            print(f"⚠️  Invalid tile index. Must be between 1 and {len(self.detected_tiles)}")
            return
        
        x, y, w, h = self.detected_tiles[tile_index - 1]
        center_x = x + w // 2
        center_y = y + h // 2
        
        print(f"🖱️  Clicking tile {tile_index} at ({center_x}, {center_y})")
        self.page.mouse.click(center_x, center_y)
        time.sleep(0.5)
        print("✅ Click completed")
    
    def detect_and_display_media_pane(self):
        """Detect media pane and display results."""
        print("\n" + "="*80)
        print("MEDIA PANE DETECTION")
        print("="*80)
        
        # Capture screenshot
        screenshot_path = self.capture_screenshot("media_pane_detection.png")
        
        # Detect media pane using widest region detector
        detector = WidestRegionDetector(screenshot_path)
        result = detector.detect_bounds()
        
        if not result:
            print("⚠️  No media pane detected")
            return
        
        x, y, w, h = result
        print(f"\n✅ Detected media pane: ({x}, {y}) {w}x{h}")
        
        # Draw rectangle on screenshot
        image = cv2.imread(screenshot_path)
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 4)
        
        # Add label
        label = "MEDIA PANE"
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(image, label, (x + 10, y + 40), font, 1.5, (0, 0, 255), 3)
        
        # Calculate area percentage
        area_pct = (w * h) / (image.shape[1] * image.shape[0]) * 100
        print(f"  Area: {area_pct:.1f}% of screen")
        
        # Save and display
        output_path = "grok_test_screenshots/media_pane_detected.png"
        cv2.imwrite(output_path, image)
        print(f"\n📺 Showing result: {output_path}")
        
        # Display image
        cv2.imshow("Detected Media Pane", image)
        print("Press any key to close the window...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def api_command_menu(self):
        """Submenu for API commands."""
        api_commands = [
            "Navigate to page",
            "Click button",
            "Type text",
            "Press key",
            "Wait for element",
            "Get page title",
            "Go back",
            "Reload page",
            "Change background color"
        ]
        
        while True:
            print("\n" + "="*80)
            print("API COMMANDS")
            print("="*80)
            for idx, cmd in enumerate(api_commands, 1):
                print(f"  {idx}. {cmd}")
            print("  0. Back to main menu")
            print("="*80)
            
            choice = input("Select API command: ").strip()
            
            if choice == "0":
                break
            
            try:
                cmd_idx = int(choice)
                if 1 <= cmd_idx <= len(api_commands):
                    self.execute_api_command(cmd_idx, api_commands[cmd_idx - 1])
                else:
                    print("⚠️  Invalid choice")
            except ValueError:
                print("⚠️  Please enter a number")
    
    def execute_api_command(self, cmd_idx: int, cmd_name: str):
        """Execute selected API command."""
        print(f"\n🔧 Executing: {cmd_name}")
        
        if cmd_idx == 1:  # Navigate to page
            url = input("Enter URL: ").strip()
            if url:
                self.page.goto(url)
                print(f"✅ Navigated to {url}")
        
        elif cmd_idx == 2:  # Click button
            selector = input("Enter button selector (e.g., 'button', '.class', '#id'): ").strip()
            if selector:
                try:
                    self.page.click(selector)
                    print(f"✅ Clicked {selector}")
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        elif cmd_idx == 3:  # Type text
            selector = input("Enter input selector: ").strip()
            text = input("Enter text to type: ").strip()
            if selector and text:
                try:
                    self.page.fill(selector, text)
                    print(f"✅ Typed '{text}' into {selector}")
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        elif cmd_idx == 4:  # Press key
            key = input("Enter key to press (e.g., 'Enter', 'Escape', 'F11'): ").strip()
            if key:
                self.page.keyboard.press(key)
                print(f"✅ Pressed {key}")
        
        elif cmd_idx == 5:  # Wait for element
            selector = input("Enter selector to wait for: ").strip()
            timeout = input("Enter timeout in seconds (default 30): ").strip()
            timeout_ms = int(timeout) * 1000 if timeout else 30000
            if selector:
                try:
                    self.page.wait_for_selector(selector, timeout=timeout_ms)
                    print(f"✅ Element {selector} appeared")
                except Exception as e:
                    print(f"❌ Timeout or error: {e}")
        
        elif cmd_idx == 6:  # Get page title
            title = self.page.title()
            print(f"📄 Page title: {title}")
        
        elif cmd_idx == 7:  # Go back
            self.page.go_back()
            print("✅ Went back")
        
        elif cmd_idx == 8:  # Reload page
            self.page.reload()
            print("✅ Page reloaded")
        
        elif cmd_idx == 9:  # Change background color
            import requests
            color = input("Enter color (hex like #ff0000 or name like 'lightblue'): ").strip()
            if color:
                try:
                    response = requests.post(
                        'http://localhost:5000/background',
                        headers={'Content-Type': 'application/json'},
                        json={'color': color},
                        timeout=5
                    )
                    if response.status_code == 200:
                        print(f"✅ Changed background to {color}")
                    else:
                        error_text = response.text
                        print(f"❌ API error: {error_text}")
                        
                        # Check for common remote-allow-origins error
                        if 'remote-allow-origins' in error_text.lower() or '403' in str(response.status_code):
                            print("\n⚠️  Chrome needs --remote-allow-origins flag")
                            print("To fix this, Chrome must be launched with:")
                            print("  --remote-allow-origins=* or --remote-allow-origins=http://localhost:9222")
                            print("\nIf using Docker, add this to Chrome launch args in your Dockerfile/compose file.")
                        
                except requests.exceptions.ConnectionError:
                    print("❌ Cannot connect to API server at http://localhost:5000")
                    print("   Make sure the Docker container is running")
                except requests.exceptions.Timeout:
                    print("❌ API request timed out")
                except Exception as e:
                    print(f"❌ Error: {e}")
    
    def main_menu(self):
        """Display main menu and handle user input."""
        while True:
            print("\n" + "="*80)
            print("GROK TEST APP - MAIN MENU")
            print("="*80)
            print("  1. API Command")
            print("  2. Detect Tiles")
            print("  3. Click Tile")
            print("  4. Detect Media Pane")
            print("  5. Capture Screenshot")
            print("  6. Open Grok (navigate to Grok)")
            print("  0. Exit")
            print("="*80)
            
            choice = input("Select option: ").strip()
            
            if choice == "0":
                print("\n👋 Exiting...")
                break
            
            elif choice == "1":
                self.api_command_menu()
            
            elif choice == "2":
                self.detect_and_display_tiles()
            
            elif choice == "3":
                if not self.detected_tiles:
                    print("⚠️  No tiles detected. Run 'Detect tiles' first.")
                else:
                    print(f"\nAvailable tiles: 1-{len(self.detected_tiles)}")
                    tile_num = input("Enter tile number to click: ").strip()
                    try:
                        self.click_tile(int(tile_num))
                    except ValueError:
                        print("⚠️  Please enter a valid number")
            
            elif choice == "4":
                self.detect_and_display_media_pane()
            
            elif choice == "5":
                filename = input("Enter filename (default: screenshot.png): ").strip()
                if not filename:
                    filename = "screenshot.png"
                self.capture_screenshot(filename)
            
            elif choice == "6":
                grok_url = input("Enter Grok URL (default: https://grok.x.com): ").strip()
                if not grok_url:
                    grok_url = "https://grok.x.com"
                print(f"🌐 Navigating to {grok_url}")
                self.page.goto(grok_url)
                time.sleep(2)
                print("✅ Navigation complete")
            
            else:
                print("⚠️  Invalid choice")
    
    def run(self):
        """Main application entry point."""
        try:
            self.start_browser()
            self.main_menu()
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close_browser()


def main():
    """Entry point."""
    print("="*80)
    print("GROK TEST APP")
    print("Interactive testing for Grok browser automation")
    print("="*80)
    
    app = GrokTestApp()
    app.run()


if __name__ == "__main__":
    main()
