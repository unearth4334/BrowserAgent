#!/usr/bin/env python3
"""
Interactive Tile Test App
Allows cataloging a specified number of tiles, clearing the database, and clicking a specific tile.
"""

import argparse
import sys
import time
import base64
import hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
import requests
from detect_tiles_from_html import detect_tiles_from_html
from tile_hash_db import TileHashDatabase

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.browser.actions import Navigate, WaitForUser
from browser_agent.config import Settings


API_URL = "http://localhost:5000"
VNC_URL = "http://localhost:6080/vnc.html"
VIEWPORT_WIDTH = 2496
VIEWPORT_HEIGHT = 1404

# Global browser controller
_browser_controller = None


def fetch_tile_image(thumbnail_url):
    """Fetch tile image via API and return base64 data with computed hash."""
    try:
        resp = requests.post(
            f"{API_URL}/fetch-image",
            json={"url": thumbnail_url},
            timeout=20
        )
        
        if resp.status_code != 200:
            print(f"            ❌ Status: {resp.status_code}")
            return None, None
        
        data = resp.json()
        
        # API returns 'ok' for success, not just 'success'
        if data.get('status') in ['success', 'ok']:
            b64_data = data.get('data')
            if b64_data:
                # Compute hash locally from base64 data
                try:
                    image_bytes = base64.b64decode(b64_data)
                    tile_hash = hashlib.sha256(image_bytes).hexdigest()
                except Exception as hash_err:
                    print(f"            ⚠️ Hash computation failed: {hash_err}")
                    tile_hash = None
                return b64_data, tile_hash
            else:
                print("            ⚠️ No data field")
                return None, None
        else:
            print(f"            ⚠️ Status: {data.get('status')}")
            if 'error' in data:
                print(f"            Error: {data.get('error')[:100]}")
            return None, None
    except Exception as e:
        print(f"            ❌ Exception: {type(e).__name__}: {str(e)[:100]}")
        return None, None


