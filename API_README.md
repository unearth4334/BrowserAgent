# Grok Auto Download Favourites - API Documentation

## Overview

This project provides a Docker-based browser automation system with a REST API for controlling Chrome running inside a VNC-accessible container. Access the browser via noVNC at http://localhost:6080 and control it programmatically via the API at http://localhost:5000.

## Quick Start

```bash
# Build and start the container
docker-compose up -d

# Access the browser
open http://localhost:6080/vnc.html

# Test the API
curl http://localhost:5000/health
```

## API Endpoints

### Health Check
**GET** `/health`

Check if the API server is running.

```bash
curl http://localhost:5000/health
```

Response:
```json
{"status": "ok"}
```

---

### List Macros
**GET** `/macros`

List all available predefined keyboard macros.

```bash
curl http://localhost:5000/macros
```

Response:
```json
{
  "macros": {
    "close_tab": "ctrl+w",
    "back": "alt+Left",
    "save": "ctrl+s",
    "enter": "Return",
    "refresh": "ctrl+r",
    "new_tab": "ctrl+t",
    "forward": "alt+Right",
    "focus_address": "ctrl+l",
    "fullscreen": "F11",
    "scroll_up": "button:4",
    "scroll_down": "button:5"
  }
}
```

---

### Trigger Macro
**POST** `/macro/<name>`

Execute a predefined keyboard or mouse macro.

```bash
# Close current tab
curl -X POST http://localhost:5000/macro/close_tab

# Navigate back
curl -X POST http://localhost:5000/macro/back

# Save page
curl -X POST http://localhost:5000/macro/save

# Press Enter
curl -X POST http://localhost:5000/macro/enter

# Toggle fullscreen
curl -X POST http://localhost:5000/macro/fullscreen

# Scroll up/down
curl -X POST http://localhost:5000/macro/scroll_up
curl -X POST http://localhost:5000/macro/scroll_down
```

Response:
```json
{"status": "ok", "macro": "close_tab", "keys": "ctrl+w"}
```

---

### Send Custom Keys
**POST** `/keys`

Send custom key sequences or combinations.

```bash
# Send key combination
curl -X POST http://localhost:5000/keys \
  -H "Content-Type: application/json" \
  -d '{"keys": "ctrl+shift+t"}'

# Send multiple keys
curl -X POST http://localhost:5000/keys \
  -H "Content-Type: application/json" \
  -d '{"keys": "ctrl+l"}'
```

Request body:
```json
{"keys": "ctrl+shift+t"}
```

Response:
```json
{"status": "ok", "keys": "ctrl+shift+t"}
```

**Key syntax:**
- Modifiers: `ctrl`, `alt`, `shift`, `super`
- Special keys: `Return`, `Escape`, `Tab`, `BackSpace`, `Delete`, `Up`, `Down`, `Left`, `Right`, `F1`-`F12`
- Combinations: `ctrl+c`, `alt+Left`, `ctrl+shift+n`

---

### Type Text
**POST** `/type`

Type text into the currently focused element.

```bash
curl -X POST http://localhost:5000/type \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'
```

Request body:
```json
{"text": "Hello World"}
```

Response:
```json
{"status": "ok", "text": "Hello World"}
```

---

### Change Background Color
**POST** `/background`

Change the background color of the current webpage.

```bash
# Use hex color
curl -X POST http://localhost:5000/background \
  -H "Content-Type: application/json" \
  -d '{"color": "#ff0000"}'

# Use named color
curl -X POST http://localhost:5000/background \
  -H "Content-Type: application/json" \
  -d '{"color": "lightblue"}'
```

Request body:
```json
{"color": "#ff0000"}
```

Response:
```json
{"status": "ok", "color": "#ff0000"}
```

---

### Execute JavaScript
**POST** `/execute`

Execute arbitrary JavaScript code in the current page using Chrome DevTools Protocol.

```bash
# Get page title
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "document.title"}'

# Click an element
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "document.querySelector(\"button\").click()"}'

# Modify page content
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "document.body.innerHTML = \"<h1>Hello!</h1>\""}'
```

Request body:
```json
{"code": "document.title"}
```

Response:
```json
{
  "status": "ok",
  "result": {
    "type": "string",
    "value": "Page Title"
  }
}
```

---

## Usage Examples

### Automated Navigation Workflow

```bash
# Focus address bar
curl -X POST http://localhost:5000/macro/focus_address

# Type URL
curl -X POST http://localhost:5000/type \
  -H "Content-Type: application/json" \
  -d '{"text": "https://example.com"}'

# Press Enter
curl -X POST http://localhost:5000/macro/enter

# Wait for page load, then scroll down
sleep 2
curl -X POST http://localhost:5000/macro/scroll_down

# Execute JavaScript to extract data
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "document.querySelector(\"h1\").textContent"}'
```

### Form Filling

```bash
# Click input field via JavaScript
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "document.querySelector(\"#username\").focus()"}'

# Type username
curl -X POST http://localhost:5000/type \
  -H "Content-Type: application/json" \
  -d '{"text": "myuser@example.com"}'

# Tab to next field
curl -X POST http://localhost:5000/keys \
  -H "Content-Type: application/json" \
  -d '{"keys": "Tab"}'

# Type password
curl -X POST http://localhost:5000/type \
  -H "Content-Type: application/json" \
  -d '{"text": "mypassword"}'

# Submit form
curl -X POST http://localhost:5000/macro/enter
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200 OK`: Success
- `400 Bad Request`: Missing or invalid parameters
- `500 Internal Server Error`: Execution failed

Error response format:
```json
{
  "error": "Error message description",
  "available": ["list", "of", "valid", "options"]
}
```

---

## Environment Variables

Configure via `docker-compose.yml`:

- `VNC_PASS`: VNC password (not used if VNC is passwordless)
- `SCREEN_W`: Screen width (default: 1920)
- `SCREEN_H`: Screen height (default: 1080)
- `URL`: Initial Chrome URL (default: https://grok.com/)

---

## Ports

- **6080**: noVNC web interface (browser access)
- **5000**: REST API
- **9222**: Chrome DevTools Protocol (internal)

---

## Development

### View Container Logs
```bash
docker-compose logs -f grok-kiosk
```

### Shell into Container
```bash
docker exec -it grok-kiosk bash
```

### Rebuild After Changes
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Limitations

- Keyboard macros use `xdotool`, which sends input to the X display (works for any window)
- JavaScript execution requires an active Chrome tab with DevTools Protocol enabled
- Scroll macros repeat 3 times for smoother scrolling
- Text typing clears modifiers before typing to avoid conflicts
