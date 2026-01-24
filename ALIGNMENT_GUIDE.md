# HTML Detection Alignment Guide

## Overview

This guide explains how to align HTML-based tile detection with visual detection to ensure accurate positioning.

## The Problem

HTML provides tile positions relative to the page content (e.g., `left: 0px, top: 0px`), but we need screen coordinates to click on tiles. A **viewport offset** converts HTML coordinates to screen coordinates:

```
screen_x = html_left + x_offset
screen_y = html_top + y_offset
```

The challenge is finding the correct viewport offset, which depends on:
- Sidebar width
- Top navigation bar height
- Browser chrome (address bar, tabs, etc.)
- Window position

## The Solution: Visual Calibration

Use visual tile detection (which finds tiles based on pixels) to calibrate the HTML offset:

1. **Visual Detection**: Finds tiles at actual screen positions (ground truth)
2. **HTML Parsing**: Extracts tile positions from page HTML
3. **Offset Calculation**: Compares both to compute the viewport offset
4. **Alignment**: Uses calibrated offset for accurate HTML-based detection

## Tools

### `align_html_detection.py`

Calibrates viewport offset by comparing visual and HTML detection:

```bash
# Run calibration
python align_html_detection.py

# Save without display
python align_html_detection.py --no-show
```

**Output**:
- `aligned_detection.png` - Visualization showing both detections
  - Green = Visual detection (ground truth)
  - Blue = HTML detection with calibrated offset
- Console output with calibrated offset values

### `visualize_html_detection.py`

Visualizes HTML detection with calibrated offset:

```bash
# Auto-detect offset (uses calibrated default)
python visualize_html_detection.py --no-show

# Override with specific offset
python visualize_html_detection.py --x-offset 348 --y-offset -120
```

### `detect_tiles_from_html.py`

Main detection module with calibrated default offset:

```python
from detect_tiles_from_html import detect_tiles_from_html

# Uses calibrated default (348, -120)
rectangles, tiles = detect_tiles_from_html()

# Override offset if needed
rectangles, tiles = detect_tiles_from_html(viewport_offset=(350, -115))
```

## Current Calibrated Values

**Default viewport offset: (348, -120)**

- X offset: 348px (sidebar + content margin)
- Y offset: -120px (negative because HTML coords start below screen top)

This was calibrated using the alignment script on 2026-01-23.

## When to Recalibrate

Re-run alignment if:
- Window layout changes (sidebar toggled, resized, etc.)
- Tiles appear misaligned in visualizations
- Click coordinates miss tiles
- Browser or application UI updates

## Workflow

### Initial Setup (One-Time)
```bash
# Run alignment to calibrate offset
python align_html_detection.py

# Check aligned_detection.png to verify alignment
# Green and blue rectangles should overlap perfectly
```

### Regular Usage
```bash
# Just use the detection - it uses calibrated defaults
python visualize_html_detection.py
```

Or in code:
```python
from detect_tiles_from_html import detect_tiles_from_html

# Automatically uses calibrated offset
rectangles, tiles = detect_tiles_from_html()
```

## Verification

To verify alignment quality:

1. Run `align_html_detection.py`
2. Check console output:
   ```
   Average alignment error: X pixels
   Maximum alignment error: Y pixels
   ```
3. View `aligned_detection.png`:
   - Green (visual) and blue (HTML) should overlap
   - Small gaps are acceptable (< 50px average)
   - Large gaps indicate calibration issues

## Troubleshooting

### "Visual detection failed - no tiles found"
- Ensure tiles are visible on screen
- Try different visual detection methods (`grid`, `edges`, `adaptive`)
- Check that screenshot was captured correctly

### "Tile count mismatch"
- Normal if some tiles are scrolled out of view
- Visual detection only finds visible tiles
- HTML parsing finds all tiles (even off-screen)
- Alignment still works using visible tiles

### Tiles still misaligned after calibration
- Window may have moved or resized
- Re-run `align_html_detection.py`
- Check browser zoom level (should be 100%)
- Verify page hasn't scrolled

## Technical Details

### Alignment Algorithm

```python
def calculate_viewport_offset(visual_rects, html_tiles):
    """
    1. Sort both lists by position (left, top)
    2. Match corresponding tiles (first N tiles)
    3. Calculate offset for each match:
       offset_x = visual_x - html_x
       offset_y = visual_y - html_y
    4. Return median offset (robust to outliers)
    """
```

### Offset Storage

The calibrated offset is stored as the default return value in:
- `detect_tiles_from_html.py::get_viewport_offset()` 
- `visualize_html_detection.py::visualize_html_detection()` 

To update, edit these functions or pass explicit offset values.

## Files

- `align_html_detection.py` - Calibration tool (green=visual, blue=HTML)
- `visualize_html_detection.py` - HTML detection visualizer (green=image, orange=video)
- `detect_tiles_from_html.py` - Core detection module
- `aligned_detection.png` - Calibration output
- `html_detection_overlay.png` - Detection output

## See Also

- `HTML_DETECTION_GUIDE.md` - General HTML detection documentation
- `detect_grok_tiles.py` - Visual tile detection methods
- `grok_test_app.py` - Interactive testing application
