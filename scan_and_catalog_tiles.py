#!/usr/bin/env python3
"""
Intelligent tile scanning with scrolling to catalog the first 100 tiles.
Uses stable API-based image fetching and generates HTML catalog output.
"""

import sys
import time
import requests
import base64
from pathlib import Path
from typing import Set, List, Dict, Optional, Tuple
from datetime import datetime

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.browser.actions import Navigate, Screenshot, WaitForUser
from browser_agent.config import Settings
from detect_tiles_from_html import detect_tiles_from_html
from tile_hash_db import TileHashDatabase


def scroll_via_api(api_url: str, delta_y: int, target: str = "auto") -> bool:
    """Scroll using the API endpoint."""
    try:
        payload = {"deltaY": delta_y}
        if target != "auto":
            payload["target"] = target
        
        response = requests.post(f"{api_url}/scroll", json=payload, timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"   ⚠️ Scroll API error: {e}")
        return False


def fetch_tile_hash_via_api(api_url: str, thumbnail_url: str, db: TileHashDatabase) -> Optional[Tuple[str, str]]:
    """Fetch tile image via API and compute hash. Returns (hash, base64_data).
    
    The improved /fetch-image endpoint now returns actual images with original format,
    not screenshots. Response includes metadata: format, content_type, size_bytes.
    """
    try:
        resp = requests.post(
            f"{api_url}/fetch-image",
            json={"url": thumbnail_url},
            timeout=20
        )
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'ok' and 'data' in data:
                b64_data = data['data']
                img_bytes = base64.b64decode(b64_data)
                tile_hash = db.compute_tile_hash(img_bytes)
                
                # Optional: Log image metadata from improved endpoint
                # format = data.get('format', 'unknown')
                # content_type = data.get('content_type', 'unknown')
                # size_bytes = data.get('size_bytes', len(img_bytes))
                
                return (tile_hash, b64_data)
    except Exception as e:
        print(f"   ⚠️ Failed to fetch {thumbnail_url[:60]}...: {e}")
    
    return None


def generate_html_catalog(tiles: List[Dict], output_file: str = "tile_catalog.html"):
    """Generate HTML catalog with thumbnail images and details."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grok Tile Catalog - {len(tiles)} Tiles</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .stats {{
            color: #666;
            font-size: 14px;
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
        .thumbnail {{
            width: 100px;
            height: 100px;
            object-fit: cover;
            border-radius: 4px;
            border: 1px solid #dee2e6;
        }}
        .hash {{
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #495057;
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
        .timestamp {{
            color: #6c757d;
            font-size: 12px;
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
        <h1>🖼️ Grok Tile Catalog</h1>
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
                    <th>Position</th>
                    <th>Type</th>
                    <th>First Seen</th>
                    <th>URL</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for idx, tile in enumerate(tiles, 1):
        thumbnail_url = tile.get('thumbnail_url', '')
        thumbnail_b64 = tile.get('thumbnail_b64', '')  # Base64 image data
        tile_hash = tile.get('hash', 'N/A')
        position = tile.get('position', idx)
        has_video = tile.get('has_video', False)
        first_seen = tile.get('first_seen_timestamp', time.time())
        first_seen_str = datetime.fromtimestamp(first_seen).strftime('%Y-%m-%d %H:%M')
        
        type_badge = '<span class="video-badge">VIDEO</span>' if has_video else '<span class="image-badge">IMAGE</span>'
        
        # Use data URI if we have base64 data, otherwise use original URL with fallback
        if thumbnail_b64:
            img_src = f"data:image/jpeg;base64,{thumbnail_b64}"
        else:
            img_src = thumbnail_url
        
        html += f"""
                <tr>
                    <td class="position">{idx}</td>
                    <td><img src="{img_src}" class="thumbnail" alt="Tile {idx}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22%3E%3Crect fill=%22%23ddd%22 width=%22100%22 height=%22100%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22%3ENo Image%3C/text%3E%3C/svg%3E'"></td>
                    <td class="hash">{tile_hash}</td>
                    <td class="position">{position}</td>
                    <td>{type_badge}</td>
                    <td class="timestamp">{first_seen_str}</td>
                    <td class="url">{thumbnail_url[:80]}...</td>
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
    
    print(f"\n📄 HTML catalog saved to: {output_file}")


