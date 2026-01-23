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
        self.height, self.width = self.image.shape[:2]
        
        # Compute content statistics for adaptive thresholding
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.content_mask = (gray < 200).astype(np.uint8) * 255
        self.row_sums = np.sum(self.content_mask > 0, axis=1)
        self.col_sums = np.sum(self.content_mask > 0, axis=0)
    
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
        
        # Use adaptive tolerance based on local variance
        tolerance = 15  # Balanced tolerance
        lower_bound = np.clip(bg_color_bgr - tolerance, 0, 255)
        upper_bound = np.clip(bg_color_bgr + tolerance, 0, 255)
        
        bg_mask = cv2.inRange(self.image, lower_bound, upper_bound)
        
        # The tiles are the inverse of the background
        tile_mask = cv2.bitwise_not(bg_mask)
        
        # Clean up the mask - be careful not to merge tiles
        kernel_small = np.ones((3, 3), np.uint8)
        
        # Remove small noise first
        tile_mask = cv2.morphologyEx(tile_mask, cv2.MORPH_OPEN, kernel_small, iterations=1)
        # Fill small gaps within tiles, but not between them
        tile_mask = cv2.morphologyEx(tile_mask, cv2.MORPH_CLOSE, kernel_small, iterations=2)
        
        # Find connected components instead of contours for better separation
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(tile_mask, connectivity=8)
        
        print(f"📦 Found {num_labels - 1} connected tile regions")
        
        tiles = []
        
        # Compute adaptive thresholds based on all detected regions
        all_areas = [stats[i, cv2.CC_STAT_AREA] for i in range(1, num_labels)]
        if all_areas:
            area_mean = np.mean(all_areas)
            area_std = np.std(all_areas)
            # Use statistical thresholds: tiles should be within reasonable range
            adaptive_min_area = max(5000, area_mean - 2 * area_std) if area_std > 0 else 5000
            adaptive_max_area = min(200000, area_mean + 2 * area_std) if area_std > 0 else 200000
            print(f"📊 Area statistics: mean={area_mean:.0f}, std={area_std:.0f}")
            print(f"   Adaptive thresholds: min={adaptive_min_area:.0f}, max={adaptive_max_area:.0f}")
        else:
            adaptive_min_area = 5000
            adaptive_max_area = 200000
        
        for i in range(1, num_labels):  # Skip label 0 (background)
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            area = stats[i, cv2.CC_STAT_AREA]
            
            aspect_ratio = w / h if h > 0 else 0
            
            print(f"  Region {i}: ({x}, {y}) {w}x{h} (area: {area}, ratio: {aspect_ratio:.2f})", end="")
            
            # Filter by size and aspect ratio with adaptive thresholds
            min_area = adaptive_min_area
            max_area = adaptive_max_area
            min_side = 50  # Minimum dimension
            
            # Check if region has sustained content (like widest region detector)
            region_mask = (labels == i).astype(np.uint8) * 255
            region_content = cv2.bitwise_and(self.content_mask, region_mask)
            content_density = np.sum(region_content > 0) / area if area > 0 else 0
            
            if area < min_area:
                print(f" - ✗ Too small (< {min_area:.0f})")
            elif area > max_area:
                print(f" - ✗ Too large (> {max_area:.0f})")
            elif w < min_side or h < min_side:
                print(f" - ✗ Side too small (< {min_side})")
            elif aspect_ratio < 0.3 or aspect_ratio > 3.5:
                print(f" - ✗ Bad aspect ratio")
            elif content_density < 0.1:  # Tiles should have some content
                print(f" - ✗ Low content density ({content_density:.2f})")
            else:
                tiles.append((x, y, w, h))
                print(f" - ✓ Valid tile (density={content_density:.2f})")
        
        self.tiles = tiles
        print(f"\n✅ Detected {len(tiles)} valid tiles")
        
        # Try to find missing tiles by extrapolating grid
        if tiles:
            additional_tiles = self._extrapolate_grid_and_verify(tiles)
            if additional_tiles:
                print(f"🔍 Found {len(additional_tiles)} additional tiles via grid extrapolation")
                tiles.extend(additional_tiles)
                self.tiles = tiles
                print(f"✅ Total tiles after extrapolation: {len(tiles)}")
        
        return tiles
    
    def _extrapolate_grid_and_verify(self, detected_tiles: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """Extrapolate grid from detected tiles and verify candidate locations with edge detection."""
        if len(detected_tiles) < 3:
            return []  # Need at least 3 tiles to establish a grid
        
        # Extract tile centers and use clustering to find dominant grid positions
        centers = [(x + w//2, y + h//2) for x, y, w, h in detected_tiles]
        xs = [c[0] for c in centers]
        ys = [c[1] for c in centers]
        
        # Estimate typical tile size from detected tiles
        avg_w = int(np.mean([w for _, _, w, _ in detected_tiles]))
        avg_h = int(np.mean([h for _, _, _, h in detected_tiles]))
        
        # Use clustering to find dominant column and row positions
        from sklearn.cluster import DBSCAN
        
        # Cluster X positions to find columns (tighter tolerance for better separation)
        x_tolerance = avg_w // 20  # Reduced from //10 to better distinguish columns
        xs_array = np.array(xs).reshape(-1, 1)
        x_clustering = DBSCAN(eps=x_tolerance, min_samples=1).fit(xs_array)
        
        # Get representative X position for each cluster (column)
        unique_x_labels = set(x_clustering.labels_)
        grid_xs = []
        for label in sorted(unique_x_labels):
            cluster_xs = [xs[i] for i in range(len(xs)) if x_clustering.labels_[i] == label]
            grid_xs.append(int(np.mean(cluster_xs)))
        
        # Cluster Y positions to find rows (tighter tolerance)
        y_tolerance = avg_h // 20  # Reduced from //10
        ys_array = np.array(ys).reshape(-1, 1)
        y_clustering = DBSCAN(eps=y_tolerance, min_samples=1).fit(ys_array)
        
        # Get representative Y position for each cluster (row)
        unique_y_labels = set(y_clustering.labels_)
        grid_ys = []
        for label in sorted(unique_y_labels):
            cluster_ys = [ys[i] for i in range(len(ys)) if y_clustering.labels_[i] == label]
            grid_ys.append(int(np.mean(cluster_ys)))
        
        grid_xs = sorted(grid_xs)
        grid_ys = sorted(grid_ys)
        
        # Compute spacing from detected grid positions
        x_spacings = [grid_xs[i+1] - grid_xs[i] for i in range(len(grid_xs)-1)] if len(grid_xs) > 1 else [avg_w + 10]
        y_spacings = [grid_ys[i+1] - grid_ys[i] for i in range(len(grid_ys)-1)] if len(grid_ys) > 1 else [avg_h + 10]
        
        x_spacing = int(np.median(x_spacings)) if x_spacings else avg_w + 10
        y_spacing = int(np.median(y_spacings)) if y_spacings else avg_h + 10
        
        print(f"📐 Grid analysis: {len(grid_xs)} cols x {len(grid_ys)} rows detected")
        print(f"   Spacing: x={x_spacing}, y={y_spacing}, avg_size={avg_w}x{avg_h}")
        
        # More aggressive extrapolation - assume 5 column layout
        # Look for the leftmost possible column position
        min_x, max_x = min(grid_xs), max(grid_xs)
        min_y, max_y = min(grid_ys), max(grid_ys)
        
        # First, fill in missing columns within the detected range
        complete_grid_xs = []
        for i in range(len(grid_xs) - 1):
            complete_grid_xs.append(grid_xs[i])
            gap = grid_xs[i+1] - grid_xs[i]
            # If gap is larger than 1.4x spacing, there's likely a missing column
            if gap > x_spacing * 1.4:
                num_missing = round(gap / x_spacing) - 1
                for j in range(1, num_missing + 1):
                    missing_x = grid_xs[i] + j * x_spacing
                    complete_grid_xs.append(missing_x)
        complete_grid_xs.append(grid_xs[-1])
        complete_grid_xs = sorted(set(complete_grid_xs))
        
        complete_grid_ys = []
        for i in range(len(grid_ys) - 1):
            complete_grid_ys.append(grid_ys[i])
            gap = grid_ys[i+1] - grid_ys[i]
            # If gap is larger than 1.4x spacing, there's likely a missing row
            if gap > y_spacing * 1.4:
                num_missing = round(gap / y_spacing) - 1
                for j in range(1, num_missing + 1):
                    missing_y = grid_ys[i] + j * y_spacing
                    complete_grid_ys.append(missing_y)
        complete_grid_ys.append(grid_ys[-1])
        complete_grid_ys = sorted(set(complete_grid_ys))
        
        # Aggressively add columns on the left until we hit the edge
        final_grid_xs = list(complete_grid_xs)
        leftmost = min(final_grid_xs)
        while True:
            candidate_x = leftmost - x_spacing
            # Must have room for at least half a tile
            if candidate_x < avg_w // 3:
                break
            final_grid_xs.insert(0, candidate_x)
            leftmost = candidate_x
        
        # Add columns on the right until we hit the edge
        rightmost = max(final_grid_xs)
        while True:
            candidate_x = rightmost + x_spacing
            # Must have room for at least half a tile
            if candidate_x > self.width - avg_w // 3:
                break
            final_grid_xs.append(candidate_x)
            rightmost = candidate_x
        
        # Add rows above and below
        final_grid_ys = list(complete_grid_ys)
        topmost = min(final_grid_ys)
        while True:
            candidate_y = topmost - y_spacing
            if candidate_y < avg_h // 3:
                break
            final_grid_ys.insert(0, candidate_y)
            topmost = candidate_y
        
        bottommost = max(final_grid_ys)
        while True:
            candidate_y = bottommost + y_spacing
            if candidate_y > self.height - avg_h // 3:
                break
            final_grid_ys.append(candidate_y)
            bottommost = candidate_y
        
        print(f"📍 Complete grid: {len(final_grid_xs)} cols x {len(final_grid_ys)} rows (extrapolated)")
        
        # Check which grid positions are missing tiles
        existing_centers_set = set((x + w//2, y + h//2) for x, y, w, h in detected_tiles)
        
        # Build a map of detected row Y centers to actual tile Y positions and heights
        row_y_map = {}  # center_y -> (actual_tile_y, actual_tile_h)
        for x, y, w, h in detected_tiles:
            center_y = y + h // 2
            # Find closest grid row
            closest_grid_y = min(grid_ys, key=lambda gy: abs(gy - center_y))
            if closest_grid_y not in row_y_map:
                row_y_map[closest_grid_y] = []
            row_y_map[closest_grid_y].append((y, h))
        
        # For each row, compute the typical Y position and height
        row_y_positions = {}
        for grid_y, tiles_info in row_y_map.items():
            avg_y = int(np.mean([y for y, h in tiles_info]))
            avg_row_h = int(np.mean([h for y, h in tiles_info]))
            row_y_positions[grid_y] = (avg_y, avg_row_h)
        
        additional_tiles = []
        tolerance = min(x_spacing, y_spacing) // 4  # Tighter tolerance for matching
        
        for grid_x in final_grid_xs:
            for grid_y in final_grid_ys:
                # Check if this position already has a tile
                found_existing = False
                for ex_x, ex_y in existing_centers_set:
                    if abs(grid_x - ex_x) < tolerance and abs(grid_y - ex_y) < tolerance:
                        found_existing = True
                        break
                
                if not found_existing:
                    # Find the closest detected row to snap Y position
                    closest_grid_y = min(grid_ys, key=lambda gy: abs(gy - grid_y))
                    
                    # Check if this grid position is too far from detected rows
                    if abs(grid_y - closest_grid_y) > y_spacing // 3:
                        continue
                    
                    # Use actual tile Y position and height from that row if available
                    if closest_grid_y in row_y_positions:
                        actual_y, actual_h = row_y_positions[closest_grid_y]
                        tile_x = grid_x - avg_w // 2
                        tile_y = actual_y  # Use actual row Y position
                        tile_h = actual_h  # Use actual row height
                    else:
                        # Fallback to computed position
                        tile_x = grid_x - avg_w // 2
                        tile_y = grid_y - avg_h // 2
                        tile_h = avg_h
                    
                    # Check bounds
                    if tile_x < 0 or tile_y < 0 or tile_x + avg_w > self.width or tile_y + tile_h > self.height:
                        continue
                    
                    # Check if candidate overlaps significantly with existing tiles
                    candidate_rect = (tile_x, tile_y, avg_w, tile_h)
                    if self._overlaps_existing_tile(candidate_rect, detected_tiles):
                        continue
                    
                    if self._verify_tile_at_location(tile_x, tile_y, avg_w, tile_h):
                        additional_tiles.append((tile_x, tile_y, avg_w, tile_h))
                        print(f"  ✓ Found missing tile at grid position ({grid_x}, {grid_y}) -> bbox ({tile_x}, {tile_y}) {avg_w}x{tile_h}")
        
        return additional_tiles
    
    def _overlaps_existing_tile(self, candidate: tuple, existing_tiles: list) -> bool:
        """Check if candidate tile overlaps significantly with any existing tile."""
        cx, cy, cw, ch = candidate
        candidate_area = cw * ch
        
        for ex, ey, ew, eh in existing_tiles:
            # Compute intersection
            ix1 = max(cx, ex)
            iy1 = max(cy, ey)
            ix2 = min(cx + cw, ex + ew)
            iy2 = min(cy + ch, ey + eh)
            
            if ix2 > ix1 and iy2 > iy1:
                intersection_area = (ix2 - ix1) * (iy2 - iy1)
                # If overlap is more than 30% of candidate area, reject it
                if intersection_area / candidate_area > 0.3:
                    return True
        
        return False
    
    def _verify_tile_at_location(self, x: int, y: int, w: int, h: int) -> bool:
        """Verify if there's a tile at the given location using edge detection and content analysis."""
        # Extract region
        region = self.image[y:y+h, x:x+w]
        if region.size == 0:
            return False
        
        # Convert to grayscale
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (w * h)
        
        # Check content
        content = (gray < 200).astype(np.uint8) * 255
        content_density = np.sum(content > 0) / (w * h)
        
        # Check if region has tile-like borders (edges around perimeter)
        border_thickness = 5
        top_border = edges[:border_thickness, :]
        bottom_border = edges[-border_thickness:, :]
        left_border = edges[:, :border_thickness]
        right_border = edges[:, -border_thickness:]
        
        border_edge_density = (
            np.sum(top_border > 0) + np.sum(bottom_border > 0) +
            np.sum(left_border > 0) + np.sum(right_border > 0)
        ) / (2 * border_thickness * (w + h))
        
        # Check all 4 borders individually - all should have edges (tile boundary)
        top_edge = np.sum(top_border > 0) / (border_thickness * w)
        bottom_edge = np.sum(bottom_border > 0) / (border_thickness * w)
        left_edge = np.sum(left_border > 0) / (border_thickness * h)
        right_edge = np.sum(right_border > 0) / (border_thickness * h)
        min_border_edge = min(top_edge, bottom_edge, left_edge, right_edge)
        
        # Tile should have:
        # 1. High content density (actual image content, not UI elements)
        # 2. Some edges (structure)
        # 3. Strong borders on all sides (complete tile boundary)
        has_content = content_density > 0.40  # Tiles should be mostly filled
        has_edges = edge_density > 0.02  # Some edge structure
        has_border = border_edge_density > 0.04  # Relaxed to allow tiles with weak borders on some sides
        
        print(f"    Verify ({x},{y}): content={content_density:.2f}, edges={edge_density:.2f}, border={border_edge_density:.2f}, min_side={min_border_edge:.2f}", end="")
        
        return has_content and has_edges and has_border
    
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


class TileDiagnostics:
    """Diagnostic tools for understanding tile detection."""
    
    @staticmethod
    def show_profiles(detector: TileDetector, tiles: List[Tuple[int, int, int, int]]):
        """Show content profiles to understand detection."""
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Row sums (vertical profile)
        ax1.plot(detector.row_sums, range(detector.height), 'b-', linewidth=1)
        ax1.set_xlabel('Content Pixels per Row')
        ax1.set_ylabel('Y Position')
        ax1.set_title('Vertical Profile - Content Distribution')
        ax1.invert_yaxis()
        ax1.grid(True, alpha=0.3)
        
        # Mark tile regions
        for x, y, w, h in tiles:
            ax1.axhspan(y, y+h, alpha=0.2, color='green')
        
        # Column sums (horizontal profile)
        ax2.plot(range(detector.width), detector.col_sums, 'b-', linewidth=1)
        ax2.set_xlabel('X Position')
        ax2.set_ylabel('Content Pixels per Column')
        ax2.set_title('Horizontal Profile - Content Distribution')
        ax2.grid(True, alpha=0.3)
        
        # Mark tile regions
        for x, y, w, h in tiles:
            ax2.axvspan(x, x+w, alpha=0.2, color='green')
        
        plt.tight_layout()
        plt.show()


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
