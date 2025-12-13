# Persistent Browser Server Guide

## Overview

The browser server allows you to **authenticate once** and then run multiple extraction scripts without reopening the browser or re-authenticating. Perfect for development and debugging!

## Architecture

- **Server** (`browser_server.py`): Keeps browser open, listens for commands on port 9999
- **Client** (`browser_client.py`): Python library to send commands to the server
- **Extraction Script** (`extract_patreon_client.py`): Uses the client to extract collections

## Quick Start

### 1. Start the Browser Server

In **Terminal 1**, start the server and authenticate:

```bash
cd /home/sdamk/dev/BrowserAgent
source .venv/bin/activate
python scripts/browser_server.py /usr/bin/brave-browser
```

This will:
1. Open Brave browser
2. Navigate to Patreon
3. Wait for you to log in
4. Start listening on port 9999

**Leave this terminal running!** The browser stays open.

### 2. Run Extraction Scripts

In **Terminal 2** (or more), run extraction scripts:

```bash
cd /home/sdamk/dev/BrowserAgent
source .venv/bin/activate
python scripts/extract_patreon_client.py 1611241
```

This will:
1. Connect to the running browser
2. Navigate to the collection
3. Click "Load more" buttons
4. Extract and save all links

**No re-authentication needed!** 🎉

### 3. Send Individual Commands

You can also send commands directly:

```bash
# Check if server is alive
python scripts/browser_client.py ping

# Get current page info
python scripts/browser_client.py info

# Navigate somewhere
python scripts/browser_client.py goto "https://www.patreon.com/collection/1611241"

# Wait for content
python scripts/browser_client.py wait 'a[href*="/posts/"]' 15000

# Click a button
python scripts/browser_client.py click 'button:has-text("Load more")' 5000

# Extract links
python scripts/browser_client.py extract 'a[href*="/posts/"]'
```

## Benefits

✅ **One-time authentication** - Log in once, use all day  
✅ **Fast iteration** - No browser startup time  
✅ **Multiple scripts** - Run different extractions without restarting  
✅ **Easy debugging** - Browser stays open, inspect as needed  
✅ **Parallel development** - Server runs independently

## Python API

Use the client in your own scripts:

```python
from browser_client import BrowserClient

client = BrowserClient()

# Navigate
result = client.goto("https://www.patreon.com/collection/1611241")
print(result)  # {'status': 'success', 'url': '...', 'title': '...'}

# Click a button
result = client.click('button:has-text("Load more")', timeout=5000)

# Extract links
result = client.extract('a[href*="/posts/"]')
links = result.get('links', [])
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
python scripts/browser_server.py /usr/bin/brave-browser 8888
python scripts/browser_client.py ping  # Add port parameter in code if needed
```

## Example Workflow

```bash
# Terminal 1: Start server (one time)
python scripts/browser_server.py /usr/bin/brave-browser
# Log in to Patreon...
# Press Enter
# Server now running...

# Terminal 2: Extract collection 1
python scripts/extract_patreon_client.py 1611241

# Terminal 2: Extract another collection (no re-auth!)
python scripts/extract_patreon_client.py 2222222

# Terminal 2: Test a selector
python scripts/browser_client.py extract 'a.post-link'

# Terminal 2: Navigate manually
python scripts/browser_client.py goto "https://www.patreon.com/home"

# Terminal 1: Ctrl+C to stop when done
```
