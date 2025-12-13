# ComfyUI Workflow Execution Guide

This guide explains how to use BrowserAgent to execute ComfyUI workflows programmatically, with support for headless execution in Docker containers.

## Overview

BrowserAgent can automate ComfyUI workflow execution by:

1. Loading workflow JSON files
2. Setting workflow parameters dynamically
3. Triggering workflow execution
4. Waiting for completion
5. Running entirely headless for Docker/containerized environments

## Prerequisites

1. **ComfyUI Running**: Ensure ComfyUI WebUI is accessible at a URL (e.g., `http://localhost:8188`)
2. **Workflow File**: Have a `.json` workflow file exported from ComfyUI
3. **BrowserAgent Installed**: 
   ```bash
   pip install -e .[dev]
   playwright install chromium
   ```

## Basic Usage

### Simple Workflow Execution

Run a workflow without parameters:

```bash
browser-agent run-canvas /path/to/workflow.json
```

This will:
- Launch a headless Chromium browser
- Navigate to `http://localhost:8188` (default)
- Load the workflow
- Trigger execution
- Wait for completion (max 600 seconds)

### Custom WebUI URL

If ComfyUI is running on a different host/port:

```bash
browser-agent run-canvas /path/to/workflow.json \
    --webui-url http://192.168.1.100:8188
```

### Setting Workflow Parameters

Pass parameters as a JSON string using the `--params` option:

```bash
browser-agent run-canvas /path/to/workflow.json \
    --params '{"3": {"seed": 42}, "4": {"steps": 20, "cfg": 7.5}}'
```

**Parameter format:**
```json
{
  "node_id": {
    "field_name": value,
    "another_field": value
  },
  "another_node_id": {
    "field_name": value
  }
}
```

To find node IDs, open your workflow JSON file and look for the node keys.

### Complete Example

```bash
browser-agent run-canvas /app/workflows/my_workflow.json \
    --webui-url http://localhost:8188 \
    --params '{"3": {"seed": 42}, "4": {"steps": 20}}' \
    --max-wait 1200 \
    --headless
```

## Docker/Containerized Usage

BrowserAgent is designed to work in headless Docker containers:

### Dockerfile Example

```dockerfile
FROM python:3.11-slim

# Install system dependencies for Chromium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install BrowserAgent
WORKDIR /app
COPY . .
RUN pip install -e .[dev]
RUN playwright install chromium

# Run workflow
CMD ["browser-agent", "run-canvas", "/app/workflows/workflow.json", "--webui-url", "http://comfyui:8188"]
```

### Docker Compose Example

```yaml
version: '3.8'

services:
  comfyui:
    image: comfyui/comfyui:latest
    ports:
      - "8188:8188"
    volumes:
      - ./workflows:/workflows
      - ./output:/output

  browser-agent:
    build: .
    depends_on:
      - comfyui
    environment:
      - BROWSER_AGENT_HEADLESS=1
      - BROWSER_AGENT_BROWSER_TYPE=chromium
      - BROWSER_AGENT_EXTRA_ARGS=--no-sandbox,--disable-gpu
    volumes:
      - ./workflows:/app/workflows
    command: >
      browser-agent run-canvas /app/workflows/workflow.json
      --webui-url http://comfyui:8188
      --params '{"3": {"seed": 42}}'
```

## Environment Variables

Configure BrowserAgent for your environment:

```bash
# Browser settings
export BROWSER_AGENT_HEADLESS=1
export BROWSER_AGENT_BROWSER_TYPE=chromium

# Timeouts (in milliseconds)
export BROWSER_AGENT_LAUNCH_TIMEOUT=15000
export BROWSER_AGENT_NAVIGATION_TIMEOUT=30000

# Wait strategy
export BROWSER_AGENT_DEFAULT_WAIT=networkidle  # or 'load' or 'domcontentloaded'

# Docker-specific args (automatically set for headless Chromium)
export BROWSER_AGENT_EXTRA_ARGS="--no-sandbox,--disable-gpu,--disable-dev-shm-usage"
```

## Programmatic Usage

You can also use BrowserAgent programmatically in Python:

