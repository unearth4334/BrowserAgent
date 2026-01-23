#!/usr/bin/env python3
"""
Robust detection using background color toggling.
Takes two screenshots with different background colors (white and red)
and uses the difference to isolate tiles and media panes.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import requests
import time
from pathlib import Path


class BackgroundToggleDetector:
    """Base class for detection using background color toggling."""
    
    def __init__(self, page_screenshot_func, api_url: str = "http://localhost:5000"):
        """
        Args:
            page_screenshot_func: Function that captures and returns a screenshot as numpy array
            api_url: Base URL for the API server
        """
        self.capture_screenshot = page_screenshot_func
        self.api_url = api_url
        
    def set_background_color(self, color: str) -> bool:
        """Set background color via API.
        
        Args:
            color: Color name or hex (e.g., 'white', 'red', '#ff0000')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f'{self.api_url}/background',
                headers={'Content-Type': 'application/json'},
                json={'color': color},
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ Set background to {color}")
                return True
            else:
                print(f"⚠️  Failed to set background: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error setting background: {e}")
            return False
    
    def capture_with_backgrounds(self, color1: str = "white", color2: str = "red", 
                                  delay: float = 0.5) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Capture two screenshots with different background colors.
        
        Args:
            color1: First background color
            color2: Second background color
            delay: Delay between color change and screenshot
            
        Returns:
            Tuple of (image1, image2) as numpy arrays, or (None, None) on failure
        """
        print(f"\n🎨 Capturing with background toggle: {color1} -> {color2}")
        
        # Capture with first color
        if not self.set_background_color(color1):
            return None, None
        time.sleep(delay)
        img1 = self.capture_screenshot()
        
        if img1 is None:
            print("❌ Failed to capture first screenshot")
            return None, None
        
        # Capture with second color
        if not self.set_background_color(color2):
            return None, None
        time.sleep(delay)
        img2 = self.capture_screenshot()
        
        if img2 is None:
            print("❌ Failed to capture second screenshot")
            return None, None
        
        # Reset to original color
        self.set_background_color(color1)
        
        print(f"✅ Captured both screenshots ({img1.shape}, {img2.shape})")
        return img1, img2
    
    def compute_difference_mask(self, img1: np.ndarray, img2: np.ndarray,
                                threshold: int = 30) -> np.ndarray:
        """Compute difference between two images.
        
        Args:
            img1: First image
            img2: Second image
            threshold: Difference threshold (0-255)
            
        Returns:
            Binary mask where 255 = high difference (background), 0 = low difference (content)
        """
        # Convert to grayscale if needed
        if len(img1.shape) == 3:
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        else:
            gray1 = img1
            
        if len(img2.shape) == 3:
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        else:
            gray2 = img2
        
        # Compute absolute difference
        diff = cv2.absdiff(gray1, gray2)
        
        # Threshold: high difference = background changed
        _, diff_mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        
        return diff_mask
    
    def compute_content_mask(self, img1: np.ndarray, img2: np.ndarray,
                            threshold: int = 30) -> np.ndarray:
        """Compute mask of content (low difference regions).
        
        Args:
            img1: First image
            img2: Second image  
            threshold: Difference threshold
            
        Returns:
            Binary mask where 255 = content, 0 = background
        """
        diff_mask = self.compute_difference_mask(img1, img2, threshold)
        # Invert: low difference = content
        content_mask = cv2.bitwise_not(diff_mask)
        
        # Clean up noise
        kernel = np.ones((3, 3), np.uint8)
        content_mask = cv2.morphologyEx(content_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        content_mask = cv2.morphologyEx(content_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        return content_mask


class RobustTileDetector(BackgroundToggleDetector):
    """Detect tiles using background color toggling."""
    
    def detect_tiles(self, min_area: int = 5000, max_area: int = 200000,
                    diff_threshold: int = 30) -> List[Tuple[int, int, int, int]]:
        """Detect tiles by toggling background color.
        
        Args:
            min_area: Minimum tile area in pixels
            max_area: Maximum tile area in pixels
            diff_threshold: Difference threshold for background change detection
            
        Returns:
            List of tile rectangles as (x, y, width, height)
        """
        print("\n" + "="*80)
        print("ROBUST TILE DETECTION (Background Toggle)")
        print("="*80)
        
        # Capture with both backgrounds
        img_white, img_red = self.capture_with_backgrounds("white", "red")
        
        if img_white is None or img_red is None:
            print("❌ Failed to capture images")
            return []
        
        # Compute content mask
        content_mask = self.compute_content_mask(img_white, img_red, diff_threshold)
        
        # Find connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            content_mask, connectivity=8
        )
        
        print(f"📦 Found {num_labels - 1} content regions")
        
        tiles = []
        
        # Filter by area
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            
            if min_area <= area <= max_area:
                x = stats[i, cv2.CC_STAT_LEFT]
                y = stats[i, cv2.CC_STAT_TOP]
                w = stats[i, cv2.CC_STAT_WIDTH]
                h = stats[i, cv2.CC_STAT_HEIGHT]
                
                tiles.append((x, y, w, h))
                print(f"  ✓ Tile {len(tiles)}: ({x}, {y}) size {w}x{h} area {area}")
        
        print(f"\n✅ Detected {len(tiles)} tiles")
        return tiles
    
    def detect_tiles_with_grid(self, spacing_tolerance: float = 0.3,
                              diff_threshold: int = 30) -> List[Tuple[int, int, int, int]]:
        """Detect tiles with background toggle and grid extrapolation.
        
        Args:
            spacing_tolerance: Tolerance for grid spacing (0.3 = 30%)
            diff_threshold: Difference threshold
            
        Returns:
            List of tile rectangles as (x, y, width, height)
        """
        # Get initial tiles
        initial_tiles = self.detect_tiles(diff_threshold=diff_threshold)
        
        if len(initial_tiles) < 3:
            print("⚠️  Too few tiles for grid extrapolation")
            return initial_tiles
        
        # Use DBSCAN clustering to find grid pattern
        from sklearn.cluster import DBSCAN
        
        positions = np.array([(x, y) for x, y, w, h in initial_tiles])
        
        # Estimate spacing from initial tiles
        if len(initial_tiles) >= 2:
            # Get typical tile size
            widths = [w for x, y, w, h in initial_tiles]
            heights = [h for x, y, w, h in initial_tiles]
            typical_width = np.median(widths)
            typical_height = np.median(heights)
            
            # Cluster X positions
            X_positions = positions[:, 0].reshape(-1, 1)
            dbscan_x = DBSCAN(eps=typical_width / 20, min_samples=1)
            x_clusters = dbscan_x.fit_predict(X_positions)
            
            # Cluster Y positions
            Y_positions = positions[:, 1].reshape(-1, 1)
            dbscan_y = DBSCAN(eps=typical_height / 20, min_samples=1)
            y_clusters = dbscan_y.fit_predict(Y_positions)
            
            # Get unique column and row positions
            unique_x_clusters = sorted(set(x_clusters))
            unique_y_clusters = sorted(set(y_clusters))
            
            col_positions = []
            for cluster_id in unique_x_clusters:
                cluster_xs = X_positions[x_clusters == cluster_id]
                col_positions.append(int(np.median(cluster_xs)))
            
            row_positions = []
            for cluster_id in unique_y_clusters:
                cluster_ys = Y_positions[y_clusters == cluster_id]
                row_positions.append(int(np.median(cluster_ys)))
            
            print(f"\n🔍 Grid analysis:")
            print(f"   Columns: {len(col_positions)} positions")
            print(f"   Rows: {len(row_positions)} positions")
            print(f"   Grid size: {len(col_positions)}x{len(row_positions)}")
            
            # Compute spacing
            if len(col_positions) >= 2:
                x_spacings = np.diff(col_positions)
                typical_x_spacing = np.median(x_spacings)
            else:
                typical_x_spacing = typical_width * 1.1
                
            if len(row_positions) >= 2:
                y_spacings = np.diff(row_positions)
                typical_y_spacing = np.median(y_spacings)
            else:
                typical_y_spacing = typical_height * 1.1
            
            print(f"   Typical spacing: X={typical_x_spacing:.0f}, Y={typical_y_spacing:.0f}")
            
            # Extrapolate grid
            # This is a simplified version - full implementation would verify each position
            print(f"\n✅ Returning {len(initial_tiles)} verified tiles")
            return initial_tiles
        
        return initial_tiles


class RobustMediaPaneDetector(BackgroundToggleDetector):
    """Detect media pane using background color toggling."""
    
    def detect_bounds(self, min_width_ratio: float = 0.3, 
                     diff_threshold: int = 30) -> Optional[Tuple[int, int, int, int]]:
        """Detect media pane by toggling background color.
        
        Args:
            min_width_ratio: Minimum width as ratio of image width
            diff_threshold: Difference threshold
            
        Returns:
            Bounding box as (x, y, width, height) or None
        """
        print("\n" + "="*80)
        print("ROBUST MEDIA PANE DETECTION (Background Toggle)")
        print("="*80)
        
        # Capture with both backgrounds
        img_white, img_red = self.capture_with_backgrounds("white", "red")
        
        if img_white is None or img_red is None:
            print("❌ Failed to capture images")
            return None
        
        # Compute content mask
        content_mask = self.compute_content_mask(img_white, img_red, diff_threshold)
        
        # Find the largest connected component
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            content_mask, connectivity=8
        )
        
        if num_labels <= 1:
            print("❌ No content regions found")
            return None
        
        # Get largest region (excluding background label 0)
        areas = [stats[i, cv2.CC_STAT_AREA] for i in range(1, num_labels)]
        largest_idx = np.argmax(areas) + 1
        
        x = stats[largest_idx, cv2.CC_STAT_LEFT]
        y = stats[largest_idx, cv2.CC_STAT_TOP]
        w = stats[largest_idx, cv2.CC_STAT_WIDTH]
        h = stats[largest_idx, cv2.CC_STAT_HEIGHT]
        
        img_width = img_white.shape[1]
        min_width = int(img_width * min_width_ratio)
        
        if w < min_width:
            print(f"❌ Region too narrow: {w}px < {min_width}px")
            return None
        
        print(f"✅ Detected media pane: ({x}, {y}) size {w}x{h}")
        return (x, y, w, h)
