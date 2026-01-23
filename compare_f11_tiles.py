#!/usr/bin/env python3
"""
Compare tile detection between normal and fullscreen screenshots.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import cv2
import numpy as np
import tkinter as tk
from detect_grok_tiles import TileDetector


def detect_and_report(image_path: str, label: str):
    """Detect tiles and report results."""
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")
    print(f"Image: {image_path}")
    
    try:
        detector = TileDetector(image_path)
        tiles = detector.detect_tiles()
        
        if tiles:
            print(f"\n✅ Found {len(tiles)} tiles")
            print("\nTile coordinates:")
            for i, (x, y, w, h) in enumerate(tiles, 1):
                center_x = x + w // 2
                center_y = y + h // 2
                area_pct = (w * h) / (detector.image.shape[0] * detector.image.shape[1]) * 100
                print(f"  Tile {i:2d}: ({x:4d},{y:4d}) {w:3d}x{h:3d} - center: ({center_x:4d},{center_y:4d}) - area: {area_pct:4.1f}%")
        else:
            print("\n⚠️  No tiles detected")
            
        return tiles
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def compare_tiles(tiles1, tiles2, label1: str, label2: str):
    """Compare two sets of tiles."""
    print(f"\n{'='*80}")
    print("COMPARISON")
    print(f"{'='*80}")
    
    if tiles1 is None or tiles2 is None:
        print("Cannot compare - detection failed for one or both images")
        return
    
    print(f"\n{label1}: {len(tiles1)} tiles")
    print(f"{label2}: {len(tiles2)} tiles")
    
    if len(tiles1) == len(tiles2):
        print(f"\n✅ Same number of tiles detected")
        
        # Check if positions are similar (allowing for small differences)
        tolerance = 10
        matching = 0
        
        for i, (t1, t2) in enumerate(zip(tiles1, tiles2), 1):
            x1, y1, w1, h1 = t1
            x2, y2, w2, h2 = t2
            
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)
            dw = abs(w1 - w2)
            dh = abs(h1 - h2)
            
            if dx <= tolerance and dy <= tolerance and dw <= tolerance and dh <= tolerance:
                matching += 1
                print(f"  Tile {i}: ✓ Match (Δx={dx}, Δy={dy}, Δw={dw}, Δh={dh})")
            else:
                print(f"  Tile {i}: ✗ Different (Δx={dx}, Δy={dy}, Δw={dw}, Δh={dh})")
        
        print(f"\n{matching}/{len(tiles1)} tiles match within {tolerance}px tolerance")
    else:
        print(f"\n⚠️  Different number of tiles detected")


def main():
    """Compare tile detection in before and after fullscreen screenshots."""
    before = "grok_test_screenshots/f11_test_before.png"
    after = "grok_test_screenshots/f11_test_after_f11.png"
    
    tiles_before = detect_and_report(before, "BEFORE FULLSCREEN")
    tiles_after = detect_and_report(after, "AFTER FULLSCREEN")
    
    compare_tiles(tiles_before, tiles_after, "Before", "After")
    
    # Show visual comparison
    show_comparison(before, after, tiles_before, tiles_after)


def show_comparison(image1_path: str, image2_path: str, tiles1, tiles2):
    """Show side-by-side comparison of tile detection in a GUI window."""
    # Load images
    img1 = cv2.imread(image1_path)
    img2 = cv2.imread(image2_path)
    
    if img1 is None or img2 is None:
        print("Failed to load images for display")
        return
    
    # Draw tiles on images
    if tiles1:
        for i, (x, y, w, h) in enumerate(tiles1, 1):
            cv2.rectangle(img1, (x, y), (x+w, y+h), (0, 255, 0), 3)
            cv2.putText(img1, str(i), (x+10, y+30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    if tiles2:
        for i, (x, y, w, h) in enumerate(tiles2, 1):
            cv2.rectangle(img2, (x, y), (x+w, y+h), (0, 255, 0), 3)
            cv2.putText(img2, str(i), (x+10, y+30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Add labels
    label1 = f"BEFORE: {len(tiles1) if tiles1 else 0} tiles"
    label2 = f"AFTER FULLSCREEN: {len(tiles2) if tiles2 else 0} tiles"
    
    cv2.putText(img1, label1, (20, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 0), 3)
    cv2.putText(img2, label2, (20, 50), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 0), 3)
    
    # Resize for display (fit on screen)
    max_height = 700
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    
    if h1 > max_height or h2 > max_height:
        scale1 = max_height / h1
        scale2 = max_height / h2
        scale = min(scale1, scale2)
        
        new_w1 = int(w1 * scale)
        new_h1 = int(h1 * scale)
        new_w2 = int(w2 * scale)
        new_h2 = int(h2 * scale)
        
        img1 = cv2.resize(img1, (new_w1, new_h1))
        img2 = cv2.resize(img2, (new_w2, new_h2))
    
    # Combine side by side
    # Make them same height
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    max_h = max(h1, h2)
    
    if h1 < max_h:
        pad = max_h - h1
        img1 = cv2.copyMakeBorder(img1, 0, pad, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    if h2 < max_h:
        pad = max_h - h2
        img2 = cv2.copyMakeBorder(img2, 0, pad, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    
    combined = np.hstack([img1, img2])
    
    # Display using tkinter
    root = tk.Tk()
    root.title("Tile Detection Comparison: Before vs After Fullscreen")
    
    # Convert BGR to RGB
    combined_rgb = cv2.cvtColor(combined, cv2.COLOR_BGR2RGB)
    
    # Convert to PhotoImage
    from PIL import Image, ImageTk
    pil_img = Image.fromarray(combined_rgb)
    photo = ImageTk.PhotoImage(pil_img)
    
    # Create label
    label = tk.Label(root, image=photo)
    label.image = photo  # Keep reference
    label.pack()
    
    # Add instruction
    instruction = tk.Label(root, text="Close window to exit", 
                          font=("Arial", 12), pady=10)
    instruction.pack()
    
    root.mainloop()


if __name__ == "__main__":
    main()
