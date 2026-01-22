# Grok Image/Video Downloader via noVNC

This branch (`grokbot`) adds vision-based browser automation capabilities to interact with Grok's imagine/favorites tileview through a noVNC container, bypassing CAPTCHA restrictions.

## Problem Statement

Direct Playwright automation of Grok fails due to "Are you human?" tests. To work around this, we:
1. Run Grok in a Docker container with noVNC (web-based VNC viewer)
2. Manually authenticate once
3. Use Playwright to control the local browser viewing the noVNC session
4. Use screenshot-based vision to identify and click on tiles

## Architecture

### New Actions
- **`Screenshot`**: Capture screenshots of the page or specific elements
  - `path`: Where to save the screenshot
  - `selector`: Optional selector to screenshot only a specific element
  - `full_page`: Whether to capture the full scrollable page

- **`ClickAtCoordinates`**: Click at specific x,y coordinates
  - `x`, `y`: Pixel coordinates relative to viewport
  - `button`: "left", "right", or "middle"

### New Components

#### Task Specs (`task_spec_grok.py`)
- **`GrokDownloadTaskSpec`**: Main task for automated downloading
  - Configurable download directory, max downloads, target type (image/video/both)
  - Integrates with noVNC container at `http://localhost:6080/vnc.html`
  
- **`GrokNavigateTaskSpec`**: Helper task for manual setup
  - Opens noVNC and waits for user to navigate to target Grok page

#### Policy (`policy_grok.py`)
- **`GrokVisionPolicy`**: Decision-making logic for vision-based automation
  - Takes screenshots of the noVNC canvas
  - Placeholder for vision analysis (LLM or CV-based)
  - Generates coordinate-based clicks based on detected elements
  - Tracks download progress

#### Enhanced Observations
- **`PageObservation`** now includes:
  - `screenshot_path`: Path to captured screenshot
  - `screenshot_data`: Raw screenshot bytes (optional)

## Usage

### 1. Set up noVNC Container

First, run Grok in a Docker container with noVNC:

```bash
# Example - adjust based on your setup
docker run -p 6080:80 -p 5900:5900 \
  -v /dev/shm:/dev/shm \
  dorowu/ubuntu-desktop-lxde-vnc
```

Then navigate to `http://localhost:6080/vnc.html` and:
1. Log in to Grok
2. Navigate to favorites or imagine page

### 2. Setup Command (Optional)

Use the setup command to verify your noVNC connection:

```bash
browser-agent grok-setup --target-page favorites
```

This will:
- Open your local browser to the noVNC viewer
- Wait for you to confirm navigation is complete
- Verify the connection works

### 3. Run Download Task

```bash
browser-agent grok-download \
  --novnc-url http://localhost:6080/vnc.html \
  --download-dir ./my_grok_images \
  --max-downloads 10 \
  --screenshot-dir ./screenshots
```

**Options:**
- `--novnc-url`: URL of your noVNC viewer (default: `http://localhost:6080/vnc.html`)
- `--download-dir`: Where to save downloaded images/videos (default: `./grok_downloads`)
- `--max-downloads`: Limit number of downloads, 0 = unlimited (default: 0)
- `--target-type`: `image`, `video`, or `both` (default: `both`)
- `--screenshot-dir`: Where to save screenshots for analysis (default: `./grok_screenshots`)
- `--headless/--no-headless`: Run in headless mode (default: visible)
- `--browser-exe`: Path to Brave/Chromium if not using default

## Current Status & Roadmap

### ✅ Implemented
- [x] Screenshot action with element/full-page support
- [x] Coordinate-based clicking action
- [x] Enhanced observations with screenshot data
- [x] Grok task specifications
- [x] Policy framework for vision-based automation
- [x] CLI commands for grok-setup and grok-download
- [x] Integration with existing browser-agent infrastructure

### 🚧 In Progress
- [ ] **Vision Analysis**: Core logic to analyze screenshots and identify:
  - Tile positions and boundaries
  - Download buttons
  - Scroll indicators
  - Navigation elements

