# ComfyUI Test Fixtures

This directory contains test fixtures and utilities for testing ComfyUI integration.

## Files

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

## Test Usage

These fixtures are imported by the main test suite at `tests/comfyui/test_workflow_actions.py`:

```python
# Tests import from this directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "examples" / "comfyui" / "tests"))
from mock_browser import MockBrowserClient
```

## Running Tests

```bash
# Run all ComfyUI tests
pytest tests/comfyui/ -v

# With coverage
pytest tests/comfyui/ --cov=browser_agent.comfyui --cov-report=term-missing
```
