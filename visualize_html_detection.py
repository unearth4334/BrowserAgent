#!/usr/bin/env python3
"""
Visualize HTML-based tile detection by overlaying rectangles on a screenshot.
Shows tile positions, numbers, and video indicators.
"""

import cv2
import numpy as np
import requests
from pathlib import Path
from detect_tiles_from_html import detect_tiles_from_html


def capture_screenshot(api_url: str = "http://localhost:5000", output_path: str = "temp_screenshot.png") -> str:
    """Capture a screenshot via the API."""
    try:
        print(f"📸 Capturing screenshot...")
        response = requests.post(
            f"{api_url}/screenshot",
            json={"format": "png"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Decode base64 data and save to file
            import base64
            image_data = base64.b64decode(data['data'])
            
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            print(f"✅ Screenshot saved to: {output_path}")
            return output_path
        else:
            print(f"❌ Screenshot failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error capturing screenshot: {e}")
        import traceback
        traceback.print_exc()
        return None


def draw_tile_overlays(
    image_path: str,
    rectangles: list,
    tiles: list,
    output_path: str = "html_detection_overlay.png",
    labels: list | None = None
) -> str:
    """
    Draw detection results on the screenshot.
    
    Args:
        image_path: Path to the screenshot
        rectangles: List of (x, y, w, h) tuples
        tiles: List of tile metadata dicts
        output_path: Where to save the annotated image
    
    Returns:
        Path to the annotated image
    """
    print(f"\n🎨 Creating visualization...")
    
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Failed to load image: {image_path}")
        return None
    
    # Create overlay
    overlay = img.copy()
    
    # Colors
    COLOR_IMAGE = (0, 255, 0)      # Green for image tiles
    COLOR_VIDEO = (0, 100, 255)     # Orange for video tiles
    COLOR_TEXT_BG = (0, 0, 0)       # Black background for text
    COLOR_TEXT = (255, 255, 255)    # White text
    
    # Draw each tile
    for i, (rect, tile) in enumerate(zip(rectangles, tiles), 1):
        x, y, w, h = rect
        
        # Choose color based on whether tile has video
        color = COLOR_VIDEO if tile['has_video'] else COLOR_IMAGE
        
        # Draw rectangle
        cv2.rectangle(overlay, (x, y), (x + w, y + h), color, 3)
        
        # Draw corner highlight (small filled square)
        corner_size = 20
        cv2.rectangle(overlay, (x, y), (x + corner_size, y + corner_size), color, -1)
        
        # Prepare label text
        label = f"#{i}"
        if tile['has_video']:
            label += " VIDEO"
        
        # Draw label background
        (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        label_y = y + 50
        cv2.rectangle(overlay, 
                     (x + 5, label_y - text_h - 5),
                     (x + text_w + 10, label_y + baseline),
                     COLOR_TEXT_BG, -1)
        
        # Draw label text
        cv2.putText(overlay, label, (x + 8, label_y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Draw position info (smaller, at bottom)
        pos_text = f"({tile['left']}, {tile['top']})"
        cv2.putText(overlay, pos_text, (x + 8, y + h - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 1)

        # Draw hash label in center if provided
        if labels and i-1 < len(labels) and labels[i-1]:
            hash_text = labels[i-1]
            (ht_w, ht_h), _ = cv2.getTextSize(hash_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cx = x + w // 2
            cy = y + h // 2
            # Background box centered
            bg_x1 = cx - ht_w // 2 - 6
            bg_y1 = cy - ht_h // 2 - 6
            bg_x2 = cx + ht_w // 2 + 6
            bg_y2 = cy + ht_h // 2 + 6
            cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), COLOR_TEXT_BG, -1)
            # Centered text
            text_x = cx - ht_w // 2
            text_y = cy + ht_h // 2 - 4
            cv2.putText(overlay, hash_text, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Add legend
    legend_y = 30
    legend_x = 20
    
    # Legend background
    cv2.rectangle(overlay, (legend_x - 10, legend_y - 25), (legend_x + 350, legend_y + 65), 
                 (0, 0, 0, 128), -1)
    
    # Legend text
    cv2.putText(overlay, "HTML-Based Tile Detection", (legend_x, legend_y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(overlay, f"Total: {len(rectangles)} tiles", (legend_x, legend_y + 25),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    cv2.putText(overlay, f"Video: {sum(1 for t in tiles if t['has_video'])} | Image: {sum(1 for t in tiles if not t['has_video'])}", 
               (legend_x, legend_y + 50),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    # Draw color legend
    legend_y += 80
    cv2.rectangle(overlay, (legend_x, legend_y), (legend_x + 30, legend_y + 20), COLOR_IMAGE, -1)
    cv2.putText(overlay, "= Image Tile", (legend_x + 40, legend_y + 15),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    legend_y += 30
    cv2.rectangle(overlay, (legend_x, legend_y), (legend_x + 30, legend_y + 20), COLOR_VIDEO, -1)
    cv2.putText(overlay, "= Video Tile", (legend_x + 40, legend_y + 15),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Blend overlay with original (for semi-transparency on rectangles)
    alpha = 0.7
    result = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
    
    # Save result
    cv2.imwrite(output_path, result)
    print(f"✅ Visualization saved to: {output_path}")
    
    return output_path


def visualize_html_detection(
    api_url: str = "http://localhost:5000",
    viewport_offset: tuple = None,  # Will use calibrated default from detect_tiles_from_html
    scale_factor: tuple = (0.75, 0.75),  # Calibrated default for 133% zoom
    tile_height: int = 680,
    screenshot_path: str = "temp_screenshot.png",
    output_path: str = "html_detection_overlay.png",
    show_image: bool = True,
    compute_hashes: bool = True
):
    """
    Main function: detect tiles from HTML and visualize on screenshot.
    
    Args:
        api_url: API server URL
        viewport_offset: (x, y) offset for viewport
        scale_factor: (x_scale, y_scale) for coordinate scaling
        tile_height: Height to use for tile rectangles
        screenshot_path: Where to save/load screenshot
        output_path: Where to save visualization
        show_image: Whether to display the result
    """
    print("=" * 80)
    print("HTML TILE DETECTION VISUALIZATION")
    print("=" * 80)
    
    # Step 1: Capture screenshot
    screenshot = capture_screenshot(api_url, screenshot_path)
    if not screenshot:
        print("❌ Failed to capture screenshot")
        return
    
    # Step 2: Detect tiles from HTML
    print("\n🌐 Detecting tiles from HTML...")
    rectangles, tiles = detect_tiles_from_html(
        api_url=api_url,
        viewport_offset=viewport_offset,
        scale_factor=scale_factor,
        tile_height=tile_height
    )
    
    if not rectangles:
        print("❌ No tiles detected")
        return
    
    print(f"✅ Detected {len(rectangles)} tiles")
    
    # Step 3: Compute thumbnail hashes with 2s delay between fetches (optional)
    hashes: list[str] = []
    if compute_hashes:
        import time
        import hashlib
        import base64
        print("\n🔑 Computing thumbnail hashes (SHA-256)...")
        for idx, tile in enumerate(tiles, 1):
            url = tile.get('thumbnail_url')
            if not url:
                hashes.append("N/A")
                continue
            try:
                resp = requests.post(f"{api_url}/fetch-image", json={"url": url}, timeout=20)
                if resp.status_code == 200:
                    payload = resp.json()
                    if payload.get('status') == 'ok' and 'data' in payload:
                        img_bytes = base64.b64decode(payload['data'])
                        h = hashlib.sha256(img_bytes).hexdigest()[:12]
                        hashes.append(h)
                    else:
                        hashes.append("ERR")
                else:
                    hashes.append("HTTP")
            except requests.RequestException:
                hashes.append("NET")
            # Respect 2 second delay to avoid crashing the server
            time.sleep(2)
    else:
        print("\n⏭️  Skipping hash computation")

    # Step 4: Draw overlays with hash labels (if computed)
    result_path = draw_tile_overlays(screenshot, rectangles, tiles, output_path, labels=hashes if hashes else None)
    
    if result_path and show_image:
        # Display the result
        print(f"\n👁️  Displaying visualization...")
        img = cv2.imread(result_path)
        
        # Resize if too large
        max_height = 900
        h, w = img.shape[:2]
        if h > max_height:
            scale = max_height / h
            new_w = int(w * scale)
            img = cv2.resize(img, (new_w, max_height))
        
        cv2.imshow("HTML Detection Overlay", img)
        print("   Press any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    # Summary
    print("\n" + "=" * 80)
    print("VISUALIZATION COMPLETE")
    print("=" * 80)
    print(f"📁 Files created:")
    print(f"   • Screenshot: {screenshot_path}")
    print(f"   • Visualization: {output_path}")
    print("\n📊 Detection summary:")
    print(f"   • Total tiles: {len(rectangles)}")
    print(f"   • Video tiles: {sum(1 for t in tiles if t['has_video'])}")
    print(f"   • Image tiles: {sum(1 for t in tiles if not t['has_video'])}")
    print(f"   • Columns: {len(set(t['left'] for t in tiles))}")


def main():
    """Command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Visualize HTML-based tile detection on a screenshot"
    )
    parser.add_argument('--api-url', default='http://localhost:5000',
                       help='API server URL')
    parser.add_argument('--x-offset', type=int, default=None,
                       help='X offset for viewport (default: auto-detect)')
    parser.add_argument('--y-offset', type=int, default=None,
                       help='Y offset for viewport (default: auto-detect)')
    parser.add_argument('--x-scale', type=float, default=0.75,
                       help='X scale factor (default: 0.75 for 133%% zoom)')
    parser.add_argument('--y-scale', type=float, default=0.75,
                       help='Y scale factor (default: 0.75 for 133%% zoom)')
    parser.add_argument('--tile-height', type=int, default=680,
                       help='Tile height in pixels')
    parser.add_argument('--screenshot', default='temp_screenshot.png',
                       help='Screenshot filename')
    parser.add_argument('--output', default='html_detection_overlay.png',
                       help='Output visualization filename')
    parser.add_argument('--no-show', action='store_true',
                       help='Don\'t display the image (just save it)')
    
    args = parser.parse_args()
    
    # Only pass viewport_offset if both x and y are specified
    viewport_offset = None
    if args.x_offset is not None and args.y_offset is not None:
        viewport_offset = (args.x_offset, args.y_offset)
    
    visualize_html_detection(
        api_url=args.api_url,
        viewport_offset=viewport_offset,
        scale_factor=(args.x_scale, args.y_scale),
        tile_height=args.tile_height,
        screenshot_path=args.screenshot,
        output_path=args.output,
        show_image=not args.no_show
    )


if __name__ == '__main__':
    main()
