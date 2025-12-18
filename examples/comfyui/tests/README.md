# ComfyUI Test Fixtures & Examples

This directory contains test fixtures, utilities, and example scripts for testing ComfyUI integration.

## Test Fixtures

### `mock_browser.py`
Mock implementation of `BrowserClient` for isolated unit testing. Simulates:
- JavaScript execution (`eval_js`)
- localStorage operations
- Workflow loading
- Button clicks
- Queue API responses

**Usage:**
```python
from mock_browser import MockBrowserClient

client = MockBrowserClient()
# Use in place of real BrowserClient for testing
```

### `sample_workflow.json`
Sample ComfyUI workflow for testing workflow loading and validation.

**Structure:**
- 5 nodes: LoadImage → VAEEncode → KSampler → VAEDecode → SaveImage
- Includes all required node configurations and connections
- Used by unit tests in `tests/comfyui/test_workflow_actions.py`

## Example Scripts

### `test_comfyui_modes.py`
Demonstrates both headless and non-headless browser modes.

**Features:**
- Tests browser server connection
- Captures screenshots in headless mode
- Shows page info (URL, title)
- Validates authentication

**Usage:**
```bash
# Start headless browser first
browser-agent comfyui open --credentials vastai_credentials.txt --headless

# Then run the test
python examples/comfyui/tests/test_comfyui_modes.py
```

### `test_sidebar_automation.py`
Automated clicking of ComfyUI sidebar buttons (Menu, Assets, Nodes, Models, Workflows, NodesMap).

**Features:**
- Programmatically clicks sidebar buttons
- Tests multiple selector strategies
- Opens and closes popovers automatically
- 1-second delays between actions to prevent overwhelming UI

**Usage:**
```bash
# Start non-headless browser to watch
browser-agent comfyui open --credentials vastai_credentials.txt

# Run automation
python examples/comfyui/tests/test_sidebar_automation.py
```

### `test_sidebar_smart_toggle.py`
Smart popover toggle with state detection - only clicks when needed.

**Features:**
- Detects current popover state (open/closed)
- Only clicks if state change is needed
- Tests all sidebar buttons: Menu, Assets, Nodes, Models, Workflows, NodesMap
- Uses `aria-expanded`, `aria-pressed`, and class attributes for state detection
- 1-second delays between operations

**Functions:**
- `check_popover_state(button_name)` - Returns current state indicators
- `toggle_sidebar_popover(button_name, desired_state)` - Smart toggle to 'open' or 'closed'

**Usage:**
```bash
# Start browser
browser-agent comfyui open --credentials vastai_credentials.txt

# Run smart toggle test
python examples/comfyui/tests/test_sidebar_smart_toggle.py
```

## Unit Test Usage

Test fixtures are imported by the main test suite at `tests/comfyui/test_workflow_actions.py`:

```python
# Tests import from this directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "examples" / "comfyui" / "tests"))
from mock_browser import MockBrowserClient
```

## Running Tests

```bash
# Run all ComfyUI unit tests
pytest tests/comfyui/ -v

# With coverage
pytest tests/comfyui/ --cov=browser_agent.comfyui --cov-report=term-missing

# Run example scripts (requires running browser server)
browser-agent comfyui open --credentials vastai_credentials.txt
python examples/comfyui/tests/test_sidebar_smart_toggle.py
```
