# Persistent Browser Server Guide

## Overview

The browser server allows you to **authenticate once** and then run multiple extraction scripts without reopening the browser or re-authenticating. Perfect for development and debugging!

## Architecture

- **Server** (`browser_agent.server.BrowserServer`): Keeps browser open, listens for commands on port 9999
- **Client** (`browser_agent.server.BrowserClient`): Python library to send commands to the server
- **CLI**: `browser-agent server` command to start the server

## Quick Start

### 1. Start the Browser Server

In **Terminal 1**, start the server:

```bash
# Start with optional initial URL
browser-agent server https://example.com --browser-exe /usr/bin/brave-browser

# Or start without URL
browser-agent server --browser-exe /usr/bin/brave-browser
```

This will:
1. Open the browser
2. Navigate to the initial URL (if provided)
3. Wait for you to authenticate if needed
4. Start listening on port 9999

**Leave this terminal running!** The browser stays open.

### 2. Connect with Python Client

In **Terminal 2** (or more), use the BrowserClient:

```python
from browser_agent.server import BrowserClient

client = BrowserClient()

# Check server is running
result = client.ping()
print(result)  # {'status': 'success', 'message': 'pong'}

# Navigate to a URL
result = client.goto("https://example.com/page")
print(result)  # {'status': 'success', 'url': '...', 'title': '...'}

# Extract links
result = client.extract('a[href*="/items/"]')
links = result.get('links', [])
```

**No re-authentication needed!** 🎉

## Benefits

✅ **One-time authentication** - Log in once, use all day  
✅ **Fast iteration** - No browser startup time  
✅ **Multiple scripts** - Run different extractions without restarting  
✅ **Easy debugging** - Browser stays open, inspect as needed  
✅ **Parallel development** - Server runs independently

## Python API

### BrowserClient Methods

```python
from browser_agent.server import BrowserClient

client = BrowserClient(host="localhost", port=9999)

# Navigation
client.goto(url)              # Navigate to URL
client.info()                 # Get current page info

# Interaction
client.click(selector, timeout=5000)       # Click an element
client.wait(selector, timeout=10000)       # Wait for element

# Extraction
client.extract(selector)       # Extract links matching selector
client.extract_html(selector)  # Extract HTML content
client.eval_js(code)          # Execute JavaScript

# File Operations
client.download(url, save_path)  # Download a file

# Server
client.ping()                 # Check server is alive
```

### Starting Server Programmatically

```python
from browser_agent.server import BrowserServer

server = BrowserServer(browser_exe="/usr/bin/brave-browser", port=9999)
server.start(initial_url="https://example.com", wait_for_auth=True)
```

## Stopping the Server

In the server terminal, press `Ctrl+C` to stop the browser and server.

## Troubleshooting

**Connection refused:**
- Make sure the server is running in another terminal
- Check the port isn't already in use: `lsof -i :9999`

**Server not responding:**
- Restart the server
- Check the browser didn't crash

**Want a different port:**
```bash
browser-agent server --port 8888
```

## Example Workflow

```bash
# Terminal 1: Start server (one time)
browser-agent server https://example.com --browser-exe /usr/bin/brave-browser
# Authenticate if needed...
# Press Enter
# Server now running...

# Terminal 2: Use Python client
python -c "
from browser_agent.server import BrowserClient
client = BrowserClient()
print(client.info())
"

# Terminal 1: Ctrl+C to stop when done
```

## For Site-Specific Examples

See `examples/patreon/` for a complete example of using the browser server for Patreon content extraction.