def main():
    """Main function to scan and catalog first 100 tiles."""
    screenshot_dir = Path("./grok_test_screenshots")
    screenshot_dir.mkdir(exist_ok=True)
    
    api_url = "http://localhost:5000"
    target_tiles = 100
    
    print("=" * 80)
    print("🚀 INTELLIGENT TILE SCANNING WITH SCROLLING")
    print("=" * 80)
    print(f"Target: First {target_tiles} tiles")
    print(f"API: {api_url}")
    print()
    
    # Test API connection
    try:
        response = requests.get(f"{api_url}/page-source", timeout=5)
        if response.status_code != 200:
            print(f"❌ API server returned status {response.status_code}")
            return 1
        print(f"✅ API server connected")
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        return 1
    
    # Initialize database
    db = TileHashDatabase("tile_hashes.db")
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
        
        # Wait for user to set up
        print("\n⏸️  Browser opened to noVNC...")
        controller.perform(WaitForUser("Press Enter once the Grok tileview is visible and at the top..."))
        
        # Track collected tiles
        collected_tiles: List[Dict] = []
        seen_hashes: Set[str] = set()
        fetched_thumbnails: Dict[str, Tuple[str, str]] = {}  # URL -> (hash, base64_data)
        scroll_count = 0
        max_scrolls = 50
        
        print("\n" + "=" * 80)
        print("🔍 STARTING TILE COLLECTION")
        print("=" * 80)
        
        while len(collected_tiles) < target_tiles and scroll_count < max_scrolls:
            scroll_count += 1
            
            print(f"\n📍 Scroll iteration #{scroll_count}")
            print(f"   Collected: {len(collected_tiles)}/{target_tiles}")
            
            # Detect tiles from current view
            try:
                rectangles, tiles = detect_tiles_from_html(
                    api_url=api_url,
                    scale_factor=(0.75, 0.75),
                    tile_height=680
                )
            except Exception as e:
                print(f"   ⚠️ Error detecting tiles: {e}")
                scroll_via_api(api_url, delta_y=1000, target="auto")
                time.sleep(2.0)
                continue
            
            if not tiles:
                print("   ⚠️ No tiles detected, scrolling...")
                scroll_via_api(api_url, delta_y=1000, target="auto")
                time.sleep(2.0)
                continue
            
            print(f"   🔍 Found {len(tiles)} tiles in current view")
            
            # Process each tile with intelligent hashing
            new_tiles_this_scroll = 0
            for tile in tiles:
                thumbnail_url = tile.get('thumbnail_url')
                if not thumbnail_url:
                    continue
                
                # Check if we've already fetched this thumbnail URL
                if thumbnail_url in fetched_thumbnails:
                    tile_hash, thumbnail_b64 = fetched_thumbnails[thumbnail_url]
                    print(f"   💾 Cached tile at position {tile['index']}: {tile_hash}")
                else:
                    # Fetch and compute hash via API (stable method)
                    print(f"   🔑 Fetching tile at position {tile['index']}...", end=' ')
                    result = fetch_tile_hash_via_api(api_url, thumbnail_url, db)
                    
                    if not result:
                        print("❌ Failed")
                        continue
                    
                    tile_hash, thumbnail_b64 = result
                    fetched_thumbnails[thumbnail_url] = (tile_hash, thumbnail_b64)
                    tile_hash, thumbnail_b64 = result
                print(f"✅ {tile_hash}")
                
                # Skip if already collected
                if tile_hash in seen_hashes:
                    continue
                
                seen_hashes.add(tile_hash)
                
                # Add to database
                position = tile['index']
                has_video = tile.get('has_video', False)
                
                tile_id = db.add_or_update_tile(
                    tile_hash=tile_hash,
                    position=position,
                    thumbnail_url=thumbnail_url,
                    has_video=has_video,
                    processed=False
                )
                
                # Get full tile info from DB and add base64 data
                tile_info = db.get_tile_by_hash(tile_hash)
                if tile_info:
                    tile_info['thumbnail_b64'] = thumbnail_b64  # Add base64 data for HTML
                    collected_tiles.append(tile_info)
                    new_tiles_this_scroll += 1
                
                # Check if we've reached target
                if len(collected_tiles) >= target_tiles:
                    break
                
                # 2 second delay between fetches for stability
                if len(collected_tiles) < target_tiles:
                    time.sleep(2)
            
            print(f"   📊 New tiles this scroll: {new_tiles_this_scroll}")
            
            # Stop if we've reached target
            if len(collected_tiles) >= target_tiles:
                print(f"\n🎉 Target reached! Collected {len(collected_tiles)} tiles.")
                break
            
            # Scroll for more tiles
            print("   📜 Scrolling down to load more tiles...")
            scroll_via_api(api_url, delta_y=1000, target="auto")
            time.sleep(2.0)
        
        # Record scan in database
        db.record_scan(
            tiles_found=len(collected_tiles),
            new_tiles=len(collected_tiles),
            stopped_at_position=collected_tiles[-1]['position'] if collected_tiles else 0
        )
        
        # Generate HTML catalog
        print("\n" + "=" * 80)
        print("📊 GENERATING HTML CATALOG")
        print("=" * 80)
        generate_html_catalog(collected_tiles, output_file="tile_catalog.html")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 COLLECTION SUMMARY")
        print("=" * 80)
        print(f"Total tiles collected: {len(collected_tiles)}")
        print(f"Total scrolls performed: {scroll_count}")
        print(f"Unique tiles: {len(seen_hashes)}")
        
        # Database stats
        stats = db.get_stats()
        print(f"\n📊 Database stats:")
        print(f"   Total tiles in DB: {stats['total_tiles']}")
        print(f"   Processed: {stats['processed_tiles']}")
        print(f"   Unprocessed: {stats['unprocessed_tiles']}")
        
        # Show first and last few
        if collected_tiles:
            print(f"\nFirst 5 tiles:")
            for i, tile in enumerate(collected_tiles[:5], 1):
                video_icon = "🎥" if tile['has_video'] else "🖼️"
                print(f"  {i}. {video_icon} Hash: {tile['hash']}, Position: {tile['position']}")
            
            if len(collected_tiles) > 5:
                print(f"\nLast 5 tiles:")
                for i, tile in enumerate(collected_tiles[-5:], len(collected_tiles) - 4):
                    video_icon = "🎥" if tile['has_video'] else "🖼️"
                    print(f"  {i}. {video_icon} Hash: {tile['hash']}, Position: {tile['position']}")
        
        print("\n✅ Done! Open tile_catalog.html in your browser to view the catalog.")
        
        # Keep browser open
        print("\n⏸️  Browser will stay open for verification...")
        controller.perform(WaitForUser("Press Enter to close browser and exit..."))
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        if collected_tiles:
            print(f"💾 Collected {len(collected_tiles)} tiles before interruption")
            generate_html_catalog(collected_tiles, output_file="tile_catalog_partial.html")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        controller.stop()
        db.close()


if __name__ == "__main__":
    sys.exit(main())
