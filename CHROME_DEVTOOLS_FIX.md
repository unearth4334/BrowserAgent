# Fixing Chrome DevTools Protocol Access

## Problem

The `/background` API endpoint returns a 403 error:
```
Rejected an incoming WebSocket connection from the http://localhost:9222 origin.
Use the command line flag --remote-allow-origins=http://localhost:9222
```

## Root Cause

Chrome's DevTools Protocol requires the `--remote-allow-origins` flag to allow WebSocket connections for security reasons.

## Solution

Add the following flag to Chrome's launch arguments:

```bash
--remote-allow-origins=*
```

or more specifically:

```bash
--remote-allow-origins=http://localhost:9222
```

## Implementation Locations

### Option 1: Docker Container (Most Likely)
If Chrome is running in a Docker container, update the Chrome launch command:

**In Dockerfile:**
```dockerfile
CMD google-chrome \
    --remote-debugging-port=9222 \
    --remote-allow-origins=* \
    --no-sandbox \
    --disable-dev-shm-usage \
    ...other flags...
```

**In docker-compose.yml:**
```yaml
command: >
  google-chrome
  --remote-debugging-port=9222
  --remote-allow-origins=*
  --no-sandbox
  --disable-dev-shm-usage
```

### Option 2: Kiosk Script
If using a startup script (like `kiosk.sh`), add the flag there:

```bash
chromium-browser \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --kiosk \
  ...
```

### Option 3: Systemd Service
If Chrome runs as a systemd service:

```ini
[Service]
ExecStart=/usr/bin/google-chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  ...
```

## After Making Changes

1. **Rebuild Docker container** (if using Docker):
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Restart the service** (if using systemd):
   ```bash
   sudo systemctl restart chrome-kiosk
   ```

3. **Restart Chrome** (if running directly):
   - Close Chrome completely
   - Launch with the new flags

## Verification

Test the API endpoint:
```bash
curl -X POST http://localhost:5000/background \
  -H "Content-Type: application/json" \
  -d '{"color": "#ff0000"}'
```

Expected successful response:
```json
{"status": "ok", "color": "#ff0000"}
```

## Security Note

Using `--remote-allow-origins=*` allows connections from any origin. For production use, specify the exact origin:

```bash
--remote-allow-origins=http://localhost:5000,http://localhost:9222
```

## Alternative: Disable This Feature

If you don't need the background color API, you can use other test app features that don't require Chrome DevTools Protocol:
- Tile detection
- Media pane detection
- Playwright-based interactions (navigate, click, type, etc.)