def generate_html_report(tiles, output_file="tile_catalog_report.html", clicked_tile=None):
    """Generate HTML report with embedded base64 thumbnails."""
    html_parts = []
    html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tile Catalog Report</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding: 20px; }
        .tile-thumbnail { max-width: 150px; max-height: 150px; }
        .clicked-row { background-color: #fff3cd !important; }
        .hash-text { font-family: monospace; font-size: 0.85em; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <h1 class="mb-4">Tile Catalog Report</h1>
        <p class="text-muted">Generated: """ + time.strftime("%Y-%m-%d %H:%M:%S") + """</p>
        <p><strong>Total Tiles Cataloged:</strong> """ + str(len(tiles)) + """</p>
""")
    
    if clicked_tile is not None:
        html_parts.append(f'        <p><strong>Clicked Tile:</strong> #{clicked_tile}</p>\n')
    
    html_parts.append("""        <table class="table table-striped table-hover">
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
""")
    
    for tile in tiles:
        position = tile['global_position']
        row_class = ' class="clicked-row"' if clicked_tile and position == clicked_tile else ''
        
        html_parts.append(f'                <tr{row_class}>\n')
        html_parts.append(f'                    <td><strong>{position}</strong>')
        if clicked_tile and position == clicked_tile:
            html_parts.append(' <span class="badge bg-warning">CLICKED</span>')
        html_parts.append('</td>\n')
        
        # Thumbnail
        if tile.get('thumbnail_b64'):
            html_parts.append(f'                    <td><img src="data:image/webp;base64,{tile["thumbnail_b64"]}" class="tile-thumbnail" alt="Tile {position}"></td>\n')
        else:
            html_parts.append('                    <td><span class="text-muted">No thumbnail</span></td>\n')
        
        # Hash
        hash_display = tile.get('hash', 'N/A')
        if hash_display and hash_display != 'N/A':
            hash_display = hash_display[:12] + '...'
        html_parts.append(f'                    <td><span class="hash-text">{hash_display}</span></td>\n')
        
        # Coordinates
        x = tile.get('screen_x', tile.get('left', ''))
        y = tile.get('screen_y', tile.get('top', ''))
        w = tile.get('screen_w', tile.get('width', ''))
        h = tile.get('screen_h', tile.get('height', ''))
        html_parts.append(f'                    <td>({x}, {y}, {w}, {h})</td>\n')
        
        # Type
        html_parts.append(f'                    <td>{tile.get("type", "N/A")}</td>\n')
        
        # URL
        url = tile.get('thumbnail_url', 'N/A')
        if len(url) > 50:
            url = url[:47] + '...'
        html_parts.append(f'                    <td><small>{url}</small></td>\n')
        
        html_parts.append('                </tr>\n')
    
    html_parts.append("""            </tbody>
        </table>
    </div>
</body>
</html>
""")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(html_parts))
    
    print(f"\n✓ HTML report generated: {output_file}")


def get_page_source():
    """Fetch page source from API."""
    try:
        response = requests.get(f"{API_URL}/page-source", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') in ['success', 'ok']:
                html = data.get('html')
                if html:
                    return html
                else:
                    print(f"  ⚠ API returned empty HTML")
            else:
                print(f"  ⚠ API returned status: {data.get('status')}")
        else:
            print(f"  ⚠ API returned status code: {response.status_code}")
    except requests.exceptions.JSONDecodeError as e:
        print(f"  ⚠ Failed to parse JSON response: {e}")
    except Exception as e:
        print(f"  ⚠ Error fetching page source: {e}")
    return None


def scroll_down(delta_y=800):
    """Scroll down by the specified deltaY (matches simple_catalog_click.py)."""
    try:
        response = requests.post(
            f"{API_URL}/scroll",
            json={"deltaY": delta_y},
            timeout=5
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"   ⚠️ Scroll API error: {e}")
        return False


def click_at_position(x, y):
    """Click at specific coordinates using the API."""
    try:
        response = requests.post(
            f"{API_URL}/click",
            json={"x": x, "y": y},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('status') in ['success', 'ok']
        else:
            print(f"Click failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"Error clicking at ({x}, {y}): {e}")
        return False


def catalog_tiles(num_tiles, clear_db=False):
    """
    Catalog the specified number of tiles.
    Returns list of cataloged tiles.
    """
    db = TileHashDatabase()
    
    if clear_db:
        print(f"\n🗑️  Clearing database...")
        db.clear_database()
        print("✓ Database cleared")
    
    # Note: Skipping page validation since Grok is a React SPA
    # and tiles are rendered after initial HTML load.
    # If tiles aren't found, detect_tiles_from_html() will return empty list.
    
    all_tiles = []
    seen_urls = set()
    scroll_iterations = 0
    max_scroll_iterations = 10  # Match simple_catalog_click.py
    
    print(f"\n📊 Cataloging {num_tiles} tiles...")
    print("=" * 60)
    
    while len(all_tiles) < num_tiles and scroll_iterations < max_scroll_iterations:
        scroll_iterations += 1
        print(f"\n📍 Scroll iteration #{scroll_iterations} - Collected: {len(all_tiles)}/{num_tiles}")
        
        # Detect tiles using the same method as simple_catalog_click.py
        rectangles, tiles = detect_tiles_from_html(
            api_url=API_URL,
            scale_factor=(0.75, 0.75),
            tile_height=680
        )
        
        print(f"   Detected {len(tiles)} tiles in current view")
        
        # Process each tile: check for duplicates by URL and fetch thumbnail
        new_tiles_in_view = []
        for rect, tile in zip(rectangles, tiles):
            if len(all_tiles) >= num_tiles:
                break
            
            x, y, w, h = rect
            thumbnail_url = tile.get('thumbnail_url', '')
            if not thumbnail_url:
                continue
            if thumbnail_url in seen_urls:
                continue
            
            seen_urls.add(thumbnail_url)
            tile['screen_x'] = x
            tile['screen_y'] = y
            tile['screen_w'] = w
            tile['screen_h'] = h
            new_tiles_in_view.append(tile)
        
        print(f"   Fetching thumbnails for {len(new_tiles_in_view)} new tiles...")
        for tile in new_tiles_in_view:
            if len(all_tiles) >= num_tiles:
                break
            
            tile['global_position'] = len(all_tiles) + 1
            tile_num = tile['global_position']
            thumbnail_url = tile.get('thumbnail_url', '')
            has_video = tile.get('has_video', False)
            type_str = "VIDEO" if has_video else "IMAGE"
            x = tile.get('screen_x')
            y = tile.get('screen_y')
            
            print(f"      🔍 Tile #{tile_num} ({type_str}) at ({x}, {y})")
            
            b64_data, img_hash = fetch_tile_image(thumbnail_url)
            if b64_data:
                tile['thumbnail_b64'] = b64_data
                tile['hash'] = img_hash if img_hash else 'N/A'
                if img_hash:
                    db.add_or_update_tile(
                        tile_hash=img_hash,
                        position=tile.get('global_position', 0),
                        thumbnail_url=tile.get('thumbnail_url'),
                        has_video=tile.get('has_video', False),
                        processed=False
                    )
                print(f"         ✅ Thumbnail fetched (hash: {tile.get('hash', 'N/A')[:12]})")
            else:
                tile['hash'] = 'N/A'
                print("         ⚠️ Failed to fetch thumbnail")
            
            all_tiles.append(tile)
        
        print(f"   Total collected: {len(all_tiles)}/{num_tiles}")
        
        if len(all_tiles) >= num_tiles:
            print(f"\n✅ Reached target of {num_tiles} tiles!")
            break
        
        if scroll_iterations < max_scroll_iterations:
            print("   📜 Scrolling down...")
            scroll_down(800)
            time.sleep(1.5)
    
    print("\n" + "=" * 60)
    print(f"✓ Cataloged {len(all_tiles)} tiles")
    
    return all_tiles


def click_tile(tiles, tile_number):
    """Click on the specified tile."""
    if tile_number < 1 or tile_number > len(tiles):
        print(f"\n❌ Invalid tile number: {tile_number} (valid range: 1-{len(tiles)})")
        return False
    
    # Find the tile
    target_tile = None
    for tile in tiles:
        if tile.get('global_position') == tile_number:
            target_tile = tile
            break
    
    if not target_tile:
        print(f"\n❌ Tile #{tile_number} not found")
        return False
    
    # Calculate click coordinates (center of tile)
    click_x = target_tile.get('screen_x', target_tile.get('left', 0)) + (target_tile.get('screen_w', target_tile.get('width', 0)) // 2)
    click_y = target_tile.get('screen_y', target_tile.get('top', 0)) + (target_tile.get('screen_h', target_tile.get('height', 0)) // 2)
    
    print(f"\n🖱️  Clicking tile #{tile_number} at ({click_x}, {click_y})...")
    
    success = click_at_position(click_x, click_y)
    
    if success:
        print(f"✓ Clicked tile #{tile_number}")
        return True
    else:
        print(f"❌ Failed to click tile #{tile_number}")
        return False


def show_menu():
    """Display the main menu."""
    print("\n" + "=" * 60)
    print("  TILE TEST APP - Interactive Menu")
    print("=" * 60)
    print("1. Catalog tiles")
    print("2. Click on a tile")
    print("3. Catalog and click")
    print("4. Clear database")
    print("5. Generate HTML report")
    print("6. View tile count")
    print("7. Exit")
    print("=" * 60)


def get_int_input(prompt, min_val=None, max_val=None):
    """Get integer input from user with validation."""
    while True:
        try:
            value = int(input(prompt))
            if min_val is not None and value < min_val:
                print(f"  ⚠ Value must be at least {min_val}")
                continue
            if max_val is not None and value > max_val:
                print(f"  ⚠ Value must be at most {max_val}")
                continue
            return value
        except ValueError:
            print("  ⚠ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n")
            return None


def start_browser():
    """Start the browser and navigate to noVNC."""
    global _browser_controller
    
    if _browser_controller is not None:
        return _browser_controller
    
    print("\n🌐 Starting browser...")
    
    # Get settings
    env_settings = Settings.from_env()
    
    # Create browser controller
    _browser_controller = PlaywrightBrowserController(
        executable_path=env_settings.browser_executable_path,
        headless=False,
        viewport_width=VIEWPORT_WIDTH,
        viewport_height=VIEWPORT_HEIGHT,
    )
    
    _browser_controller.start()
    print(f"✓ Browser started")
    
    # Navigate to noVNC
    print(f"✓ Navigating to {VNC_URL}...")
    _browser_controller.perform(Navigate(VNC_URL))
    time.sleep(3)
    
    print("✓ Browser ready")
    print("\n📝 Please navigate to https://grok.com/imagine/favorites in the VNC browser")
    print("   and scroll to the top of the tile view.")
    
    input("\nPress Enter when ready to continue...")
    
    return _browser_controller


def stop_browser():
    """Stop the browser if running."""
    global _browser_controller
    
    if _browser_controller is not None:
        print("\n🛑 Closing browser...")
        _browser_controller.stop()
        _browser_controller = None
        print("✓ Browser closed")


def interactive_mode():
    """Run the app in interactive menu mode."""
    tiles = []
    clicked_tile = None
    output_file = "tile_catalog_report.html"
    
    print("\n🎮 Welcome to the Tile Test App!")
    print("This app helps you catalog and interact with tiles.")
    
    # Start browser on first run
    try:
        start_browser()
    except Exception as e:
        print(f"\n❌ Failed to start browser: {e}")
        print("Please make sure Docker container is running and try again.")
        return 1
    
    while True:
        show_menu()
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1':
            # Catalog tiles
            num_tiles = get_int_input("\n📊 How many tiles to catalog? ", min_val=1)
            if num_tiles is None:
                continue
            
            clear = input("Clear database first? (y/n): ").strip().lower() == 'y'
            
            tiles = catalog_tiles(num_tiles, clear_db=clear)
            clicked_tile = None  # Reset clicked tile
            
            if tiles:
                print(f"\n✓ Successfully cataloged {len(tiles)} tiles")
            else:
                print("\n❌ No tiles were cataloged")
        
        elif choice == '2':
            # Click on a tile
            if not tiles:
                print("\n⚠️  No tiles cataloged yet. Please catalog tiles first (option 1).")
                continue
            
            print(f"\n🖱️  You have {len(tiles)} tiles cataloged (1-{len(tiles)})")
            tile_num = get_int_input(f"Which tile to click? (1-{len(tiles)}): ", min_val=1, max_val=len(tiles))
            if tile_num is None:
                continue
            
            if click_tile(tiles, tile_num):
                clicked_tile = tile_num
                print(f"\n✓ Successfully clicked tile #{tile_num}")
                time.sleep(2)
            else:
                print(f"\n❌ Failed to click tile #{tile_num}")
        
        elif choice == '3':
            # Catalog and click
            num_tiles = get_int_input("\n📊 How many tiles to catalog? ", min_val=1)
            if num_tiles is None:
                continue
            
            clear = input("Clear database first? (y/n): ").strip().lower() == 'y'
            
            tiles = catalog_tiles(num_tiles, clear_db=clear)
            
            if not tiles:
                print("\n❌ No tiles were cataloged")
                continue
            
            print(f"\n✓ Cataloged {len(tiles)} tiles")
            
            tile_num = get_int_input(f"\n🖱️  Which tile to click? (1-{len(tiles)}): ", min_val=1, max_val=len(tiles))
            if tile_num is None:
                continue
            
            if click_tile(tiles, tile_num):
                clicked_tile = tile_num
                print(f"\n✓ Successfully clicked tile #{tile_num}")
                time.sleep(2)
            else:
                print(f"\n❌ Failed to click tile #{tile_num}")
        
        elif choice == '4':
            # Clear database
            confirm = input("\n⚠️  Are you sure you want to clear the database? (yes/no): ").strip().lower()
            if confirm == 'yes':
                db = TileHashDatabase()
                db.clear_database()
                print("✓ Database cleared")
            else:
                print("Cancelled")
        
        elif choice == '5':
            # Generate HTML report
            if not tiles:
                print("\n⚠️  No tiles to report. Please catalog tiles first (option 1).")
                continue
            
            custom = input(f"\nCurrent output: {output_file}\nUse custom filename? (y/n): ").strip().lower()
            if custom == 'y':
                output_file = input("Enter filename: ").strip() or output_file
            
            generate_html_report(tiles, output_file, clicked_tile)
        
        elif choice == '6':
            # View tile count
            if tiles:
                print(f"\n📊 Currently cataloged: {len(tiles)} tiles")
                if clicked_tile:
                    print(f"   Last clicked: Tile #{clicked_tile}")
            else:
                print("\n📊 No tiles cataloged yet")
            
            # Database stats
            db = TileHashDatabase()
            try:
                cursor = db.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tiles")
                db_count = cursor.fetchone()[0]
                print(f"   Database contains: {db_count} tiles")
            except:
                pass
        
        elif choice == '7':
            # Exit
            print("\n👋 Goodbye!")
            stop_browser()
            return 0
        
        else:
            print("\n⚠️  Invalid choice. Please enter a number between 1 and 7.")


def main():
    parser = argparse.ArgumentParser(
        description="Interactive Tile Test App - Catalog and click tiles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Command-line mode examples:
  %(prog)s --catalog 30                    # Catalog 30 tiles
  %(prog)s --catalog 30 --click 15         # Catalog 30 tiles and click tile #15
  %(prog)s --catalog 50 --clear-db         # Clear database and catalog 50 tiles
  %(prog)s --catalog 30 --click 28 --output my_report.html

Interactive mode:
  %(prog)s                                 # Run with interactive menu
        """
    )
    
    parser.add_argument(
        '--catalog', '-c',
        type=int,
        metavar='N',
        help='Catalog N tiles (command-line mode)'
    )
    
    parser.add_argument(
        '--click', '-k',
        type=int,
        metavar='N',
        help='Click tile number N (command-line mode)'
    )
    
    parser.add_argument(
        '--clear-db',
        action='store_true',
        help='Clear the tile hash database before cataloging'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='tile_catalog_report.html',
        help='Output HTML report filename (default: tile_catalog_report.html)'
    )
    
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Skip generating HTML report'
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, run in interactive mode
    if not args.catalog and not args.click and not args.clear_db:
        try:
            return interactive_mode()
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            stop_browser()
            return 130
        except Exception as e:
            print(f"\n❌ Error: {e}")
            stop_browser()
            return 1
        finally:
            stop_browser()
    
    # Command-line mode
    # Validate arguments
    if not args.catalog and not args.click:
        parser.error("Must specify --catalog and/or --click")
    
    if args.click and not args.catalog:
        parser.error("--click requires --catalog (or run catalog first)")
    
    tiles = []
    
    try:
        # Start browser for command-line mode
        try:
            start_browser()
        except Exception as e:
            print(f"\n❌ Failed to start browser: {e}")
            return 1
        
        # Catalog tiles if requested
        if args.catalog:
            tiles = catalog_tiles(args.catalog, clear_db=args.clear_db)
            
            if not tiles:
                print("\n❌ No tiles cataloged")
                stop_browser()
                return 1
        
        # Click tile if requested
        clicked_tile = None
        if args.click:
            if click_tile(tiles, args.click):
                clicked_tile = args.click
                time.sleep(2)  # Wait for tile to open
        
        # Generate HTML report
        if tiles and not args.no_report:
            generate_html_report(tiles, args.output, clicked_tile)
        
        print("\n✅ Test completed successfully!")
        stop_browser()
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        stop_browser()
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        stop_browser()
        return 1


if __name__ == "__main__":
    sys.exit(main())