```python
from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.agent.workflow_runner import CanvasWorkflowRunner

# Create browser controller
controller = PlaywrightBrowserController(
    headless=True,
    browser_type="chromium",
    screenshot_on_error=True,
)

# Start browser
controller.start()

try:
    # Create workflow runner
    runner = CanvasWorkflowRunner(
        browser=controller,
        webui_url="http://localhost:8188",
        max_wait_time=600.0,
    )
    
    # Load workflow
    runner.load_workflow("/path/to/workflow.json")
    
    # Set parameters
    runner.set_parameter("3", "seed", 42)
    runner.set_parameter("4", "steps", 20)
    
    # Execute workflow
    runner.run()
    
    # Wait for completion
    success = runner.wait_for_completion()
    
    if success:
        print("Workflow completed successfully!")
    else:
        print("Workflow timed out")
        
finally:
    controller.stop()
```

## Troubleshooting

### Browser fails to launch

**Error**: `Failed to start browser`

**Solution**: Install Playwright browsers:
```bash
playwright install chromium
```

For Docker, ensure all dependencies are installed (see Dockerfile example above).

### Workflow doesn't load

**Error**: `Could not set parameter`

**Possible causes**:
1. ComfyUI WebUI is not accessible at the specified URL
2. Workflow JSON is malformed
3. Node IDs in parameters don't match workflow

**Solution**: 
- Check ComfyUI is running: `curl http://localhost:8188`
- Validate workflow JSON
- Verify node IDs in the workflow file

### Timeout waiting for completion

**Error**: `Workflow did not complete within timeout`

**Solution**: Increase `--max-wait` parameter:
```bash
browser-agent run-canvas workflow.json --max-wait 1800  # 30 minutes
```

### Screenshot on error

If errors occur, BrowserAgent automatically captures screenshots to `/tmp/browser-agent-screenshots/`.

Enable explicitly:
```python
controller = PlaywrightBrowserController(screenshot_on_error=True)
```

## Advanced Features

### Custom Completion Detection

The workflow runner polls ComfyUI's queue status to detect completion:

```javascript
// Default completion check (runs every 2 seconds)
{
  running: 0,  // No jobs running
  pending: 0   // No jobs pending
}
```

You can customize the check interval:

```python
runner = CanvasWorkflowRunner(
    browser=controller,
    webui_url="http://localhost:8188",
    completion_check_interval=5.0,  # Check every 5 seconds
    max_wait_time=1200.0,           # Wait max 20 minutes
)
```

### JavaScript Execution

Execute custom JavaScript in the ComfyUI context:

```python
from browser_agent.browser.actions import ExecuteJS

# Get queue status
controller.perform(ExecuteJS("""
    return {
        running: app.ui.queue.running,
        pending: app.ui.queue.pending
    };
"""))

result = controller.get_last_js_result()
print(f"Queue status: {result}")
```

### File Upload

Upload files (e.g., images) to workflow:

```python
from browser_agent.browser.actions import UploadFile

controller.perform(UploadFile(
    selector="input[type=file]",
    file_path="/path/to/image.png"
))
```

## Exit Codes

The `run-canvas` command returns:
- `0`: Workflow completed successfully
- `1`: Error occurred (file not found, browser failure, etc.)
- `2`: Workflow timed out

Use in scripts:

```bash
if browser-agent run-canvas workflow.json; then
    echo "Success!"
else
    echo "Failed with code $?"
fi
```

## Best Practices

1. **Use specific timeouts**: Set `--max-wait` based on your workflow's expected duration
2. **Enable screenshots**: Helps debug issues in headless mode
3. **Test workflows first**: Test in ComfyUI GUI before automating
4. **Use environment variables**: Easier configuration in Docker
5. **Monitor logs**: BrowserAgent provides detailed logging
6. **Version your workflows**: Keep workflow JSON files in version control

## Examples

See the `examples/` directory for complete working examples:
- Basic workflow execution
- Parameter injection
- Docker deployment
- Error handling

## Need Help?

- Check logs for detailed error messages
- Use `--no-headless` to debug in visible browser
- Review workflow JSON for correct node IDs
- Ensure ComfyUI is accessible and responding
