# Browser Server Interactive Commands

## Overview

The browser server supports interactive commands in foreground mode, allowing you to control the server without terminating it.

## Commands Available

### During Authentication Wait (wait_for_auth=True)

When the server starts with `wait_for_auth=True`, it pauses and waits for you to login. Available commands:

- **`ready`** - Continue to main server loop after authentication
- **`background`** / **`detach`** / **`bg`** - Exit foreground mode, server continues running in background
- **`status`** - Show current page info (URL, title)
- **`quit`** / **`exit`** - Stop the server and exit
- **`help`** - Show available commands

### During Main Server Loop

After authentication, the server enters its main loop. Available commands:

- **`status`** - Show current page info (URL, title, buttons, inputs)
- **`background`** / **`detach`** / **`bg`** - Exit foreground mode, server continues running in background
- **`quit`** / **`exit`** - Stop the server and exit
- **`help`** - Show available commands

## Usage Examples

### Example 1: Start, Login, and Detach

```bash
# Start server
python examples/civitai/browser_server.py /usr/bin/brave-browser

# Server opens browser at civitai.com
# You login in the browser window
# In the terminal, type:
background

# Server continues running in background
# You can now use the terminal for other commands
```

### Example 2: Check Status Before Detaching

```bash
# Start server
python examples/civitai/browser_server.py /usr/bin/brave-browser

# Check what page you're on
status

# Continue when ready
ready

# Later, detach from foreground
background
```

### Example 3: Using Client While Server is Foreground

The server responds to both interactive commands AND client connections simultaneously:

```bash
# Terminal 1: Start server
python examples/civitai/browser_server.py /usr/bin/brave-browser

# Terminal 2: Send commands via client
python examples/civitai/browser_client.py goto 'https://civitai.com/models/277058'
python examples/civitai/browser_client.py extract_html 'h1'

# Terminal 1: Server is still interactive, type:
background
# Now server runs in background, both terminals available
```

## Background Mode Benefits

The `background` command allows you to:

1. **Keep the browser session alive** - Don't lose your authentication
2. **Free up the terminal** - Terminal stops showing prompts, you can use it for client commands
3. **Continue using the client** - Send commands via client while server runs
4. **No session loss** - Browser stays open, server keeps running

**Note:** After typing `background`, the terminal will stop showing interactive prompts but the server process continues running. The terminal is available for you to use client commands or other tasks.

## Process Management

After entering background mode:

- **Server continues running** - Accepts client connections
- **Browser stays open** - Your session is preserved
- **Terminal is free** - You can run other commands

To stop the server after backgrounding:
```bash
# Find the process
ps aux | grep browser_server

# Send SIGTERM
kill <pid>

# Or use the client
python examples/civitai/browser_client.py quit
```

## Foreground vs Background Detection

The server automatically detects if it's running in:

- **Foreground**: Shows interactive prompts, accepts typed commands
- **Background**: No prompts, accepts client connections only

When you type `background`, the server:
1. Stops showing interactive prompts
2. Continues accepting client connections
3. Keeps the browser session alive
4. Frees the terminal for other use

## Tips

1. **Use `status` liberally** - Check what page you're on before proceeding
2. **Use `background` instead of Ctrl+Z** - Backgrounding properly lets server continue
3. **Don't use Ctrl+C** - This terminates the server; use `quit` or `background` instead
4. **Login before detaching** - Type `background` after completing authentication
