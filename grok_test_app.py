#!/usr/bin/env python3
"""
Interactive test app for Grok browser automation.
Combines tile detection, media pane detection, and browser control.
"""

import sys
import time
import re
from pathlib import Path
import cv2
import numpy as np
from typing import Optional, List, Tuple, Dict

from playwright.sync_api import sync_playwright, Page, Browser
from detect_grok_tiles import TileDetector
from detect_widest_region import WidestRegionDetector
from detect_with_background_toggle import RobustTileDetector, RobustMediaPaneDetector
from detect_tiles_from_html import detect_tiles_from_html
from visualize_html_detection import visualize_html_detection
from tile_hash_db import TileHashDatabase
from tile_hash_db import TileHashDatabase


class GrokTestApp:
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.novnc_url = "http://localhost:6080/vnc.html?autoconnect=true"
        self.detected_tiles: List[Tuple[int, int, int, int]] = []
        self.last_screenshot_path: Optional[str] = None
        self.tile_db = TileHashDatabase("grok_tiles.db")
        self.tile_db = TileHashDatabase("grok_tiles.db")
        
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
        if hasattr(self, 'tile_db'):
            self.tile_db.close()
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
    
    def detect_and_display_tiles(self, use_robust: bool = False):
        """Detect tiles and display results.
        
        Args:
            use_robust: If True, use background toggle method, else use traditional method
        """
        print("\n" + "="*80)
        if use_robust:
            print("TILE DETECTION (Robust - Background Toggle)")
        else:
            print("TILE DETECTION (Traditional)")
        print("="*80)
        
        if use_robust:
            # Use robust background toggle detection
            def capture_func():
                """Capture screenshot and return as numpy array."""
                screenshot_path = self.capture_screenshot("temp_capture.png")
                return cv2.imread(screenshot_path)
            
            detector = RobustTileDetector(capture_func)
            tiles = detector.detect_tiles_with_grid(show_diagnostic=True)
            self.detected_tiles = tiles
            
            if not tiles:
                print("⚠️  No tiles detected")
                return
            
            # Get the most recent screenshot for visualization
            screenshot_path = self.last_screenshot_path or "grok_test_screenshots/temp_capture.png"
            image = cv2.imread(screenshot_path)
        else:
            # Traditional detection
            screenshot_path = self.capture_screenshot("tiles_detection.png")
            detector = TileDetector(screenshot_path)
            tiles = detector.detect_tiles(method="grid")
            self.detected_tiles = tiles
            
            if not tiles:
                print("⚠️  No tiles detected")
                return
            
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
    
    def diagnose_tiles(self, api_url: str = "http://localhost:5000"):
        """Diagnose tile detection by inspecting DOM."""
        print("\n" + "="*80)
        print("TILE DIAGNOSTIC")
        print("="*80)
        
        # JavaScript to inspect tiles in the DOM
        js_code = """
        (function() {
            const tiles = document.querySelectorAll('[role="listitem"]');
            const tileInfo = [];
            
            tiles.forEach((tile, idx) => {
                const style = tile.getAttribute('style') || '';
                const rect = tile.getBoundingClientRect();
                const imgs = tile.querySelectorAll('img');
                const videos = tile.querySelectorAll('video');
                
                tileInfo.push({
                    index: idx + 1,
                    style: style.substring(0, 100),
                    visible: rect.width > 0 && rect.height > 0,
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    numImages: imgs.length,
                    numVideos: videos.length
                });
            });
            
            return {
                totalTiles: tiles.length,
                tiles: tileInfo.slice(0, 10)  // First 10 tiles
            };
        })();
        """
        
        try:
            import requests
            response = requests.post(
                f"{api_url}/execute",
                json={"code": js_code},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # API returns: {'status': 'ok', 'result': {'type': 'object', 'value': {...}}}
                result = data.get('result', {})
                
                if result.get('type') == 'object' and 'value' in result:
                    info = result['value']
                    print(f"\n📊 Found {info.get('totalTiles', 0)} tiles in DOM")
                    print(f"\n🔍 First {len(info.get('tiles', []))} tiles:")
                    
                    for tile in info.get('tiles', []):
                        print(f"\n  Tile {tile['index']}:")
                        print(f"    Position: ({tile['x']}, {tile['y']})")
                        print(f"    Size: {tile['width']}x{tile['height']}")
                        print(f"    Visible: {tile['visible']}")
                        print(f"    Images: {tile['numImages']}, Videos: {tile['numVideos']}")
                        print(f"    Style: {tile['style']}...")
                else:
                    print(f"⚠️  Unexpected result format")
                    print(f"   Result type: {result.get('type')}")
                    print(f"   Has value: {'value' in result}")
                    print(f"   Full response: {data}")
            else:
                print(f"❌ API error: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Error diagnosing tiles: {e}")
            import traceback
            traceback.print_exc()
    
    def click_tile(self, tile_index: int, api_url: str = "http://localhost:5000"):
        """Click on a tile by index using JavaScript via API."""
        if not self.detected_tiles:
            print("⚠️  No tiles detected. Run 'Detect tiles' first.")
            return
        
        if tile_index < 1 or tile_index > len(self.detected_tiles):
            print(f"⚠️  Invalid tile index. Must be between 1 and {len(self.detected_tiles)}")
            return
        
        print(f"🖱️  Clicking tile {tile_index} using JavaScript...")
        
        # Use JavaScript to click the tile directly in the DOM
        # Tiles are identified by role='listitem' and we select by index (0-based)
        js_code = f"""
        (function() {{
            const tiles = document.querySelectorAll('[role="listitem"]');
            console.log('Total tiles found:', tiles.length);
            console.log('Attempting to click tile index:', {tile_index - 1});
            
            if (tiles.length >= {tile_index}) {{
                const tile = tiles[{tile_index - 1}];
                const rect = tile.getBoundingClientRect();
                console.log('Tile rect:', rect);
                console.log('Tile visible:', rect.width > 0 && rect.height > 0);
                
                tile.click();
                console.log('Click executed on tile', {tile_index});
                
                return {{
                    success: true,
                    index: {tile_index},
                    total: tiles.length,
                    rect: {{
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    }}
                }};
            }} else {{
                console.error('Tile not found! Requested:', {tile_index}, 'Available:', tiles.length);
                return {{
                    success: false,
                    error: 'Tile not found',
                    requested: {tile_index},
                    total: tiles.length
                }};
            }}
        }})();
        """
        
        try:
            import requests
            response = requests.post(
                f"{api_url}/execute",
                json={"code": js_code},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Debug: show what we got
                print(f"   DEBUG: Response keys: {list(data.keys())}")
                
                result = data.get('result', {})
                print(f"   DEBUG: Result type in response: {result.get('type') if isinstance(result, dict) else 'N/A'}")
                
                # Extract the returned value
                if isinstance(result, dict) and result.get('type') == 'object' and 'value' in result:
                    result_value = result['value']
                    if isinstance(result_value, dict):
                        if result_value.get('success'):
                            print(f"✅ Tile {tile_index} clicked successfully")
                            if 'rect' in result_value:
                                rect = result_value['rect']
                                print(f"   Position: ({rect['x']}, {rect['y']})")
                                print(f"   Size: {rect['width']}x{rect['height']}")
                            print(f"   Total tiles in DOM: {result_value.get('total', 'unknown')}")
                        else:
                            print(f"❌ Click failed!")
                            print(f"   Error: {result_value.get('error', 'Unknown')}")
                            print(f"   Requested: {result_value.get('requested', tile_index)}")
                            print(f"   Available: {result_value.get('total', 'unknown')}")
                    else:
                        print(f"⚠️  Unexpected result value type: {type(result_value)}")
                        print(f"   Value: {result_value}")
                else:
                    print(f"⚠️  Unexpected response structure")
                    print(f"   Result type: {result.get('type') if isinstance(result, dict) else type(result)}")
                    print(f"   Result is dict: {isinstance(result, dict)}")
                    print(f"   Has 'value' key: {'value' in result if isinstance(result, dict) else False}")
                    print(f"   Full data keys: {list(data.keys())}")
                    print(f"   Full data: {data}")
            else:
                print(f"❌ API error: HTTP {response.status_code}")
                print(f"   Response: {response.text[:500]}")
        except Exception as e:
            print(f"❌ Error clicking tile: {e}")
        
        time.sleep(0.5)
        print("✅ Click completed")

    def analyze_current_page_for_video_indicator(self):
        """Fetch page HTML via API and detect video indicator in media pane."""
        print("\n" + "="*80)
        print("MEDIA PANE VIDEO ANALYSIS")
        print("="*80)
        # Small delay to allow content to load after click
        time.sleep(1.5)

        api_url = "http://localhost:5000"
        try:
            import requests
            print("\n🌐 Fetching page source...")
            resp = requests.get(f"{api_url}/page-source", timeout=10)
            if resp.status_code != 200:
                print(f"❌ HTTP error: {resp.status_code}")
                print(f"   Response: {resp.text[:200]}")
                return

            data = resp.json()
            html = data.get('html') or ''
            if not html:
                print("⚠️  Empty HTML returned")
                return

            print("📄 Analyzing HTML for video indicators...")
            
            # Primary indicators (strong signals)
            primary_patterns = {
                'video_tag': r"<video\b[^>]*>",
                'video_source': r'<source[^>]+src\s*=\s*"[^"]+\.(mp4|webm)',
            }
            
            # Secondary indicators (need context from primary)
            secondary_patterns = {
                'svg_video_icon': r'<svg[^>]*>\s*<use[^>]*xlink:href\s*=\s*"[^"]*video',
                'video_button': r'<button[^>]*aria-label\s*=\s*"[^"]*video[^"]*play',
            }
            
            primary_matches = []
            secondary_matches = []
            
            for name, pat in primary_patterns.items():
                if re.search(pat, html, flags=re.IGNORECASE):
                    print(f"   ✅ Primary match: {name}")
                    primary_matches.append(name)
            
            for name, pat in secondary_patterns.items():
                if re.search(pat, html, flags=re.IGNORECASE):
                    print(f"   ℹ️  Secondary match: {name}")
                    secondary_matches.append(name)
            
            # Decision logic: need at least one primary match
            if primary_matches:
                print("\n🎬 Video component detected")
            elif secondary_matches:
                print("\n⚠️  Video indicators found but no video element")
            else:
                print("\n🖼️  No video component found")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def scan_tiles_with_hash_detection(
        self,
        tiles: List[Dict],
        viewport_offset: Tuple[int, int],
        scale_factor: Tuple[float, float],
        api_url: str = "http://localhost:5000"
    ) -> Tuple[int, int]:
        """
        Scan tiles with intelligent hash-based detection.
        Stops when 3 consecutive tiles are unchanged.
        
        Args:
            tiles: List of tile metadata dicts
            viewport_offset: (x, y) viewport offset
            scale_factor: (x_scale, y_scale) scaling
            api_url: API server URL
            
        Returns:
            Tuple of (tiles_processed, stop_position)
        """
        import requests
        import base64
        
        print("\n" + "="*80)
        print("INTELLIGENT TILE SCANNING")
        print("="*80)
        print(f"Total tiles found: {len(tiles)}")
        print("Strategy: Stop at 3 consecutive unchanged tiles")
        
        # Compute hashes incrementally and check for stop condition
        print("\n🔑 Computing tile hashes incrementally...")
        tile_hashes = []
        stop_pos = None
        required_consecutive = 3
        
        for idx, tile in enumerate(tiles, 1):
            url = tile.get('thumbnail_url')
            if not url:
                tile_hashes.append(None)
                print(f"  Tile {idx}: No thumbnail URL")
            else:
                try:
                    resp = requests.post(
                        f"{api_url}/fetch-image",
                        json={"url": url},
                        timeout=20
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get('status') == 'ok' and 'data' in data:
                            img_bytes = base64.b64decode(data['data'])
                            tile_hash = self.tile_db.compute_tile_hash(img_bytes)
                            tile_hashes.append(tile_hash)
                            print(f"  Tile {idx}: {tile_hash}")
                        else:
                            tile_hashes.append(None)
                            print(f"  Tile {idx}: API error")
                    else:
                        tile_hashes.append(None)
                        print(f"  Tile {idx}: HTTP {resp.status_code}")
                except Exception as e:
                    tile_hashes.append(None)
                    print(f"  Tile {idx}: Error - {e}")
            
            # Check if we have enough hashes to check for stop condition
            if idx >= required_consecutive:
                # Check if we found N consecutive unchanged tiles
                for start_pos in range(1, idx - required_consecutive + 2):
                    if self.tile_db.check_consecutive_unchanged(tile_hashes, start_pos, required_consecutive):
                        stop_pos = start_pos + required_consecutive - 1
                        print(f"\n✋ Found {required_consecutive} consecutive unchanged tiles!")
                        print(f"   Stopping at position {stop_pos} (tiles 1-{stop_pos} processed)")
                        break
                
                if stop_pos:
                    break
            
            # 2 second delay between requests
            if idx < len(tiles):
                time.sleep(2)
        
        if not stop_pos:
            print(f"\n📝 No stopping point found, processed all {len(tile_hashes)} tiles")
            stop_pos = len(tile_hashes)
        
        tiles_to_process = stop_pos
        
        # Process new/modified tiles
        print(f"\n🔄 Updating database...")
        new_count = 0
        
        for idx in range(1, tiles_to_process + 1):
            if idx - 1 >= len(tile_hashes) or tile_hashes[idx - 1] is None:
                continue
            
            tile_hash = tile_hashes[idx - 1]
            tile = tiles[idx - 1]
            
            # Check if this is new or moved
            existing = self.tile_db.get_tile_by_hash(tile_hash)
            if not existing or existing['position'] != idx:
                self.tile_db.add_or_update_tile(
                    tile_hash=tile_hash,
                    position=idx,
                    thumbnail_url=tile.get('thumbnail_url'),
                    has_video=tile.get('has_video', False),
                    processed=False
                )
                new_count += 1
        
        # Record scan
        self.tile_db.record_scan(
            tiles_found=len(tiles),
            new_tiles=new_count,
            stopped_at_position=stop_pos
        )
        
        # Show stats
        stats = self.tile_db.get_stats()
        print(f"\n📊 Database stats:")
        print(f"   Total tiles in DB: {stats['total_tiles']}")
        print(f"   Processed: {stats['processed_tiles']}")
        print(f"   Unprocessed: {stats['unprocessed_tiles']}")
        print(f"   New/modified this scan: {new_count}")
        
        return tiles_to_process, stop_pos or len(tiles)
    
    def detect_and_display_media_pane(self, use_robust: bool = False):
        """Detect media pane and display results.
        
        Args:
            use_robust: If True, use background toggle method, else use traditional method
        """
        print("\n" + "="*80)
        if use_robust:
            print("MEDIA PANE DETECTION (Robust - Background Toggle)")
        else:
            print("MEDIA PANE DETECTION (Traditional)")
        print("="*80)
        
        if use_robust:
            # Use robust background toggle detection
            def capture_func():
                """Capture screenshot and return as numpy array."""
                screenshot_path = self.capture_screenshot("temp_capture_media.png")
                return cv2.imread(screenshot_path)
            
            detector = RobustMediaPaneDetector(capture_func)
            result = detector.detect_bounds()
            
            if not result:
                print("⚠️  No media pane detected")
                return
            
            # Get the most recent screenshot for visualization
            screenshot_path = self.last_screenshot_path or "grok_test_screenshots/temp_capture_media.png"
        else:
            # Traditional detection
            screenshot_path = self.capture_screenshot("media_pane_detection.png")
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
        """Submenu for API commands that control the noVNC container browser."""
        api_commands = [
            "Navigate to page (focus address + type URL)",
            "Click element (via JavaScript)",
            "Type text",
            "Press key combination",
            "Wait (sleep)",
            "Get page title (via JavaScript)",
            "Go back (Alt+Left macro)",
            "Reload page (Ctrl+R macro)",
            "Change background color (DevTools API)"
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
        """Execute selected API command using REST API to noVNC container."""
        import requests
        print(f"\n🔧 Executing: {cmd_name}")
        
        if cmd_idx == 1:  # Navigate to page
            url = input("Enter URL: ").strip()
            if url:
                try:
                    # Use focus_address macro + type + enter
                    response = requests.post('http://localhost:5000/macro/focus_address', timeout=5)
                    if response.status_code == 200:
                        time.sleep(0.5)
                        response = requests.post(
                            'http://localhost:5000/type',
                            headers={'Content-Type': 'application/json'},
                            json={'text': url},
                            timeout=5
                        )
                        if response.status_code == 200:
                            time.sleep(0.3)
                            response = requests.post('http://localhost:5000/macro/enter', timeout=5)
                            if response.status_code == 200:
                                print(f"✅ Navigated to {url}")
                            else:
                                print(f"❌ Failed to press Enter: {response.text}")
                        else:
                            print(f"❌ Failed to type URL: {response.text}")
                    else:
                        print(f"❌ Failed to focus address bar: {response.text}")
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        elif cmd_idx == 2:  # Click button
            selector = input("Enter button selector (e.g., 'button', '.class', '#id'): ").strip()
            if selector:
                try:
                    # Use JavaScript execution to click
                    code = f'document.querySelector("{selector}").click()'
                    response = requests.post(
                        'http://localhost:5000/execute',
                        headers={'Content-Type': 'application/json'},
                        json={'code': code},
                        timeout=5
                    )
                    if response.status_code == 200:
                        print(f"✅ Clicked {selector}")
                    else:
                        print(f"❌ API error: {response.text}")
                        self._show_api_fix_hint(response)
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        elif cmd_idx == 3:  # Type text
            text = input("Enter text to type: ").strip()
            if text:
                try:
                    response = requests.post(
                        'http://localhost:5000/type',
                        headers={'Content-Type': 'application/json'},
                        json={'text': text},
                        timeout=5
                    )
                    if response.status_code == 200:
                        print(f"✅ Typed '{text}'")
                    else:
                        print(f"❌ API error: {response.text}")
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        elif cmd_idx == 4:  # Press key
            key = input("Enter key to press (e.g., 'Return', 'Escape', 'F11'): ").strip()
            if key:
                try:
                    response = requests.post(
                        'http://localhost:5000/keys',
                        headers={'Content-Type': 'application/json'},
                        json={'keys': key},
                        timeout=5
                    )
                    if response.status_code == 200:
                        print(f"✅ Pressed {key}")
                    else:
                        print(f"❌ API error: {response.text}")
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        elif cmd_idx == 5:  # Wait
            seconds = input("Enter seconds to wait (default 2): ").strip()
            wait_time = float(seconds) if seconds else 2.0
            print(f"⏳ Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            print(f"✅ Waited {wait_time} seconds")
        
        elif cmd_idx == 6:  # Get page title
            try:
                code = 'document.title'
                response = requests.post(
                    'http://localhost:5000/execute',
                    headers={'Content-Type': 'application/json'},
                    json={'code': code},
                    timeout=5
                )
                if response.status_code == 200:
                    result = response.json()
                    title = result.get('result', {}).get('value', 'N/A')
                    print(f"📄 Page title: {title}")
                else:
                    print(f"❌ API error: {response.text}")
                    self._show_api_fix_hint(response)
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif cmd_idx == 7:  # Go back
            try:
                response = requests.post('http://localhost:5000/macro/back', timeout=5)
                if response.status_code == 200:
                    print("✅ Went back")
                else:
                    print(f"❌ API error: {response.text}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif cmd_idx == 8:  # Reload page
            try:
                response = requests.post('http://localhost:5000/macro/refresh', timeout=5)
                if response.status_code == 200:
                    print("✅ Page reloaded")
                else:
                    print(f"❌ API error: {response.text}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif cmd_idx == 9:  # Change background color
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
                        print(f"❌ API error: {response.text}")
                        self._show_api_fix_hint(response)
                        
                except requests.exceptions.ConnectionError:
                    print("❌ Cannot connect to API server at http://localhost:5000")
                    print("   Make sure the Docker container is running")
                except requests.exceptions.Timeout:
                    print("❌ API request timed out")
                except Exception as e:
                    print(f"❌ Error: {e}")
    
    def _show_api_fix_hint(self, response):
        """Show hint for common API errors."""
        error_text = response.text
        # Check for common remote-allow-origins error
        if 'remote-allow-origins' in error_text.lower() or '403' in str(response.status_code):
            print("\n⚠️  Chrome needs --remote-allow-origins flag")
            print("To fix this, Chrome must be launched with:")
            print("  --remote-allow-origins=* or --remote-allow-origins=http://localhost:9222")
            print("\nIf using Docker, add this to Chrome launch args in your Dockerfile/compose file.")
            print("See CHROME_DEVTOOLS_FIX.md for detailed instructions.")
    
    def detect_tiles_html(self):
        """Detect tiles using HTML parsing with scaling support."""
        print("\n" + "="*80)
        print("HTML-BASED TILE DETECTION")
        print("="*80)
        
        try:
            # Get viewport offset and scale
            print("\nViewport offset and scale configuration:")
            print("  Calibrated defaults: offset=(118, 49), scale=0.75 (for 133% zoom)")
            use_defaults = input("Use calibrated defaults? (y/n): ").strip().lower()
            
            if use_defaults == 'y':
                viewport_offset = (118, 49)
                scale_factor = (0.75, 0.75)
            else:
                try:
                    x_offset = int(input("Enter X offset [118]: ") or "118")
                    y_offset = int(input("Enter Y offset [49]: ") or "49")
                    viewport_offset = (x_offset, y_offset)
                    
                    x_scale = float(input("Enter X scale [0.75]: ") or "0.75")
                    y_scale = float(input("Enter Y scale [0.75]: ") or "0.75")
                    scale_factor = (x_scale, y_scale)
                except ValueError:
                    print("⚠️ Invalid values, using calibrated defaults")
                    viewport_offset = (118, 49)
                    scale_factor = (0.75, 0.75)
            
            print(f"Using: offset={viewport_offset}, scale={scale_factor}")
            
            # Ask if user wants visualization
            show_viz = input("\nCreate visualization overlay? (y/n): ").strip().lower()
            
            # Ask about hash scanning first (to avoid duplicate computation)
            use_hash_scan = input("Use intelligent hash-based scanning? (y/n): ").strip().lower()
            
            if show_viz == 'y':
                # Skip hash computation in visualization if we're doing intelligent scanning
                # (to avoid computing hashes twice)
                visualize_html_detection(
                    api_url="http://localhost:5000",
                    viewport_offset=viewport_offset,
                    scale_factor=scale_factor,
                    tile_height=680,
                    screenshot_path="temp_screenshot.png",
                    output_path="html_detection_overlay.png",
                    show_image=True,
                    compute_hashes=(use_hash_scan != 'y')  # Skip if using intelligent scan
                )
                # The visualization function already stores tiles, but we need to get them
                from detect_tiles_from_html import detect_tiles_from_html
                rectangles, tiles = detect_tiles_from_html(
                    api_url="http://localhost:5000",
                    viewport_offset=viewport_offset,
                    scale_factor=scale_factor,
                    tile_height=680
                )
                self.detected_tiles = rectangles
                self.tile_metadata = tiles  # Store full tile data for thumbnails
                
                # Do hash-based scanning if requested
                if use_hash_scan == 'y' and tiles:
                    self.scan_tiles_with_hash_detection(
                        tiles, viewport_offset, scale_factor, "http://localhost:5000"
                    )
            else:
                # Run HTML-based detection without visualization
                print("\n🌐 Fetching page source and parsing tiles...")
                rectangles, tiles = detect_tiles_from_html(
                    api_url="http://localhost:5000",
                    viewport_offset=viewport_offset,
                    scale_factor=scale_factor,
                    tile_height=680
                )
                
                if rectangles:
                    self.detected_tiles = rectangles
                    self.tile_metadata = tiles  # Store full tile data including thumbnail URLs
                    print(f"\n✅ Successfully detected {len(rectangles)} tiles")
                    
                    # Show summary by column
                    print("\n📊 Tile Layout:")
                    columns = {}
                    for rect, tile in zip(rectangles, tiles):
                        left = tile['left']
                        if left not in columns:
                            columns[left] = []
                        columns[left].append((rect, tile))
                    
                    for col_num, left_val in enumerate(sorted(columns.keys()), 1):
                        items = columns[left_val]
                        video_count = sum(1 for _, t in items if t['has_video'])
                        print(f"  Column {col_num} (x={left_val}px): {len(items)} tiles ({video_count} with video)")
                    
                    # Show first few tiles
                    print("\n🔍 Sample tiles (first 5):")
                    for i, (rect, tile) in enumerate(zip(rectangles[:5], tiles[:5]), 1):
                        x, y, w, h = rect
                        video_marker = "[VIDEO]" if tile['has_video'] else "[IMAGE]"
                        print(f"  {i}. Screen: ({x}, {y}) {w}x{h}  HTML: ({tile['left']}, {tile['top']})  {video_marker}")
                    
                    if len(rectangles) > 5:
                        print(f"  ... and {len(rectangles) - 5} more")
                        
                    print("\n💡 Tiles stored in memory for clicking")
                    
                    # Ask if user wants hash-based scanning
                    use_hash_scan = input("\nUse intelligent hash-based scanning? (y/n): ").strip().lower()
                    if use_hash_scan == 'y':
                        self.scan_tiles_with_hash_detection(
                            tiles, viewport_offset, scale_factor, "http://localhost:5000"
                        )
                else:
                    print("\n❌ No tiles detected")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def get_tile_thumbnail(self):
        """Fetch and display thumbnail for a specific tile."""
        print("\n" + "="*80)
        print("GET TILE THUMBNAIL")
        print("="*80)
        
        # Check if we have HTML tile data stored
        if not hasattr(self, 'tile_metadata') or not self.tile_metadata:
            print("\n⚠️  No HTML tile data available.")
            print("   Please run 'Detect Tiles (HTML-based)' first (Option 4)")
            return
        
        try:
            print(f"\nAvailable tiles: 1-{len(self.tile_metadata)}")
            tile_num = input("Enter tile number to get thumbnail: ").strip()
            
            try:
                idx = int(tile_num)
                if idx < 1 or idx > len(self.tile_metadata):
                    print(f"⚠️  Invalid tile number. Must be between 1 and {len(self.tile_metadata)}")
                    return
            except ValueError:
                print("⚠️  Please enter a valid number")
                return
            
            tile = self.tile_metadata[idx - 1]
            thumbnail_url = tile.get('thumbnail_url')
            
            if not thumbnail_url:
                print(f"❌ No thumbnail URL found for tile {idx}")
                print(f"   Tile data: {tile}")
                return
            
            print(f"\n📷 Fetching thumbnail from: {thumbnail_url}")
            
            # Call the API endpoint to fetch the image
            import requests
            api_url = "http://localhost:5000"
            
            try:
                response = requests.post(
                    f"{api_url}/fetch-image",
                    json={"url": thumbnail_url},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'ok':
                        # Decode base64 image data
                        import base64
                        image_data = base64.b64decode(data['data'])
                        
                        # Save to file
                        output_path = f"grok_test_screenshots/thumbnail_tile_{idx}.png"
                        Path("grok_test_screenshots").mkdir(exist_ok=True)
                        
                        with open(output_path, 'wb') as f:
                            f.write(image_data)
                        
                        print(f"✅ Thumbnail saved to: {output_path}")
                        
                        # Display the image
                        img = cv2.imread(output_path)
                        if img is not None:
                            # Resize if too large
                            h, w = img.shape[:2]
                            max_size = 800
                            if h > max_size or w > max_size:
                                scale = max_size / max(h, w)
                                new_h, new_w = int(h * scale), int(w * scale)
                                img = cv2.resize(img, (new_w, new_h))
                            
                            cv2.imshow(f"Tile {idx} Thumbnail", img)
                            print("👁️  Displaying thumbnail (press any key to close)...")
                            cv2.waitKey(0)
                            cv2.destroyAllWindows()
                        else:
                            print("⚠️  Image saved but couldn't display it")
                    else:
                        print(f"❌ API error: {data.get('error', 'Unknown error')}")
                else:
                    print(f"❌ HTTP error: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
            
            except requests.RequestException as e:
                print(f"❌ Network error: {e}")
                print("   Make sure the API server is running on port 5000")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    def main_menu(self):
        """Display main menu and handle user input."""
        while True:
            print("\n" + "="*80)
            print("GROK TEST APP - MAIN MENU")
            print("="*80)
            print("  1. API Command")
            print("  2. Detect Tiles (Traditional)")
            print("  3. Detect Tiles (Robust - Background Toggle)")
            print("  4. Detect Tiles (HTML-based)")
            print("  5. Click Tile")
            print("  6. Get Tile Thumbnail")
            print("  7. Detect Media Pane (Traditional)")
            print("  8. Detect Media Pane (Robust - Background Toggle)")
            print("  9. Capture Screenshot")
            print(" 10. Clear Tile Hash Database")
            print(" 11. Diagnose Tile Detection")
            print("  0. Exit")
            print("="*80)
            
            choice = input("Select option: ").strip()
            
            if choice == "0":
                print("\n👋 Exiting...")
                break
            
            elif choice == "1":
                self.api_command_menu()
            
            elif choice == "2":
                self.detect_and_display_tiles(use_robust=False)
            
            elif choice == "3":
                self.detect_and_display_tiles(use_robust=True)
            
            elif choice == "4":
                self.detect_tiles_html()
            
            elif choice == "5":
                if not self.detected_tiles:
                    print("⚠️  No tiles detected. Run 'Detect tiles' first.")
                else:
                    print(f"\nAvailable tiles: 1-{len(self.detected_tiles)}")
                    tile_num = input("Enter tile number to click: ").strip()
                    try:
                        self.click_tile(int(tile_num))
                        do_analysis = input("Analyze for video indicator? (y/n): ").strip().lower()
                        if do_analysis == 'y':
                            self.analyze_current_page_for_video_indicator()
                    except ValueError:
                        print("⚠️  Please enter a valid number")
            
            elif choice == "6":
                self.get_tile_thumbnail()
            
            elif choice == "7":
                self.detect_and_display_media_pane(use_robust=False)
            
            elif choice == "8":
                self.detect_and_display_media_pane(use_robust=True)
            
            elif choice == "9":
                filename = input("Enter filename (default: screenshot.png): ").strip()
                if not filename:
                    filename = "screenshot.png"
                self.capture_screenshot(filename)
            
            elif choice == "10":
                print("\n⚠️  WARNING: This will delete all tile hash data!")
                confirm = input("Are you sure? (yes/no): ").strip().lower()
                if confirm == "yes":
                    self.tile_db.clear_database()
                    stats = self.tile_db.get_stats()
                    print(f"\n✅ Database cleared!")
                    print(f"   Total tiles: {stats['total_tiles']}")
                    print(f"   Total scans: {stats['total_scans']}")
                else:
                    print("\n❌ Clear cancelled")
            
            elif choice == "11":
                self.diagnose_tiles()
            
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
