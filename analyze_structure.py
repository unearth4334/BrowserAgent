#!/usr/bin/env python3
"""
Analyze the actual image to understand what we're looking for.
Show different visualizations to help understand the structure.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt


def analyze_image(image_path: str):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Failed to load: {image_path}")
    
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Create visualizations
    fig = plt.figure(figsize=(16, 12))
    
    # 1. Original image
    ax1 = plt.subplot(3, 3, 1)
    ax1.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    ax1.set_title('Original Image')
    ax1.axis('off')
    
    # 2. Brightness
    ax2 = plt.subplot(3, 3, 2)
    ax2.imshow(gray, cmap='gray')
    ax2.set_title('Brightness')
    ax2.axis('off')
    
    # 3. Background mask (bright pixels ~252)
    bg_mask = (gray > 240).astype(np.uint8) * 255
    ax3 = plt.subplot(3, 3, 3)
    ax3.imshow(bg_mask, cmap='gray')
    ax3.set_title(f'Background Mask (>{240})')
    ax3.axis('off')
    
    # 4. Content mask (dark pixels ~44)
    content_mask = (gray < 200).astype(np.uint8) * 255
    ax4 = plt.subplot(3, 3, 4)
    ax4.imshow(content_mask, cmap='gray')
    ax4.set_title(f'Content Mask (<{200})')
    ax4.axis('off')
    
    # 5. Row-wise content density
    row_sums = np.sum(content_mask > 0, axis=1)
    ax5 = plt.subplot(3, 3, 5)
    ax5.barh(range(height), row_sums, height=1)
    ax5.set_xlabel('Content Pixels per Row')
    ax5.set_ylabel('Y Position')
    ax5.set_title('Vertical Content Density')
    ax5.invert_yaxis()
    ax5.grid(True, alpha=0.3)
    
    # 6. Column-wise content density
    col_sums = np.sum(content_mask > 0, axis=0)
    ax6 = plt.subplot(3, 3, 6)
    ax6.bar(range(width), col_sums, width=1)
    ax6.set_xlabel('X Position')
    ax6.set_ylabel('Content Pixels per Column')
    ax6.set_title('Horizontal Content Density')
    ax6.grid(True, alpha=0.3)
    
    # 7. Standard deviation of brightness by row (texture indicator)
    row_std = np.std(gray, axis=1)
    ax7 = plt.subplot(3, 3, 7)
    ax7.barh(range(height), row_std, height=1)
    ax7.set_xlabel('Std Dev of Brightness')
    ax7.set_ylabel('Y Position')
    ax7.set_title('Vertical Texture (Std Dev)')
    ax7.invert_yaxis()
    ax7.grid(True, alpha=0.3)
    
    # 8. Standard deviation of brightness by column
    col_std = np.std(gray, axis=0)
    ax8 = plt.subplot(3, 3, 8)
    ax8.bar(range(width), col_std, width=1)
    ax8.set_xlabel('X Position')
    ax8.set_ylabel('Std Dev of Brightness')
    ax8.set_title('Horizontal Texture (Std Dev)')
    ax8.grid(True, alpha=0.3)
    
    # 9. Gradient magnitude
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_mag = np.sqrt(sobelx**2 + sobely**2)
    ax9 = plt.subplot(3, 3, 9)
    ax9.imshow(gradient_mag, cmap='hot')
    ax9.set_title('Gradient Magnitude')
    ax9.axis('off')
    
    plt.tight_layout()
    plt.show()
    
    # Print statistics
    print("\n" + "="*80)
    print("IMAGE ANALYSIS")
    print("="*80)
    print(f"\nDimensions: {width} x {height}")
    print(f"\nBrightness statistics:")
    print(f"  Min: {gray.min()}, Max: {gray.max()}, Mean: {gray.mean():.1f}, Std: {gray.std():.1f}")
    
    print(f"\nContent pixels (<200 brightness): {np.sum(content_mask > 0)} ({np.sum(content_mask > 0) / gray.size * 100:.1f}%)")
    print(f"Background pixels (>240 brightness): {np.sum(bg_mask > 0)} ({np.sum(bg_mask > 0) / gray.size * 100:.1f}%)")
    
    print(f"\nRow content sums:")
    print(f"  Min: {row_sums.min()}, Max: {row_sums.max()}, Mean: {row_sums.mean():.1f}")
    print(f"  25th percentile: {np.percentile(row_sums, 25):.1f}")
    print(f"  50th percentile: {np.percentile(row_sums, 50):.1f}")
    print(f"  75th percentile: {np.percentile(row_sums, 75):.1f}")
    
    print(f"\nColumn content sums:")
    print(f"  Min: {col_sums.min()}, Max: {col_sums.max()}, Mean: {col_sums.mean():.1f}")
    print(f"  25th percentile: {np.percentile(col_sums, 25):.1f}")
    print(f"  50th percentile: {np.percentile(col_sums, 50):.1f}")
    print(f"  75th percentile: {np.percentile(col_sums, 75):.1f}")
    
    print(f"\nRow texture (std dev):")
    print(f"  Min: {row_std.min():.1f}, Max: {row_std.max():.1f}, Mean: {row_std.mean():.1f}")
    
    print(f"\nColumn texture (std dev):")
    print(f"  Min: {col_std.min():.1f}, Max: {col_std.max():.1f}, Mean: {col_std.mean():.1f}")
    
    # Find rows with low content (potential UI regions)
    print(f"\nRows with minimal content (<600 pixels):")
    low_content_rows = np.where(row_sums < 600)[0]
    if len(low_content_rows) > 0:
        print(f"  Count: {len(low_content_rows)}")
        print(f"  First few: {low_content_rows[:10]}")
        print(f"  Last few: {low_content_rows[-10:]}")
    else:
        print("  None found")
    
    print(f"\nColumns with minimal content (<400 pixels):")
    low_content_cols = np.where(col_sums < 400)[0]
    if len(low_content_cols) > 0:
        print(f"  Count: {len(low_content_cols)}")
        print(f"  First few: {low_content_cols[:10]}")
        print(f"  Last few: {low_content_cols[-10:]}")
    else:
        print("  None found")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = "grok_test_screenshots/case_image_only.png"
    
    print(f"🖼️  Analyzing: {image_path}")
    analyze_image(image_path)
