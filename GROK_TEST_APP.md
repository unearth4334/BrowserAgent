# Grok Test App

Interactive CLI application for testing Grok browser automation features.

## Features

### 1. **API Command Menu**
Control the Chrome browser running inside the **noVNC container** via REST API:
- **Navigate to page**: Focus address bar (Ctrl+L), type URL, press Enter
- **Click element**: Execute JavaScript to click by selector
- **Type text**: Send text input to the container browser
- **Press key**: Send key combinations (Return, Escape, F11, etc.)
- **Wait**: Simple sleep delay
- **Get page title**: Retrieve current page title via JavaScript
- **Go back**: Browser back navigation (Alt+Left macro)
- **Reload page**: Refresh current page (Ctrl+R macro)
- **Change background color**: Modify page background via Chrome DevTools Protocol

**Important**: All API commands control the **noVNC container browser** at `http://localhost:6080`, not the local Playwright browser. The local browser is only used to view noVNC and capture screenshots for tile/media pane detection.

### 2. **Detect Tiles**
- Captures screenshot of current page
- Detects all Grok image tiles using computer vision
- Displays detected tiles with numbered labels
- Shows tile coordinates, dimensions, and area percentages
- Uses grid extrapolation to find missing tiles in 5-column layout

### 3. **Click Tile**
- Click on any detected tile by entering its number
- Requires running "Detect Tiles" first
- Centers click on the tile for reliable interaction

### 4. **Detect Media Pane**
- Captures screenshot of current page
- Detects the enlarged media/image pane
- Uses widest continuous region algorithm
- Displays detected pane with red boundary
- Shows pane coordinates and area percentage

### 5. **Capture Screenshot**
- Take a screenshot at any time
- Specify custom filename
- Saves to `grok_test_screenshots/` directory

### 6. **Open Grok**
- Quick navigation to Grok (https://grok.x.com)
- Can specify custom URL

## Usage

```bash
python grok_test_app.py
```

The app will:
1. Launch a browser (Chromium) with viewport size 2496x1404
2. Navigate to noVNC (http://localhost:6080/vnc.html?autoconnect=true)
3. Display the main menu

## Menu Navigation

```
GROK TEST APP - MAIN MENU
================================================================================
  1. API Command
  2. Detect Tiles
  3. Click Tile
  4. Detect Media Pane
  5. Capture Screenshot
  6. Open Grok (navigate to Grok)
  0. Exit
================================================================================
```

### Example Workflow

1. **Start the app**: `python grok_test_app.py`
2. **Navigate to Grok**: Select option 6
3. **Detect tiles**: Select option 2
   - View detected tiles in popup window
   - Press any key to close
4. **Click a tile**: Select option 3
   - Enter tile number (1-9 typically)
   - Tile will be clicked
5. **Detect media pane**: Select option 4
   - View detected pane in popup window
6. **Use API commands**: Select option 1
   - Navigate, type, click, etc.

## Requirements

- Python 3.11+
- Playwright
- OpenCV (cv2)
- NumPy
- scikit-learn (for DBSCAN clustering in tile detection)

## Detection Algorithms

### Tile Detection
- Uses connected components to find tile regions
- Adaptive thresholds based on statistical analysis
- DBSCAN clustering to identify dominant grid pattern
- Grid extrapolation to find missing tiles
- Edge detection and content density verification
- Overlap checking to prevent false positives

### Media Pane Detection
- Analyzes row and column content density profiles
- Finds widest continuous regions above threshold
- Adapts to different screen layouts
- Robust to scrollbars and UI elements

## Output Files

All screenshots and detection results are saved to:
```
grok_test_screenshots/
├── tiles_detection.png       # Raw screenshot
├── tiles_detected.png         # Annotated with tile numbers
├── media_pane_detection.png   # Raw screenshot
└── media_pane_detected.png    # Annotated with pane boundary
```

## Tips

- **noVNC requirement**: The app expects noVNC to be running on localhost:6080
- **Window focus**: Detection works on the current browser page
- **Image popups**: Press any key to close detection result windows
- **Tile persistence**: Detected tiles remain available until you run detection again
- **Error handling**: The app will show errors if detection fails or elements aren't found

## Keyboard Shortcuts in Menus

- Enter number + Enter to select option
- `0` to go back/exit
- Ctrl+C to force quit (any time)
