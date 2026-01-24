#!/usr/bin/env python3
"""
Quick test of HTML-based tile detection.
Verifies the end-to-end flow works correctly.
"""

from detect_tiles_from_html import detect_tiles_from_html
import json


def main():
    print("=" * 70)
    print("HTML-BASED TILE DETECTION TEST")
    print("=" * 70)
    
    print("\n1️⃣  Testing with default viewport offset (300, 100)...")
    rectangles, tiles = detect_tiles_from_html(
        api_url="http://localhost:5000",
        viewport_offset=(300, 100),
        tile_height=680
    )
    
    if rectangles:
        print(f"\n✅ SUCCESS: Detected {len(rectangles)} tiles")
        
        print("\n📋 Quick Summary:")
        print(f"   - Total tiles: {len(tiles)}")
        print(f"   - Video tiles: {sum(1 for t in tiles if t['has_video'])}")
        print(f"   - Image tiles: {sum(1 for t in tiles if not t['has_video'])}")
        
        # Group by columns
        columns = {}
        for tile in tiles:
            left = tile['left']
            if left not in columns:
                columns[left] = []
            columns[left].append(tile)
        
        print(f"   - Columns: {len(columns)}")
        for col_x in sorted(columns.keys()):
            print(f"     • Column at x={col_x}px: {len(columns[col_x])} tiles")
        
        print("\n📍 First 3 tile positions (screen coordinates):")
        for i, rect in enumerate(rectangles[:3], 1):
            x, y, w, h = rect
            print(f"   Tile {i}: x={x:4d}, y={y:4d}, w={w:3d}, h={h:3d}")
        
        print("\n" + "=" * 70)
        print("✅ HTML-based detection is working correctly!")
        print("=" * 70)
        print("\n💡 Integration points:")
        print("   • grok_test_app.py: Option 4 - 'Detect Tiles (HTML-based)'")
        print("   • detect_tiles_from_html.py: Main detection module")
        print("   • API endpoint: http://localhost:5000/page-source")
        
    else:
        print("\n❌ FAILED: No tiles detected")
        print("   Check that the API server is running at http://localhost:5000")


if __name__ == '__main__':
    main()
