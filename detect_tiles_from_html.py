#!/usr/bin/env python3
"""
HTML-based tile detection for Grok image gallery.
Uses the page source API to get exact tile positions instead of visual detection.
"""

import requests
import json
from bs4 import BeautifulSoup
from typing import List, Tuple, Dict, Optional


def fetch_page_source(api_url: str = "http://localhost:5000") -> str:
    """Fetch HTML from the page source API endpoint."""
    try:
        response = requests.get(f"{api_url}/page-source", timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('html', '')
    except Exception as e:
        print(f"❌ Error fetching page source: {e}")
        return ''


def parse_tile_positions(html_content: str) -> List[Dict]:
    """Parse tile positions from HTML listitems."""
    soup = BeautifulSoup(html_content, 'html.parser')
    listitems = soup.find_all(attrs={'role': 'listitem'})
    
    tiles = []
    for idx, item in enumerate(listitems, 1):
        style_attr = item.get('style', '')
        style_dict = {}
        
        # Parse style string
        for prop in style_attr.split(';'):
            if ':' in prop:
                key, value = prop.split(':', 1)
                style_dict[key.strip()] = value.strip()
        
        # Extract position values
        try:
            left = int(style_dict.get('left', '0').replace('px', ''))
            top = int(style_dict.get('top', '0').replace('px', ''))
            width = int(style_dict.get('width', '450').replace('px', ''))
            
            # Find images and videos
            images = item.find_all('img')
            videos = item.find_all('video')
            
            # Extract image URLs (src or data-src attributes)
            image_urls = []
            for img in images:
                url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if url:
                    image_urls.append(url)
            
            tile_data = {
                'index': idx,
                'left': left,
                'top': top,
                'width': width,
                'has_video': len(videos) > 0,
                'num_images': len(images),
                'num_videos': len(videos),
                'image_urls': image_urls,  # List of image URLs
                'thumbnail_url': image_urls[0] if image_urls else None,  # First image as thumbnail
            }
            tiles.append(tile_data)
        except (ValueError, AttributeError) as e:
            print(f"⚠️ Failed to parse tile {idx}: {e}")
            continue
    
    return tiles


def get_viewport_offset(api_url: str = "http://localhost:5000") -> Tuple[int, int]:
    """
    Get the viewport offset from the API.
    This tells us where the page content starts relative to the browser window.
    """
    try:
        response = requests.get(f"{api_url}/viewport-info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Assuming the API returns scroll offsets or content area position
            x_offset = data.get('content_x', 0)
            y_offset = data.get('content_y', 0)
            return x_offset, y_offset
        # API endpoint doesn't exist or returned error
        raise Exception("Viewport info not available")
    except:
        # Default offsets based on typical Grok layout (calibrated via visual detection)
        # Content area typically starts after sidebar and top bar
        return 118, 49  # Calibrated values from align_html_detection.py with scale 0.75


def convert_to_screen_coordinates(
    tiles: List[Dict],
    viewport_offset: Tuple[int, int],
    scale_factor: Tuple[float, float] = (1.0, 1.0),
    tile_height: int = 680  # Approximate tile height
) -> List[Tuple[int, int, int, int]]:
    """
    Convert HTML positions to screen coordinates (x, y, w, h).
    
    Args:
        tiles: List of tile dictionaries with 'left', 'top', 'width'
        viewport_offset: (x_offset, y_offset) from browser window origin
        scale_factor: (x_scale, y_scale) scaling factor for coordinates
        tile_height: Estimated height of tiles
        
    Returns:
        List of rectangles as (x, y, width, height) tuples
    """
    x_offset, y_offset = viewport_offset
    x_scale, y_scale = scale_factor
    rectangles = []
    
    for tile in tiles:
        # Convert HTML coordinates to screen coordinates with scaling
        x = x_offset + int(tile['left'] * x_scale)
        y = y_offset + int(tile['top'] * y_scale)
        w = int(tile['width'] * x_scale)
        h = int(tile_height * y_scale)  # Use scaled height
        
        rectangles.append((x, y, w, h))
    
    return rectangles


def detect_tiles_from_html(
    api_url: str = "http://localhost:5000",
    viewport_offset: Optional[Tuple[int, int]] = None,
    scale_factor: Tuple[float, float] = (0.75, 0.75),  # Calibrated default for 133% zoom
    tile_height: int = 680
) -> Tuple[List[Tuple[int, int, int, int]], List[Dict]]:
    """
    Main function to detect tiles using HTML parsing.
    
    Args:
        api_url: Base URL of the API server
        viewport_offset: Optional (x, y) offset, will be auto-detected if None
        scale_factor: (x_scale, y_scale) for coordinate scaling (default 0.75 for 133% zoom)
        tile_height: Height to use for tile rectangles
        
    Returns:
        Tuple of (rectangles, tile_data):
            - rectangles: List of (x, y, w, h) tuples for each tile
            - tile_data: List of dictionaries with tile metadata
    """
    print("🌐 Fetching page source...")
    html_content = fetch_page_source(api_url)
    
    if not html_content:
        print("❌ Failed to fetch page source")
        return [], []
    
    print("📄 Parsing HTML for tile positions...")
    tiles = parse_tile_positions(html_content)
    
    # Sort tiles by reading order: top-to-bottom (rows), then left-to-right (columns)
    # Group by row first (using 'top' coordinate with some tolerance for alignment)
    tiles.sort(key=lambda t: (t['top'] // 50, t['left']))  # 50px tolerance for row grouping
    
    # Re-index after sorting
    for idx, tile in enumerate(tiles, 1):
        tile['index'] = idx
    
    print(f"✅ Found {len(tiles)} tiles")
    
    if viewport_offset is None:
        print("📏 Detecting viewport offset...")
        viewport_offset = get_viewport_offset(api_url)
    
    print(f"📍 Using viewport offset: {viewport_offset}")
    print(f"📍 Using scale factor: ({scale_factor[0]:.3f}, {scale_factor[1]:.3f})")
    
    print("🔄 Converting to screen coordinates...")
    rectangles = convert_to_screen_coordinates(tiles, viewport_offset, scale_factor, tile_height)
    
    # Print summary
    print("\n📊 Tile Detection Summary:")
    print(f"  Total tiles: {len(tiles)}")
    print(f"  Viewport offset: {viewport_offset}")
    
    # Group by column
    columns = {}
    for tile in tiles:
        left = tile['left']
        if left not in columns:
            columns[left] = []
        columns[left].append(tile)
    
    print(f"  Columns detected: {len(columns)}")
    for col_x in sorted(columns.keys()):
        print(f"    Column at x={col_x}px: {len(columns[col_x])} tiles")
    
    return rectangles, tiles


def save_detection_results(
    rectangles: List[Tuple[int, int, int, int]],
    tiles: List[Dict],
    output_file: str = "html_detection_results.json"
):
    """Save detection results to JSON file."""
    data = {
        'num_tiles': len(rectangles),
        'rectangles': [
            {'x': r[0], 'y': r[1], 'width': r[2], 'height': r[3]}
            for r in rectangles
        ],
        'tiles': tiles
    }
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")


def main():
    """Test the HTML-based detection."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Detect tiles from HTML page source')
    parser.add_argument('--api-url', default='http://localhost:5000',
                       help='API server URL')
    parser.add_argument('--x-offset', type=int, default=None,
                       help='X offset for viewport (auto-detect if not provided)')
    parser.add_argument('--y-offset', type=int, default=None,
                       help='Y offset for viewport (auto-detect if not provided)')
    parser.add_argument('--tile-height', type=int, default=680,
                       help='Estimated tile height in pixels')
    parser.add_argument('--output', default='html_detection_results.json',
                       help='Output JSON file')
    
    args = parser.parse_args()
    
    viewport_offset = None
    if args.x_offset is not None and args.y_offset is not None:
        viewport_offset = (args.x_offset, args.y_offset)
    
    rectangles, tiles = detect_tiles_from_html(
        api_url=args.api_url,
        viewport_offset=viewport_offset,
        tile_height=args.tile_height
    )
    
    if rectangles:
        save_detection_results(rectangles, tiles, args.output)
        print("\n✅ HTML-based tile detection complete!")
    else:
        print("\n❌ No tiles detected")


if __name__ == '__main__':
    main()
