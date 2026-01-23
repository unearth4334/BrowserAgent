#!/usr/bin/env python3
"""
Detect image pane by finding the widest continuous region where content exceeds threshold.
The image pane should be the region with sustained high content density.
"""

import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt


class WidestRegionDetector:
    def __init__(self, image_path: str):
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        self.height, self.width = self.image.shape[:2]
        
        # Compute content mask
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.content_mask = (gray < 200).astype(np.uint8) * 255
        
        # Compute row and column sums
        self.row_sums = np.sum(self.content_mask > 0, axis=1)
        self.col_sums = np.sum(self.content_mask > 0, axis=0)
        
        print(f"📊 Content distribution:")
        print(f"   Row sums - Min: {self.row_sums.min()}, Max: {self.row_sums.max()}, Mean: {self.row_sums.mean():.1f}")
        print(f"   Col sums - Min: {self.col_sums.min()}, Max: {self.col_sums.max()}, Mean: {self.col_sums.mean():.1f}")
    
    def find_widest_continuous_region(self, profile: np.ndarray, threshold: float) -> tuple[int, int] | None:
        """
        Find the widest continuous region where profile > threshold.
        
        Returns:
            Tuple of (start, end) indices, or None if no region found
        """
        n = len(profile)
        
        # Find all positions above threshold
        above_threshold = profile > threshold
        
        if not np.any(above_threshold):
            return None
        
        # Find continuous regions
        regions = []
        in_region = False
        start = 0
        
        for i in range(n):
            if above_threshold[i]:
                if not in_region:
                    start = i
                    in_region = True
            else:
                if in_region:
                    regions.append((start, i - 1))
                    in_region = False
        
        # Don't forget the last region if it extends to the end
        if in_region:
            regions.append((start, n - 1))
        
        if not regions:
            return None
        
        # Find the widest region
        widest = max(regions, key=lambda r: r[1] - r[0])
        return widest
    
    def detect_bounds(self, row_threshold: float, col_threshold: float) -> tuple[int, int, int, int] | None:
        """
        Detect bounds by finding widest continuous regions in rows and columns.
        
        Args:
            row_threshold: Minimum content per row
            col_threshold: Minimum content per column
        """
        # Find widest vertical region (rows)
        row_region = self.find_widest_continuous_region(self.row_sums, row_threshold)
        if row_region is None:
            return None
        y_min, y_max = row_region
        
        # Find widest horizontal region (columns)
        col_region = self.find_widest_continuous_region(self.col_sums, col_threshold)
        if col_region is None:
            return None
        x_min, x_max = col_region
        
        return (x_min, y_min, x_max, y_max)
    
    def show_profiles(self, row_threshold: float, col_threshold: float, bounds: tuple[int, int, int, int] | None):
        """Show profiles with threshold lines and detected regions."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Row sums (vertical profile)
        ax1.plot(self.row_sums, range(self.height), 'b-', linewidth=1)
        ax1.axvline(row_threshold, color='r', linestyle='--', linewidth=2, label=f'Threshold={row_threshold:.0f}')
        if bounds:
            _, y_min, _, y_max = bounds
            ax1.axhline(y_min, color='g', linestyle='-', linewidth=2, label=f'Y: {y_min}-{y_max} (width={y_max-y_min})')
            ax1.axhline(y_max, color='g', linestyle='-', linewidth=2)
            # Highlight the detected region
            ax1.axhspan(y_min, y_max, alpha=0.2, color='green', label='Detected region')
        ax1.set_xlabel('Content Pixels per Row')
        ax1.set_ylabel('Y Position')
        ax1.set_title('Vertical Profile - Finding Widest Region Above Threshold')
        ax1.invert_yaxis()
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Column sums (horizontal profile)
        ax2.plot(range(self.width), self.col_sums, 'b-', linewidth=1)
        ax2.axhline(col_threshold, color='r', linestyle='--', linewidth=2, label=f'Threshold={col_threshold:.0f}')
        if bounds:
            x_min, _, x_max, _ = bounds
            ax2.axvline(x_min, color='g', linestyle='-', linewidth=2, label=f'X: {x_min}-{x_max} (width={x_max-x_min})')
            ax2.axvline(x_max, color='g', linestyle='-', linewidth=2)
            # Highlight the detected region
            ax2.axvspan(x_min, x_max, alpha=0.2, color='green', label='Detected region')
        ax2.set_xlabel('X Position')
        ax2.set_ylabel('Content Pixels per Column')
        ax2.set_title('Horizontal Profile - Finding Widest Region Above Threshold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        plt.show()
    
    def show_result(self, bounds: tuple[int, int, int, int] | None):
        """Display the detection result."""
        result_img = self.image.copy()
        
        if bounds:
            x_min, y_min, x_max, y_max = bounds
            cv2.rectangle(result_img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 3)
            
            # Draw center crosshairs
            center_x = (x_min + x_max) // 2
            center_y = (y_min + y_max) // 2
            cv2.line(result_img, (center_x - 20, center_y), (center_x + 20, center_y), (0, 255, 0), 2)
            cv2.line(result_img, (center_x, center_y - 20), (center_x, center_y + 20), (0, 255, 0), 2)
            
            # Add text
            width = x_max - x_min
            height = y_max - y_min
            area_pct = (width * height) / (self.width * self.height) * 100
            text = f"({x_min},{y_min}) {width}x{height}, area={area_pct:.1f}%"
            cv2.putText(result_img, text, (x_min, y_min - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        result_rgb = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
        
        root = tk.Tk()
        root.title("Widest Continuous Region Detection")
        
        display_img = Image.fromarray(result_rgb)
        scale = min(1.0, 1400 / self.width, 900 / self.height)
        new_size = (int(self.width * scale), int(self.height * scale))
        display_img = display_img.resize(new_size, Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(display_img)
        label = tk.Label(root, image=photo)
        label.image = photo
        label.pack()
        
        root.mainloop()
    
    def analyze_regions(self, row_threshold: float, col_threshold: float):
        """Show all continuous regions found."""
        print(f"\n📊 Finding all continuous regions above thresholds...")
        print(f"   Row threshold: {row_threshold:.0f}")
        print(f"   Col threshold: {col_threshold:.0f}")
        
        # Find all row regions
        row_regions = []
        above = self.row_sums > row_threshold
        in_region = False
        start = 0
        
        for i in range(len(self.row_sums)):
            if above[i]:
                if not in_region:
                    start = i
                    in_region = True
            else:
                if in_region:
                    row_regions.append((start, i - 1))
                    in_region = False
        if in_region:
            row_regions.append((start, len(self.row_sums) - 1))
        
        print(f"\n   Vertical regions found: {len(row_regions)}")
        for i, (start, end) in enumerate(row_regions, 1):
            width = end - start + 1
            print(f"     Region {i}: rows {start}-{end} (height={width})")
        
        # Find all column regions
        col_regions = []
        above = self.col_sums > col_threshold
        in_region = False
        start = 0
        
        for i in range(len(self.col_sums)):
            if above[i]:
                if not in_region:
                    start = i
                    in_region = True
            else:
                if in_region:
                    col_regions.append((start, i - 1))
                    in_region = False
        if in_region:
            col_regions.append((start, len(self.col_sums) - 1))
        
        print(f"\n   Horizontal regions found: {len(col_regions)}")
        for i, (start, end) in enumerate(col_regions, 1):
            width = end - start + 1
            print(f"     Region {i}: columns {start}-{end} (width={width})")


def tune_detection(image_path: str):
    """Interactive tuning loop."""
    detector = WidestRegionDetector(image_path)
    
    # Start with threshold of 600 as user suggested
    row_threshold = 600
    col_threshold = 600
    iteration = 1
    
    print("\n" + "="*80)
    print("Finding widest continuous region with content above threshold...")
    print("="*80)
    
    while True:
        print(f"\n{'='*80}")
        print(f"ITERATION {iteration}")
        print(f"{'='*80}")
        print(f"Row threshold: {row_threshold:.0f}")
        print(f"Column threshold: {col_threshold:.0f}")
        
        # Analyze all regions
        detector.analyze_regions(row_threshold, col_threshold)
        
        # Detect bounds
        print("\n🔍 Detecting widest regions...")
        bounds = detector.detect_bounds(row_threshold, col_threshold)
        
        if bounds:
            x_min, y_min, x_max, y_max = bounds
            width = x_max - x_min
            height = y_max - y_min
            area_pct = (width * height) / (detector.width * detector.height) * 100
            print(f"✅ Detected: ({x_min},{y_min}) {width}x{height}, area={area_pct:.1f}%")
        else:
            print("⚠️  No bounds detected")
        
        # Show profiles
        print("\n📊 Showing profiles (close plot to continue)...")
        detector.show_profiles(row_threshold, col_threshold, bounds)
        
        # Show visual result
        print("📺 Showing detection result (close window to continue)...")
        detector.show_result(bounds)
        
        # Ask for feedback
        print("\n" + "="*80)
        if bounds:
            print("Does this detection look correct? (y/n): ", end="", flush=True)
            response = input().strip().lower()
            if response == 'y':
                print(f"✅ Final detection: ({x_min},{y_min}) {width}x{height}")
                break
            
            print("\nWhat adjustment is needed?")
            print("  [h] Raise thresholds (tighter bounds)")
            print("  [l] Lower thresholds (looser bounds)")
            print("  [r] Adjust row threshold only")
            print("  [c] Adjust column threshold only")
            print("  [q] Quit")
            print("Choice: ", end="", flush=True)
            choice = input().strip().lower()
            
            if choice == 'q':
                print("⚠️  Tuning stopped by user")
                break
            elif choice == 'h':
                row_threshold = int(row_threshold * 1.2)
                col_threshold = int(col_threshold * 1.2)
                print(f"  → Raised to row={row_threshold}, col={col_threshold}")
            elif choice == 'l':
                row_threshold = int(row_threshold * 0.8)
                col_threshold = int(col_threshold * 0.8)
                print(f"  → Lowered to row={row_threshold}, col={col_threshold}")
            elif choice == 'r':
                print(f"Current row threshold: {row_threshold}")
                print("Enter new value: ", end="", flush=True)
                try:
                    row_threshold = float(input().strip())
                    print(f"  → Set to {row_threshold:.0f}")
                except:
                    print("  ⚠️  Invalid input")
            elif choice == 'c':
                print(f"Current column threshold: {col_threshold}")
                print("Enter new value: ", end="", flush=True)
                try:
                    col_threshold = float(input().strip())
                    print(f"  → Set to {col_threshold:.0f}")
                except:
                    print("  ⚠️  Invalid input")
        else:
            print("No detection. Lower thresholds? (y/n): ", end="", flush=True)
            response = input().strip().lower()
            if response != 'y':
                print("⚠️  Tuning stopped by user")
                break
            row_threshold = int(row_threshold * 0.7)
            col_threshold = int(col_threshold * 0.7)
            print(f"  → Lowered to row={row_threshold}, col={col_threshold}")
        
        iteration += 1
        
        if iteration > 20:
            print("⚠️  Maximum iterations reached")
            break


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = "grok_test_screenshots/case_image_only.png"
    
    print(f"🖼️  Loading: {image_path}")
    tune_detection(image_path)