### 🎯 Planned
- [ ] **LLM Vision Integration**: Use GPT-4V, Claude Vision, or similar to:
  - Identify clickable tiles in screenshots
  - Detect UI state (loading, errors, etc.)
  - Generate precise click coordinates
  
- [ ] **Computer Vision Alternative**: OpenCV-based approach for:
  - Template matching for buttons/icons
  - Edge detection for tile boundaries
  - Color-based element identification

- [ ] **Download Management**:
  - Track downloaded items (avoid duplicates)
  - Monitor download progress
  - Handle failed downloads
  - Organize by date/category

- [ ] **Pagination/Scrolling**:
  - Detect when scrolling is needed
  - Scroll the VNC canvas viewport
  - Handle lazy-loaded content

- [ ] **Configuration Files**:
  - Store known element coordinates
  - Define tile detection parameters
  - Customize retry/timeout behavior

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=browser_agent --cov-report=html

# Test specific Grok components (when tests are added)
pytest tests/test_grok*.py
```

### Adding Vision Analysis

The `GrokVisionPolicy.analyze_screenshot()` method is where vision logic should be implemented:

```python
def analyze_screenshot(self, screenshot_path: str) -> dict[str, Any]:
    """Analyze a screenshot to identify interactive elements."""
    
    # Option 1: LLM Vision API
    # response = openai.ChatCompletion.create(
    #     model="gpt-4-vision-preview",
    #     messages=[{
    #         "role": "user",
    #         "content": [
    #             {"type": "text", "text": "Identify all clickable tiles in this Grok tileview"},
    #             {"type": "image_url", "image_url": {"url": f"file://{screenshot_path}"}}
    #         ]
    #     }]
    # )
    
    # Option 2: OpenCV
    # img = cv2.imread(screenshot_path)
    # tiles = detect_tiles(img)  # Your CV logic here
    
    return {
        "tiles": [...],  # List of {x, y, width, height}
        "buttons": [...],  # List of {x, y, label}
        "scroll_needed": False,
    }
```

### Testing with Mock Vision

For testing without implementing full vision:

```python
# Create a test policy with hardcoded coordinates
class TestGrokPolicy(GrokVisionPolicy):
    def analyze_screenshot(self, screenshot_path: str):
        return {
            "tiles": [
                {"x": 100, "y": 200, "width": 150, "height": 150},
                {"x": 300, "y": 200, "width": 150, "height": 150},
            ],
            "buttons": [],
            "scroll_needed": False,
        }
```

## Technical Notes

### Why Two Browsers?
- **Outer browser** (controlled by Playwright): Your local Chrome/Brave
- **Inner browser** (running in VNC): The containerized browser accessing Grok
- We control the outer browser to interact with the noVNC canvas showing the inner browser

### Coordinate Mapping
Coordinates from vision analysis must be relative to the noVNC canvas element, not the full page. Future improvements should:
1. Identify the canvas element bounds
2. Map detected coordinates to canvas-relative positions
3. Account for any scaling/zoom in the VNC viewer

### Screenshot Strategy
Current approach takes full-page screenshots. For production:
1. Target only the VNC canvas element with `selector` parameter
2. Use `full_page=False` to capture viewport only
3. Consider screenshot frequency to balance performance and accuracy

## Contributing

When adding features:
1. Follow existing patterns (dataclasses for actions, protocols for abstractions)
2. Add tests with mock browsers first
3. Use the logging system: `logger = get_logger(__name__)`
4. Update this README with new capabilities

## Related Files

- [actions.py](src/browser_agent/browser/actions.py) - Screenshot and ClickAtCoordinates actions
- [observation.py](src/browser_agent/browser/observation.py) - Extended with screenshot data
- [playwright_driver.py](src/browser_agent/browser/playwright_driver.py) - Handles new actions
- [task_spec_grok.py](src/browser_agent/agent/task_spec_grok.py) - Task specifications
- [policy_grok.py](src/browser_agent/agent/policy_grok.py) - Vision-based policy
- [cli.py](src/browser_agent/cli.py) - CLI commands
