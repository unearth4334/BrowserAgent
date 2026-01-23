# Issue: Chrome DevTools Protocol Returns 403 - Missing remote-allow-origins Flag

## Priority
**High** - Blocks background color API functionality

## Environment
- Chrome/Chromium running in Docker container
- API server on port 5000
- Chrome DevTools Protocol on port 9222
- noVNC on port 6080

## Problem Description

The `/background` API endpoint fails with a 403 Forbidden error when attempting to change the page background color via Chrome DevTools Protocol.

### Error Message
```
Rejected an incoming WebSocket connection from the http://localhost:9222 origin.
Use the command line flag --remote-allow-origins=http://localhost:9222 to allow 
connections from this origin or --remote-allow-origins=* to allow all origins.
```

### Steps to Reproduce
1. Start the grok test app: `python grok_test_app.py`
2. Select option 1 (API Command)
3. Select option 9 (Change background color)
4. Enter any color (e.g., "red" or "#ff0000")
5. Observe 403 error response

### Expected Behavior
The background color should change successfully, returning:
```json
{"status": "ok", "color": "#ff0000"}
```

### Actual Behavior
API returns 403 error with WebSocket handshake rejection.

## Root Cause

Chrome's DevTools Protocol enforces CORS-like restrictions on WebSocket connections. The flag `--remote-allow-origins` must be explicitly set to allow connections from the API server.

## Solution Required

### Required Change
Add the `--remote-allow-origins=*` flag to Chrome's launch arguments in the Docker container.

### Implementation

**Locate the Chrome launch configuration** in one of these files:
- `Dockerfile`
- `docker-compose.yml`
- Startup script (e.g., `kiosk.sh`, `start-chrome.sh`)
- Supervisor configuration

**Add the flag:**

#### Option A: Dockerfile
```dockerfile
CMD ["google-chrome", \
     "--remote-debugging-port=9222", \
     "--remote-allow-origins=*", \
     "--no-sandbox", \
     "--disable-dev-shm-usage", \
     "--disable-gpu", \
     # ... other existing flags
     "${URL}"]
```

#### Option B: docker-compose.yml
```yaml
services:
  grok-kiosk:
    # ... existing configuration
    command: >
      google-chrome
      --remote-debugging-port=9222
      --remote-allow-origins=*
      --no-sandbox
      --disable-dev-shm-usage
      --disable-gpu
      ${URL}
```

#### Option C: Startup Script (kiosk.sh or similar)
```bash
#!/bin/bash
google-chrome \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --no-sandbox \
  --disable-dev-shm-usage \
  --disable-gpu \
  --kiosk \
  "$URL"
```

### Security Consideration

For production environments, consider restricting origins instead of using `*`:
```bash
--remote-allow-origins=http://localhost:5000,http://localhost:9222
```

However, for development/testing, `*` is acceptable.

## Testing Instructions

### 1. Apply the Change
```bash
# Rebuild and restart the container
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 2. Verify Chrome is Running with New Flag
```bash
# Check Chrome process arguments
docker exec grok-kiosk ps aux | grep chrome
```

Look for `--remote-allow-origins=*` in the output.

### 3. Test the API Endpoint
```bash
# Test with curl
curl -X POST http://localhost:5000/background \
  -H "Content-Type: application/json" \
  -d '{"color": "#ff0000"}'
```

Expected response:
```json
{"status": "ok", "color": "#ff0000"}
```

### 4. Test via Test App
```bash
# Run the test app
python grok_test_app.py

# Select: 1 (API Command) -> 9 (Change background color)
# Enter: red
# Should see: ✅ Changed background to red
```

### 5. Visual Verification
1. Open noVNC: http://localhost:6080/vnc.html
2. Execute background color change via API
3. Observe the page background color change in the VNC viewer

## Additional Notes

### Related Files
- `grok_test_app.py` - Test application that uses this API
- `CHROME_DEVTOOLS_FIX.md` - Detailed troubleshooting guide
- `API_README.md` - API documentation

### Alternative Workaround
If the container cannot be modified immediately, other test app features still work:
- Tile detection (uses OpenCV, no DevTools needed)
- Media pane detection (uses OpenCV)
- Playwright interactions (navigate, click, type)

Only the "Change background color" API command requires this fix.

## Acceptance Criteria

- [ ] Chrome launches with `--remote-allow-origins=*` flag
- [ ] `/background` API endpoint returns 200 status code
- [ ] Background color changes are visible in noVNC viewer
- [ ] Test app's "Change background color" command works without errors
- [ ] No regression in existing Chrome functionality

## References

- Chrome DevTools Protocol Documentation: https://chromedevtools.github.io/devtools-protocol/
- Remote Debugging: https://www.chromium.org/developers/how-tos/run-chromium-with-flags/
- Test App Error Handling: `grok_test_app.py` lines 276-302
