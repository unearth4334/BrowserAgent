#!/usr/bin/env python3
"""Process Grok tileview screenshot to identify clickable tiles."""

import sys
from pathlib import Path
import cv2
import numpy as np
from typing import List, Tuple
import tkinter as tk
from PIL import Image, ImageTk

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


class TileDetector:
    """Detect tiles in Grok tileview screenshot."""
    
    def __init__(self, screenshot_path: str):
        self.screenshot_path = screenshot_path
        self.image = cv2.imread(screenshot_path)
        if self.image is None:
            raise ValueError(f"Could not load image: {screenshot_path}")
        self.tiles: List[Tuple[int, int, int, int]] = []  # List of (x, y, w, h)
    
    def detect_tiles(self, bg_color_hex: str = "fcfcfc", method: str = "grid") -> List[Tuple[int, int, int, int]]:
        """Detect tiles by finding regions on the specified background color.
        
        Args:
            bg_color_hex: Hex color of the tileview background (without #)
            method: Detection method - "color", "edges", "adaptive", or "grid"
            
        Returns:
            List of tile rectangles as (x, y, width, height)
        """
        print(f"🔍 Detecting tiles using method: {method}")
        
        if method == "grid":
            return self._detect_by_grid(bg_color_hex)
        elif method == "edges":
            return self._detect_by_edges()
        elif method == "adaptive":
            return self._detect_by_adaptive_threshold()
        else:
            return self._detect_by_color(bg_color_hex)
    
    def _detect_by_grid(self, bg_color_hex: str) -> List[Tuple[int, int, int, int]]:
        """Detect tiles by finding the background grid and extracting tile regions."""
        # Convert hex to BGR for OpenCV
        r, g, b = int(bg_color_hex[0:2], 16), int(bg_color_hex[2:4], 16), int(bg_color_hex[4:6], 16)
        bg_color_bgr = np.array([b, g, r])
        
        print(f"Looking for background grid color: #{bg_color_hex} (BGR: {bg_color_bgr})")
        
        # Create mask for the background color (the grid between tiles)
        tolerance = 15
        lower_bound = np.clip(bg_color_bgr - tolerance, 0, 255)
        upper_bound = np.clip(bg_color_bgr + tolerance, 0, 255)
        
        bg_mask = cv2.inRange(self.image, lower_bound, upper_bound)
        
        # The tiles are the inverse of the background
        tile_mask = cv2.bitwise_not(bg_mask)
        
        # Clean up the mask
        kernel = np.ones((3, 3), np.uint8)
        tile_mask = cv2.morphologyEx(tile_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        tile_mask = cv2.morphologyEx(tile_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Find connected components instead of contours for better separation
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(tile_mask, connectivity=8)
        
        print(f"📦 Found {num_labels - 1} connected tile regions")
        
        tiles = []
        for i in range(1, num_labels):  # Skip label 0 (background)
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            area = stats[i, cv2.CC_STAT_AREA]
            
            aspect_ratio = w / h if h > 0 else 0
            
            print(f"  Region {i}: ({x}, {y}) {w}x{h} (area: {area}, ratio: {aspect_ratio:.2f})", end="")
            
            # Filter by size and aspect ratio
            min_area = 5000  # Minimum tile area
            max_area = 200000  # Maximum tile area  
            min_side = 50  # Minimum dimension
            
            if area < min_area:
                print(f" - ✗ Too small (< {min_area})")
            elif area > max_area:
                print(f" - ✗ Too large (> {max_area})")
            elif w < min_side or h < min_side:
                print(f" - ✗ Side too small (< {min_side})")
            elif aspect_ratio < 0.3 or aspect_ratio > 3.5:
                print(f" - ✗ Bad aspect ratio")
            else:
                tiles.append((x, y, w, h))
                print(f" - ✓ Valid tile")
        
        self.tiles = tiles
        print(f"\n✅ Detected {len(tiles)} valid tiles")
        return tiles
    
    def _detect_by_edges(self) -> List[Tuple[int, int, int, int]]:
        """Detect tiles using edge detection and contours."""
        # Convert to grayscale
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 30, 100)  # Lower thresholds to detect more edges
        
        # Close gaps in edges
        kernel = np.ones((5, 5), np.uint8)
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Find contours - use RETR_TREE to get internal contours
        contours, hierarchy = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        print(f"📦 Found {len(contours)} edge regions with hierarchy")
        
        return self._filter_contours(contours)
    
    def _detect_by_adaptive_threshold(self) -> List[Tuple[int, int, int, int]]:
        """Detect tiles using adaptive thresholding."""
        # Convert to grayscale
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        print(f"📦 Found {len(contours)} threshold regions")
        
        return self._filter_contours(contours)
    
    def _detect_by_color(self, bg_color_hex: str) -> List[Tuple[int, int, int, int]]:
        """Original color-based detection."""
        # Convert hex to BGR for OpenCV
        r, g, b = int(bg_color_hex[0:2], 16), int(bg_color_hex[2:4], 16), int(bg_color_hex[4:6], 16)
        bg_color_bgr = np.array([b, g, r])
        
        print(f"Looking for background color: #{bg_color_hex} (BGR: {bg_color_bgr})")
        
        # Create mask for the background color (with some tolerance)
        tolerance = 10
        lower_bound = np.clip(bg_color_bgr - tolerance, 0, 255)
        upper_bound = np.clip(bg_color_bgr + tolerance, 0, 255)
        
        mask = cv2.inRange(self.image, lower_bound, upper_bound)
        
        # Invert mask - we want the tiles (non-background)
        tile_mask = cv2.bitwise_not(mask)
        
        # Apply morphological operations to clean up the mask
        kernel = np.ones((5, 5), np.uint8)
        tile_mask = cv2.morphologyEx(tile_mask, cv2.MORPH_CLOSE, kernel)
        tile_mask = cv2.morphologyEx(tile_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(tile_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        print(f"📦 Found {len(contours)} color-based regions")
        
        return self._filter_contours(contours)
    
    def _filter_contours(self, contours) -> List[Tuple[int, int, int, int]]:
        """Filter contours to find valid tiles."""
        # Filter contours by size - tiles should be reasonably large
        min_area = 10000  # Minimum tile area in pixels (increased for actual tiles)
        max_area = 800000  # Maximum tile area
        min_side = 80  # Minimum width or height
        
        tiles = []
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            aspect_ratio = w / h if h > 0 else 0
            
            print(f"  Region {i+1}: ({x}, {y}) {w}x{h} (area: {area}, ratio: {aspect_ratio:.2f})", end="")
            
            # Filter by area and aspect ratio
            if area < min_area:
                print(f" - ✗ Too small (< {min_area})")
            elif area > max_area:
                print(f" - ✗ Too large (> {max_area})")
            elif w < min_side or h < min_side:
                print(f" - ✗ Side too small (< {min_side})")
            elif aspect_ratio < 0.5 or aspect_ratio > 2.0:
                print(f" - ✗ Bad aspect ratio (not in 0.5-2.0)")
            else:
                tiles.append((x, y, w, h))
                print(f" - ✓ Valid tile")
        
        self.tiles = tiles
        print(f"\n✅ Detected {len(tiles)} valid tiles")
        return tiles


class TileViewer:
    """GUI to display screenshot with detected tiles overlaid."""
    
    def __init__(self, screenshot_path: str, tiles: List[Tuple[int, int, int, int]]):
        self.screenshot_path = screenshot_path
        self.tiles = tiles
        
        # Load image with PIL for display
        self.pil_image = Image.open(screenshot_path)
        self.display_image = self.pil_image.copy()
        
        # Draw rectangles on display image
        self._draw_tiles()
        
        # Create GUI
        self.root = tk.Tk()
        self.root.title(f"Tile Detection - {len(tiles)} tiles found")
        
        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(self.display_image)
        
        # Create canvas
        canvas = tk.Canvas(self.root, width=self.display_image.width, height=self.display_image.height)
        canvas.pack()
        canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # Add info label
        info_text = f"Detected {len(tiles)} tiles | Green rectangles show tile boundaries"
        info_label = tk.Label(self.root, text=info_text, pady=10)
        info_label.pack()
        
        # Add export button
        export_btn = tk.Button(self.root, text="Export Tile Coordinates", command=self._export_tiles)
        export_btn.pack(pady=5)
        
        print(f"\n🖼️  GUI opened with {len(tiles)} tiles highlighted")
        print("Close the window when done inspecting.")
    
    def _draw_tiles(self):
        """Draw green rectangles over detected tiles."""
        from PIL import ImageDraw
        
        draw = ImageDraw.Draw(self.display_image)
        
        for i, (x, y, w, h) in enumerate(self.tiles):
            # Draw green rectangle
            draw.rectangle(
                [(x, y), (x + w, y + h)],
                outline="green",
                width=3
            )
            # Draw tile number
            draw.text((x + 5, y + 5), str(i + 1), fill="green")
    
    def _export_tiles(self):
        """Export tile coordinates to a file."""
        output_path = Path(self.screenshot_path).parent / "detected_tiles.txt"
        
        with open(output_path, 'w') as f:
            f.write(f"Detected {len(self.tiles)} tiles\n")
            f.write("Format: tile_number, x, y, width, height, center_x, center_y\n\n")
            
            for i, (x, y, w, h) in enumerate(self.tiles, 1):
                center_x = x + w // 2
                center_y = y + h // 2
                f.write(f"{i}, {x}, {y}, {w}, {h}, {center_x}, {center_y}\n")
        
        print(f"✅ Exported tile coordinates to: {output_path}")
    
    def show(self):
        """Display the GUI."""
        self.root.mainloop()


def main():
    screenshot_path = "grok_test_screenshots/novnc_poc.png"
    
    if not Path(screenshot_path).exists():
        print(f"❌ Screenshot not found: {screenshot_path}")
        return 1
    
    print(f"🚀 Processing screenshot: {screenshot_path}")
    
    # Allow method to be passed as command line argument
    method = sys.argv[1] if len(sys.argv) > 1 else "edges"
    
    try:
        # Detect tiles
        detector = TileDetector(screenshot_path)
        
        # Save edge detection debug image
        gray = cv2.cvtColor(detector.image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        debug_path = Path(screenshot_path).parent / "debug_edges.png"
        cv2.imwrite(str(debug_path), edges)
        print(f"💾 Saved edge detection debug image: {debug_path}")
        
        tiles = detector.detect_tiles(method=method)
        
        if not tiles:
            print("⚠️  No tiles detected. Try adjusting the detection parameters.")
            return 1
        
        # Show GUI with detected tiles
        viewer = TileViewer(screenshot_path, tiles)
        viewer.show()
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
