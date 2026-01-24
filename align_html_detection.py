#!/usr/bin/env python3
"""
Align HTML-based tile detection using visual detection as ground truth.
Uses visual detection to calibrate the viewport offset for accurate HTML positioning.
"""

import cv2
import numpy as np
import requests
import base64
from typing import List, Tuple, Dict, Optional
from detect_tiles_from_html import detect_tiles_from_html, parse_tile_positions, fetch_page_source
from detect_grok_tiles import TileDetector


def capture_screenshot_from_api(api_url: str = "http://localhost:5000") -> Optional[np.ndarray]:
    """Capture screenshot and return as numpy array."""
    try:
        response = requests.post(f"{api_url}/screenshot", json={"format": "png"}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            image_data = base64.b64decode(data['data'])
            
            # Convert to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        return None
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None


def calculate_viewport_offset_and_scale(
    visual_rects: List[Tuple[int, int, int, int]],
    html_tiles: List[Dict]
) -> Tuple[Tuple[int, int], Tuple[float, float]]:
    """
    Calculate viewport offset and scaling factor by comparing visual and HTML positions.
    
    Args:
        visual_rects: List of (x, y, w, h) from visual detection
        html_tiles: List of tile dicts with 'left' and 'top' from HTML
    
    Returns:
        ((x_offset, y_offset), (x_scale, y_scale)) tuple
    """
    if not visual_rects or not html_tiles:
        return ((300, 100), (1.0, 1.0))  # Default
    
    # Sort both by position to match corresponding tiles
    visual_sorted = sorted(visual_rects, key=lambda r: (r[0], r[1]))
    html_sorted = sorted(html_tiles, key=lambda t: (t['left'], t['top']))
    
    # Use multiple tiles to calculate scale and offset
    matches_to_try = min(len(visual_sorted), len(html_sorted))
    
    if matches_to_try < 2:
        # Not enough tiles to calculate scale, just use offset
        if matches_to_try == 1:
            v_rect = visual_sorted[0]
            h_tile = html_sorted[0]
            x_offset = v_rect[0] - h_tile['left']
            y_offset = v_rect[1] - h_tile['top']
            return ((x_offset, y_offset), (1.0, 1.0))
        return ((300, 100), (1.0, 1.0))
    
    # Calculate uniform scale factor from tile widths
    # For browser zoom/DPI scaling, X and Y scales should be identical
    scales = []
    
    # Calculate scale from multiple tile widths
    for i in range(min(5, matches_to_try)):
        v_rect = visual_sorted[i]
        h_tile = html_sorted[i]
        
        # Calculate scale using width
        if h_tile['width'] > 0:
            scale_from_width = v_rect[2] / h_tile['width']
            scales.append(scale_from_width)
    
    # Use median scale (robust to outliers)
    scale = np.median(scales) if scales else 0.75
    
    # Use same scale for both X and Y (uniform scaling)
    x_scale = scale
    y_scale = scale
    
    # Calculate offset using the topmost, leftmost tile
    # This ensures we use tiles from the top row if available
    # screen = offset + (html * scale)
    # offset = screen - (html * scale)
    
    # Find tile with minimum Y (topmost), then minimum X (leftmost)
    v_top = min(visual_sorted, key=lambda r: (r[1], r[0]))
    h_top = min(html_sorted, key=lambda t: (t['top'], t['left']))
    
    x_offset = v_top[0] - (h_top['left'] * x_scale)
    y_offset = v_top[1] - (h_top['top'] * y_scale)
    
    return ((int(x_offset), int(y_offset)), (float(x_scale), float(y_scale)))


def align_and_visualize(
    api_url: str = "http://localhost:5000",
    screenshot_path: str = "temp_screenshot.png",
    output_path: str = "aligned_detection.png",
    show_comparison: bool = True
):
    """
    Main alignment function that:
    1. Captures screenshot
    2. Runs visual detection
    3. Fetches HTML positions
    4. Calculates correct viewport offset
    5. Visualizes both detections with alignment info
    """
    print("=" * 80)
    print("HTML DETECTION ALIGNMENT USING VISUAL DETECTION")
    print("=" * 80)
    
    # Step 1: Capture screenshot
    print("\n📸 Capturing screenshot...")
    img = capture_screenshot_from_api(api_url)
    if img is None:
        print("❌ Failed to capture screenshot")
        return
    
    cv2.imwrite(screenshot_path, img)
    print(f"✅ Screenshot saved: {screenshot_path}")
    
    # Step 2: Run visual detection
    print("\n👁️  Running visual tile detection...")
    try:
        detector = TileDetector(screenshot_path)
        visual_rects = detector.detect_tiles(method="grid")
    except Exception as e:
        print(f"❌ Visual detection error: {e}")
        visual_rects = []
    
    if not visual_rects:
        print("❌ Visual detection failed - no tiles found")
        print("   Try the robust detection with background toggle")
        return
    
    print(f"✅ Visual detection found {len(visual_rects)} tiles")
    
    # Step 3: Fetch HTML positions
    print("\n🌐 Fetching HTML tile positions...")
    html_content = fetch_page_source(api_url)
    html_tiles = parse_tile_positions(html_content)
    
    if not html_tiles:
        print("❌ HTML parsing failed - no tiles found")
        return
    
    print(f"✅ HTML parsing found {len(html_tiles)} tiles")
    
    # Step 4: Calculate viewport offset and scaling
    print("\n🔧 Calculating viewport offset and scaling...")
    old_offset = (300, 100)
    old_scale = (1.0, 1.0)
    (new_offset, new_scale) = calculate_viewport_offset_and_scale(visual_rects, html_tiles)
    
    print(f"   Old offset: {old_offset}, scale: {old_scale}")
    print(f"   New offset: {new_offset}, scale: ({new_scale[0]:.3f}, {new_scale[1]:.3f})")
    print(f"   Offset adjustment: ({new_offset[0] - old_offset[0]:+d}, {new_offset[1] - old_offset[1]:+d})")
    print(f"   Scale adjustment: ({new_scale[0] - old_scale[0]:+.3f}, {new_scale[1] - old_scale[1]:+.3f})")
    
    # Step 5: Apply offset and scale to convert HTML positions to screen coordinates
    print("\n🔄 Converting HTML positions with corrected offset and scale...")
    html_rects = []
    for tile in html_tiles:
        x = new_offset[0] + int(tile['left'] * new_scale[0])
        y = new_offset[1] + int(tile['top'] * new_scale[1])
        w = int(tile['width'] * new_scale[0])
        h = int(680 * new_scale[1])  # Estimated height with scale
        html_rects.append((x, y, w, h))
    
    # Step 6: Create visualization
    print("\n🎨 Creating comparison visualization...")
    overlay = img.copy()
    
    # Draw visual detection in green
    for rect in visual_rects:
        x, y, w, h = rect
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 0), 3)
    
    # Draw HTML detection in blue
    for rect in html_rects:
        x, y, w, h = rect
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (255, 0, 0), 2)
    
    # Add legend
    legend_y = 30
    legend_x = 20
    
    # Background
    cv2.rectangle(overlay, (legend_x - 10, legend_y - 25), (legend_x + 450, legend_y + 120),
                 (0, 0, 0), -1)
    
    # Title
    cv2.putText(overlay, "Alignment Comparison", (legend_x, legend_y),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Visual detection info
    cv2.rectangle(overlay, (legend_x, legend_y + 15), (legend_x + 30, legend_y + 35), (0, 255, 0), -1)
    cv2.putText(overlay, f"= Visual Detection ({len(visual_rects)} tiles)", 
               (legend_x + 40, legend_y + 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # HTML detection info
    cv2.rectangle(overlay, (legend_x, legend_y + 45), (legend_x + 30, legend_y + 65), (255, 0, 0), -1)
    cv2.putText(overlay, f"= HTML Detection ({len(html_rects)} tiles)", 
               (legend_x + 40, legend_y + 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    # Offset info
    cv2.putText(overlay, f"Viewport Offset: {new_offset}", 
               (legend_x, legend_y + 90),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.putText(overlay, f"Scale: ({new_scale[0]:.3f}, {new_scale[1]:.3f})", 
               (legend_x, legend_y + 110),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    # Save result
    cv2.imwrite(output_path, overlay)
    print(f"✅ Visualization saved: {output_path}")
    
    # Calculate alignment quality
    print("\n📊 Alignment Analysis:")
    
    # Match tiles and calculate distances
    if len(visual_rects) == len(html_rects):
        distances = []
        for v_rect, h_rect in zip(visual_rects, html_rects):
            # Distance between centers
            v_cx, v_cy = v_rect[0] + v_rect[2]//2, v_rect[1] + v_rect[3]//2
            h_cx, h_cy = h_rect[0] + h_rect[2]//2, h_rect[1] + h_rect[3]//2
            dist = np.sqrt((v_cx - h_cx)**2 + (v_cy - h_cy)**2)
            distances.append(dist)
        
        avg_distance = np.mean(distances)
        max_distance = np.max(distances)
        
        print(f"   Average alignment error: {avg_distance:.1f} pixels")
        print(f"   Maximum alignment error: {max_distance:.1f} pixels")
        
        if avg_distance < 50:
            print("   ✅ Excellent alignment!")
        elif avg_distance < 100:
            print("   ⚠️  Good alignment, minor offset")
        else:
            print("   ❌ Poor alignment, check viewport offset")
    else:
        print(f"   ⚠️  Tile count mismatch: {len(visual_rects)} visual vs {len(html_rects)} HTML")
    
    # Display if requested
    if show_comparison:
        print("\n👁️  Displaying comparison...")
        display_img = overlay.copy()
        
        # Resize if too large
        max_height = 900
        h, w = display_img.shape[:2]
        if h > max_height:
            scale = max_height / h
            new_w = int(w * scale)
            display_img = cv2.resize(display_img, (new_w, max_height))
        
        cv2.imshow("Alignment Comparison (Green=Visual, Blue=HTML)", display_img)
        print("   Press any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    print("\n" + "=" * 80)
    print("ALIGNMENT COMPLETE")
    print("=" * 80)
    print(f"\n💡 Use these values in detect_tiles_from_html:")
    print(f"   viewport_offset={new_offset}")
    print(f"   scale_factor={new_scale}")
    
    return (new_offset, new_scale)


def main():
    """Command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Align HTML detection using visual detection"
    )
    parser.add_argument('--api-url', default='http://localhost:5000',
                       help='API server URL')
    parser.add_argument('--screenshot', default='temp_screenshot.png',
                       help='Screenshot filename')
    parser.add_argument('--output', default='aligned_detection.png',
                       help='Output filename')
    parser.add_argument('--no-show', action='store_true',
                       help='Don\'t display the image')
    
    args = parser.parse_args()
    
    result = align_and_visualize(
        api_url=args.api_url,
        screenshot_path=args.screenshot,
        output_path=args.output,
        show_comparison=not args.no_show
    )
    
    if result:
        offset, scale = result
        print(f"\n✅ Calibrated viewport offset: {offset}")
        print(f"✅ Calibrated scale factor: ({scale[0]:.3f}, {scale[1]:.3f})")


if __name__ == '__main__':
    main()
