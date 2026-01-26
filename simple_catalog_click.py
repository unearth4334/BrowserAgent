#!/usr/bin/env python3
"""
Simple script: detect 30 tiles (without fetching images) and click on the 28th tile.
"""

import sys
import time
import requests
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.browser.actions import Navigate, ClickAtCoordinates, WaitForUser
from browser_agent.config import Settings
from detect_tiles_from_html import detect_tiles_from_html
from tile_hash_db import TileHashDatabase


def scroll_via_api(api_url: str, delta_y: int) -> bool:
    """Scroll using the API endpoint."""
    try:
        response = requests.post(
            f"{api_url}/scroll", 
            json={"deltaY": delta_y}, 
            timeout=5
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"   ⚠️ Scroll API error: {e}")
        return False


def fetch_tile_image(api_url: str, thumbnail_url: str) -> Optional[str]:
    """Fetch tile image via API and return base64 data with computed hash."""
    try:
        resp = requests.post(
            f"{api_url}/fetch-image",
            json={"url": thumbnail_url},
            timeout=20
        )
        
        if resp.status_code != 200:
            print(f"            ❌ Status: {resp.status_code}")
            return None, None
        
        data = resp.json()
        
        # API returns 'ok' for success, not 'success'
        if data.get('status') in ['success', 'ok']:
            b64_data = data.get('data')
            if b64_data:
                # Compute hash locally from base64 data
                import base64
                try:
                    image_bytes = base64.b64decode(b64_data)
                    tile_hash = hashlib.sha256(image_bytes).hexdigest()
                except Exception as hash_err:
                    print(f"            ⚠️ Hash computation failed: {hash_err}")
                    tile_hash = None
                return b64_data, tile_hash
            else:
                print(f"            ⚠️ No data field")
                return None, None
        else:
            print(f"            ⚠️ Status: {data.get('status')}")
            if 'error' in data:
                print(f"            Error: {data.get('error')[:100]}")
            return None, None
    except Exception as e:
        print(f"            ❌ Exception: {type(e).__name__}: {str(e)[:100]}")
        return None, None


