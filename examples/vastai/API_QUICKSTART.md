# VastAI API Quick Start Guide

## Overview

The VastAI API server provides a REST API for automating ComfyUI workflows on vast.ai instances. Instead of using credential files, you can provide credentials via API requests, making it easy to integrate with other applications.

## Installation

```bash
# Install the API dependencies
pip install -r examples/vastai/requirements-api.txt
```

This installs:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- Pydantic (data validation)

## Starting the Server

```bash
# Basic start
python examples/vastai/api_server.py

# Custom host and port
python examples/vastai/api_server.py --host 0.0.0.0 --port 8080

# With auto-reload for development
python examples/vastai/api_server.py --reload
```

The server will be available at:
- API: `http://localhost:8000`
- Interactive Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing the API

Run the test script to verify everything works:

```bash
# Basic tests (no credentials needed)
python examples/vastai/test_api.py

# Full tests with credentials
python examples/vastai/test_api.py --with-credentials
```

## Typical Workflow

### 1. Start Session

```bash
curl -X POST http://localhost:8000/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "credentials": {
      "username": "YOUR_USERNAME",
      "password": "YOUR_PASSWORD",
      "url": "https://your-instance.trycloudflare.com"
    },
    "port": 9999,
    "headless": true
  }'
```

### 2. Open Workflow

```bash
curl -X POST http://localhost:8000/workflow/open \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_path": "workflows/my_workflow.json"
  }'
```

### 3. Queue Executions

```bash
curl -X POST http://localhost:8000/workflow/queue \
  -H "Content-Type: application/json" \
  -d '{
    "iterations": 10
  }'
```

### 4. Check Status

```bash
curl http://localhost:8000/session/status
```

### 5. Stop Session

```bash
curl -X POST http://localhost:8000/session/stop
```

## Python Integration

```python
import requests
import time

API_URL = "http://localhost:8000"

def run_workflow(username, password, url, workflow_path, iterations):
    """Run a ComfyUI workflow on vast.ai."""
    
    # 1. Start authenticated session
    print("Starting session...")
    response = requests.post(f"{API_URL}/session/start", json={
        "credentials": {
            "username": username,
            "password": password,
            "url": url
        },
        "headless": True
    })
    response.raise_for_status()
    print(f"Session started: {response.json()['message']}")
    
    # Wait for browser to initialize
    time.sleep(3)
    
    # 2. Open workflow
    print(f"Opening workflow: {workflow_path}")
    response = requests.post(f"{API_URL}/workflow/open", json={
        "workflow_path": workflow_path
    })
    response.raise_for_status()
    print(f"Workflow opened: {response.json()['message']}")
    
    # 3. Queue executions
    print(f"Queueing {iterations} executions...")
    response = requests.post(f"{API_URL}/workflow/queue", json={
        "iterations": iterations
    })
    response.raise_for_status()
    print(f"Queued: {response.json()['message']}")
    
    # 4. Stop session
    print("Stopping session...")
    response = requests.post(f"{API_URL}/session/stop")
    response.raise_for_status()
    print("Session stopped")

# Example usage
if __name__ == "__main__":
    run_workflow(
        username="myuser",
        password="mypass",
        url="https://your-instance.trycloudflare.com",
        workflow_path="workflows/my_workflow.json",
        iterations=5
    )
```

## Advanced Usage

### Running Multiple Sessions

The API currently supports one browser session at a time per API server instance. To run multiple sessions:

1. **Option A**: Start multiple API servers on different ports
   ```bash
   python examples/vastai/api_server.py --port 8000 &
   python examples/vastai/api_server.py --port 8001 &
   ```

2. **Option B**: Stop and restart sessions as needed
   ```bash
   # Stop current session
   curl -X POST http://localhost:8000/session/stop
   
   # Start new session
   curl -X POST http://localhost:8000/session/start -d '...'
   ```

### Background Server

Run the API server as a background service:

```bash
# Using nohup
nohup python examples/vastai/api_server.py > api_server.log 2>&1 &

# Using systemd (create /etc/systemd/system/vastai-api.service)
[Unit]
Description=VastAI ComfyUI Automation API
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/BrowserAgent
ExecStart=/path/to/python examples/vastai/api_server.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . .

# Install Python dependencies
RUN pip install -e . && \
    pip install -r examples/vastai/requirements-api.txt && \
    playwright install chromium

# Expose API port
EXPOSE 8000

# Run API server
CMD ["python", "examples/vastai/api_server.py", "--host", "0.0.0.0"]
```

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid request (e.g., no active session)
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Browser server not responding

Example error response:
```json
{
  "detail": "No active browser session. Start a session first with POST /session/start"
}
```

## Security Considerations

⚠️ **Important Security Notes:**

1. **HTTPS in Production**: Always use HTTPS in production to encrypt credentials in transit
2. **Authentication**: Consider adding API authentication (OAuth, API keys, etc.)
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Input Validation**: All inputs are validated by Pydantic, but consider additional checks
5. **Network Access**: Restrict API access to trusted networks only

Example with basic authentication:
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "admin" or credentials.password != "secret":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials
```

## Troubleshooting

### "Browser server not responding"

The browser server takes 2-3 seconds to start. Wait a moment after starting the session before calling other endpoints.

### "No active browser session"

You must call `/session/start` before calling `/workflow/open` or `/workflow/queue`.

### Port Already in Use

If port 9999 (browser server) or 8000 (API server) is already in use:
```bash
# Find process using port
lsof -i :9999

# Kill process
kill -9 <PID>

# Or use different ports
python examples/vastai/api_server.py --port 8001
curl -X POST ... -d '{"port": 9998, ...}'
```

## API Reference

See the interactive documentation at `http://localhost:8000/docs` for complete API reference with request/response schemas and try-it-out functionality.