def generate_html_report(tiles: List[Dict], output_file: str = "tile_catalog_report.html"):
    """Generate HTML report with embedded base64 thumbnails."""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Tile Catalog Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            font-size: 14px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .stats {{
            font-size: 16px;
            opacity: 0.9;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #dee2e6;
            vertical-align: middle;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        tr.clicked-tile {{
            background: #fff3cd;
            font-weight: 600;
        }}
        tr.clicked-tile:hover {{
            background: #ffe69c;
        }}
        .thumbnail {{
            width: 100px;
            height: 100px;
            object-fit: cover;
            border-radius: 4px;
            border: 1px solid #dee2e6;
        }}
        .video-badge {{
            display: inline-block;
            background: #ff4444;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .image-badge {{
            display: inline-block;
            background: #4CAF50;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .position {{
            font-weight: 600;
            color: #007bff;
        }}
        .clicked-badge {{
            display: inline-block;
            background: #ffc107;
            color: #000;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 5px;
        }}
        .coordinates {{
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #6c757d;
        }}
        .hash {{
            font-family: 'Courier New', monospace;
            font-size: 11px;
            color: #495057;
            background: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        .url {{
            font-size: 11px;
            color: #6c757d;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🖼️ Tile Catalog Report</h1>
        <div class="stats">
            <strong>{len(tiles)}</strong> tiles cataloged | 
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    
    <div class="container">
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Thumbnail</th>
                    <th>Hash</th>
                    <th>Coordinates</th>
                    <th>Type</th>
                    <th>URL</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for tile in tiles:
        global_pos = tile.get('global_position', 0)
        thumbnail_url = tile.get('thumbnail_url', '')
        thumbnail_b64 = tile.get('thumbnail_b64', '')
        tile_hash = tile.get('hash', 'N/A')
        screen_x = tile.get('screen_x', 0)
        screen_y = tile.get('screen_y', 0)
        has_video = tile.get('has_video', False)
        
        type_badge = '<span class="video-badge">VIDEO</span>' if has_video else '<span class="image-badge">IMAGE</span>'
        
        # Mark tile #28 as clicked
        row_class = 'class="clicked-tile"' if global_pos == 28 else ''
        clicked_badge = '<span class="clicked-badge">CLICKED</span>' if global_pos == 28 else ''
        
        # Use data URI if we have base64 data, otherwise use original URL with fallback
        if thumbnail_b64:
            img_src = f"data:image/jpeg;base64,{thumbnail_b64}"
        else:
            img_src = thumbnail_url
        
        # Show first 12 chars of hash
        hash_display = tile_hash[:12] if tile_hash and tile_hash != 'N/A' else 'N/A'
        
        html += f"""
                <tr {row_class}>
                    <td class="position">{global_pos}{clicked_badge}</td>
                    <td><img src="{img_src}" class="thumbnail" alt="Tile {global_pos}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22%3E%3Crect fill=%22%23ddd%22 width=%22100%22 height=%22100%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22%3ENo Image%3C/text%3E%3C/svg%3E'"></td>
                    <td><span class="hash">{hash_display}</span></td>
                    <td class="coordinates">({screen_x}, {screen_y})</td>
                    <td>{type_badge}</td>
                    <td class="url">{thumbnail_url[:100]}...</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"\n📄 HTML report saved to: {output_file}")
    return output_file


def main():
    """Collect 30 tile positions and click on the 28th."""
    api_url = "http://localhost:5000"
    target_tiles = 30
    db_path = "tile_hashes.db"
    
    print("=" * 80)
    print("🎯 DETECT 30 TILES AND CLICK ON #28")
    print("=" * 80)
    print(f"Target: {target_tiles} tiles")
    print(f"API: {api_url}")
    print()
    
    # Test API connection
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API server returned status {response.status_code}")
            return 1
        print(f"✅ API server connected")
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        return 1
    
    # Ask about wiping database
    from pathlib import Path
    if Path(db_path).exists():
        response = input(f"\n🗑️  Wipe existing database ({db_path})? (y/n): ").strip().lower()
        if response == 'y':
            Path(db_path).unlink()
            print("✅ Database wiped")
        else:
            print("📂 Using existing database")
    
    # Initialize database
    db = TileHashDatabase(db_path)
    print("💾 Database initialized")
    
    # Get settings
    env_settings = Settings.from_env()
    
    # Create browser controller
    controller = PlaywrightBrowserController(
        executable_path=env_settings.browser_executable_path,
        headless=False,
        viewport_width=2496,
        viewport_height=1404,
    )
    
    try:
        # Start browser
        print("📂 Starting browser...")
        controller.start()
        
        # Navigate to noVNC
        novnc_url = "http://localhost:6080/vnc.html"
        print(f"🌐 Navigating to {novnc_url}...")
        controller.perform(Navigate(novnc_url))
        time.sleep(3)
        
        # Wait for user to position the tileview
        print("\n⏸️  Browser opened to noVNC...")
        controller.perform(WaitForUser("Press Enter once the Grok tileview is visible and at the top..."))
        
        # Collect tiles
        all_tiles: List[Dict] = []
        seen_urls: set = set()  # Track by thumbnail URL instead of coordinates
        scroll_count = 0
        max_scrolls = 10
        
        print("\n" + "=" * 80)
        print("🔍 DETECTING TILES AND FETCHING THUMBNAILS")
        print("=" * 80)
        
        while len(all_tiles) < target_tiles and scroll_count < max_scrolls:
            scroll_count += 1
            
            print(f"\n📍 Scroll iteration #{scroll_count} - Collected: {len(all_tiles)}/{target_tiles}")
            
            # Detect tiles from current view
            try:
                rectangles, tiles = detect_tiles_from_html(
                    api_url=api_url,
                    scale_factor=(0.75, 0.75),
                    tile_height=680
                )
                
                print(f"   Detected {len(tiles)} tiles in current view")
                
                # Process each tile: check for duplicates by URL and fetch thumbnail
                new_tiles_in_view = []
                for idx, (rect, tile) in enumerate(zip(rectangles, tiles)):
                    if len(all_tiles) >= target_tiles:
                        break
                    
                    # Rectangle is (x, y, w, h)
                    x, y, w, h = rect
                    
                    # Use thumbnail URL as unique identifier
                    thumbnail_url = tile.get('thumbnail_url', '')
                    if not thumbnail_url:
                        continue
                    
                    # Check if we've already seen this tile by URL
                    if thumbnail_url in seen_urls:
                        continue
                    
                    # Mark as seen
                    seen_urls.add(thumbnail_url)
                    
                    # Store coordinates (position assigned later)
                    tile['screen_x'] = x
                    tile['screen_y'] = y
                    tile['screen_w'] = w
                    tile['screen_h'] = h
                    new_tiles_in_view.append(tile)
                
                # Fetch thumbnails for new tiles immediately
                print(f"   Fetching thumbnails for {len(new_tiles_in_view)} new tiles...")
                for tile in new_tiles_in_view:
                    # Assign global position as we process each tile
                    tile['global_position'] = len(all_tiles) + 1
                    tile_num = tile['global_position']
                    
                    thumbnail_url = tile.get('thumbnail_url', '')
                    has_video = tile.get('has_video', False)
                    type_str = "VIDEO" if has_video else "IMAGE"
                    x = tile.get('screen_x')
                    y = tile.get('screen_y')
                    
                    print(f"      🔍 Tile #{tile_num} ({type_str}) at ({x}, {y})")
                    
                    # Fetch thumbnail
                    thumbnail_b64, tile_hash = fetch_tile_image(api_url, thumbnail_url)
                    if thumbnail_b64:
                        tile['thumbnail_b64'] = thumbnail_b64
                        tile['hash'] = tile_hash if tile_hash else 'N/A'
                        print(f"         ✅ Thumbnail fetched (hash: {tile.get('hash', 'N/A')[:12]})")
                    else:
                        tile['hash'] = 'N/A'
                        print(f"         ⚠️ Failed to fetch thumbnail")
                    
                    all_tiles.append(tile)
                    
                    if len(all_tiles) >= target_tiles:
                        break
                
                print(f"   Total collected: {len(all_tiles)}/{target_tiles}")
                
                if len(all_tiles) >= target_tiles:
                    print(f"\n✅ Reached target of {target_tiles} tiles!")
                    break
                
                # Scroll down for more tiles
                if scroll_count < max_scrolls:
                    print(f"   📜 Scrolling down...")
                    scroll_via_api(api_url, 800)
                    time.sleep(1.5)
                    
            except Exception as e:
                print(f"   ❌ Error detecting tiles: {e}")
                import traceback
                traceback.print_exc()
                break
        
        # Generate HTML report
        print("\n" + "=" * 80)
        print("📄 GENERATING HTML REPORT")
        print("=" * 80)
        
        report_file = generate_html_report(all_tiles)
        
        # Now find and click on the 28th tile
        print("\n" + "=" * 80)
        print("🎯 CLICKING ON TILE #28")
        print("=" * 80)
        
        if len(all_tiles) < 28:
            print(f"❌ Only collected {len(all_tiles)} tiles, cannot click on #28")
            return 1
        
        target_tile = all_tiles[27]  # 0-indexed, so 28th is index 27
        print(f"\nTarget tile #28:")
        print(f"  Has video: {target_tile.get('has_video')}")
        print(f"  Thumbnail: {target_tile.get('thumbnail_url', '')[:80]}...")
        
        # Get the tile's screen coordinates
        x = target_tile.get('screen_x')
        y = target_tile.get('screen_y')
        w = target_tile.get('screen_w')
        h = target_tile.get('screen_h')
        
        if x is None or y is None or w is None or h is None:
            print("❌ No screen coordinates for tile #28")
            return 1
        
        # Calculate click position (center of tile)
        click_x = x + w // 2
        click_y = y + h // 2
        
        print(f"\n🖱️  Clicking at position ({click_x}, {click_y})...")
        controller.perform(ClickAtCoordinates(x=click_x, y=click_y))
        
        print("✅ Click executed!")
        print("\n⏸️  Pausing for 5 seconds to observe result...")
        time.sleep(5)
        
        print("\n" + "=" * 80)
        print("✅ TASK COMPLETED")
        print("=" * 80)
        print(f"Total tiles detected: {len(all_tiles)}")
        print(f"HTML report: {report_file}")
        print(f"Clicked on tile #28 at ({click_x}, {click_y})")
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        print("\n🔒 Closing browser...")
        controller.stop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
