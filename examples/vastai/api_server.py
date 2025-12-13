#!/usr/bin/env python3
"""
FastAPI server for VastAI ComfyUI automation.

Provides REST API endpoints for:
- Starting authenticated browser sessions
- Opening workflows
- Queueing workflow executions

This allows credentials to be provided via API requests instead of files.
"""
from pathlib import Path
import sys
from typing import Optional

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from browser_agent.server.browser_server import BrowserServer
from browser_agent.server.browser_client import BrowserClient
from browser_agent.browser.actions import Navigate
import uvicorn

# Import workflow functions
from open_workflow import open_workflow
from queue_workflow import queue_workflow


app = FastAPI(
    title="VastAI ComfyUI Automation API",
    description="REST API for automating ComfyUI workflows on vast.ai instances",
    version="1.0.0"
)

# Global browser server instance
browser_server: Optional[BrowserServer] = None
browser_client: Optional[BrowserClient] = None


class Credentials(BaseModel):
    """Authentication credentials for vast.ai instance."""
    username: Optional[str] = Field(None, description="HTTP basic auth username (optional for localhost)")
    password: Optional[str] = Field(None, description="HTTP basic auth password (optional for localhost)")
    url: str = Field(..., description="ComfyUI instance URL (e.g., https://example.trycloudflare.com or http://localhost:8188)")
    workflow_path: Optional[str] = Field(None, description="ComfyUI workflow path to auto-open (e.g., 'workflows/my_workflow.json')")


class StartSessionRequest(BaseModel):
    """Request to start an authenticated browser session."""
    credentials: Credentials
    port: int = Field(9999, description="Port for browser server")
    headless: bool = Field(True, description="Run browser in headless mode")
    auto_open_workflow: bool = Field(True, description="Automatically open workflow if workflow_path is provided in credentials")


class OpenWorkflowRequest(BaseModel):
    """Request to open a workflow."""
    workflow_path: str = Field(..., description="Path to workflow file in ComfyUI (e.g., 'workflows/my_workflow.json')")
    port: int = Field(9999, description="Browser server port to connect to")


class QueueWorkflowRequest(BaseModel):
    """Request to queue workflow executions."""
    iterations: int = Field(1, ge=1, le=100, description="Number of times to execute the workflow")
    port: int = Field(9999, description="Browser server port to connect to")


class SessionStatus(BaseModel):
    """Status of the browser session."""
    active: bool
    port: Optional[int] = None
    url: Optional[str] = None


class OperationResponse(BaseModel):
    """Response for workflow operations."""
    success: bool
    message: str
    details: Optional[dict] = None


@app.get("/", response_model=dict)
async def root():
    """API root endpoint."""
    return {
        "name": "VastAI ComfyUI Automation API",
        "version": "1.0.0",
        "endpoints": {
            "POST /session/start": "Start authenticated browser session",
            "POST /session/stop": "Stop browser session",
            "GET /session/status": "Get session status",
            "POST /workflow/open": "Open a workflow",
            "POST /workflow/queue": "Queue workflow executions"
        }
    }


@app.post("/session/start", response_model=OperationResponse)
async def start_session(request: StartSessionRequest, background_tasks: BackgroundTasks):
    """
    Start an authenticated browser session.
    
    This creates a persistent browser instance and navigates to the ComfyUI instance
    with HTTP basic authentication.
    """
    global browser_server, browser_client
    
    # Check if session already exists
    if browser_server and browser_server.running:
        return OperationResponse(
            success=False,
            message="Browser session already active. Stop the existing session first.",
            details={"port": browser_server.port}
        )
    
    try:
        # Build URL with optional authentication
        base_url = request.credentials.url.strip()
        
        # Add authentication only if username and password are provided
        if request.credentials.username and request.credentials.password:
            username = request.credentials.username
            password = request.credentials.password
            
            # Remove protocol if present to rebuild with auth
            if "://" in base_url:
                protocol, rest = base_url.split("://", 1)
                auth_url = f"{protocol}://{username}:{password}@{rest}"
            else:
                auth_url = f"https://{username}:{password}@{base_url}"
        else:
            # No authentication needed (e.g., localhost)
            auth_url = base_url
            if not base_url.startswith(("http://", "https://")):
                auth_url = f"http://{base_url}"
        
        # Start browser server
        browser_server = BrowserServer(
            port=request.port,
            headless=request.headless,
            log_file=f"/tmp/vastai_browser_{request.port}.log"
        )
        
        # Start in background since it's a blocking call
        def start_server():
            browser_server.start(initial_url=auth_url, wait_for_auth=False)
        
        background_tasks.add_task(start_server)
        
        # Create client for future operations
        browser_client = BrowserClient(port=request.port)
        
        # Give server a moment to start
        import time
        time.sleep(2)
        
        # Verify server is responding
        ping_result = browser_client.ping()
        if ping_result.get("status") != "success":
            raise Exception("Server started but not responding to ping")
        
        # Mask credentials in response if they exist
        display_url = auth_url
        if request.credentials.username and request.credentials.password:
            display_url = auth_url.replace(f"{request.credentials.username}:{request.credentials.password}@", "***:***@")
        
        details = {
            "port": request.port,
            "url": display_url,
            "headless": request.headless
        }
        
        # Auto-open workflow if provided
        workflow_opened = False
        if request.auto_open_workflow and request.credentials.workflow_path:
            import time
            time.sleep(1)  # Extra moment for page to stabilize
            try:
                workflow_opened = open_workflow(browser_client, request.credentials.workflow_path)
                details["workflow_path"] = request.credentials.workflow_path
                details["workflow_opened"] = workflow_opened
            except Exception as e:
                details["workflow_error"] = str(e)
        
        message = f"Browser session started on port {request.port}"
        if workflow_opened:
            message += f" and opened workflow: {request.credentials.workflow_path}"
        
        return OperationResponse(
            success=True,
            message=message,
            details=details
        )
        
    except Exception as e:
        browser_server = None
        browser_client = None
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@app.post("/session/stop", response_model=OperationResponse)
async def stop_session():
    """Stop the active browser session."""
    global browser_server, browser_client
    
    if not browser_server or not browser_server.running:
        return OperationResponse(
            success=False,
            message="No active browser session to stop"
        )
    
    try:
        # Stop the server
        browser_server.running = False
        if browser_server.controller:
            browser_server.controller.stop()
        
        port = browser_server.port
        browser_server = None
        browser_client = None
        
        return OperationResponse(
            success=True,
            message=f"Browser session on port {port} stopped"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop session: {str(e)}")


@app.get("/session/status", response_model=SessionStatus)
async def session_status():
    """Get the status of the browser session."""
    if browser_server and browser_server.running:
        # Try to get current URL from observation
        url = None
        try:
            if browser_client:
                info_result = browser_client.info()
                if info_result.get("status") == "success":
                    url = info_result.get("url")
        except:
            pass
        
        return SessionStatus(
            active=True,
            port=browser_server.port,
            url=url
        )
    else:
        return SessionStatus(active=False)


@app.post("/workflow/open", response_model=OperationResponse)
async def open_workflow_endpoint(request: OpenWorkflowRequest):
    """
    Open a workflow in ComfyUI.
    
    Navigates the ComfyUI interface to open the specified workflow file.
    Requires an active browser session.
    """
    if not browser_client:
        raise HTTPException(
            status_code=400,
            detail="No active browser session. Start a session first with POST /session/start"
        )
    
    try:
        # Check if server is responding
        ping_result = browser_client.ping()
        if ping_result.get("status") != "success":
            raise HTTPException(status_code=503, detail="Browser server not responding")
        
        # Open the workflow
        success = open_workflow(browser_client, request.workflow_path)
        
        if success:
            return OperationResponse(
                success=True,
                message=f"Successfully opened workflow: {request.workflow_path}"
            )
        else:
            return OperationResponse(
                success=False,
                message=f"Failed to open workflow: {request.workflow_path}",
                details={"workflow_path": request.workflow_path}
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error opening workflow: {str(e)}")


@app.post("/workflow/queue", response_model=OperationResponse)
async def queue_workflow_endpoint(request: QueueWorkflowRequest):
    """
    Queue workflow executions.
    
    Sets the batch count and clicks the run button to queue executions.
    Requires an active browser session with a workflow already opened.
    """
    if not browser_client:
        raise HTTPException(
            status_code=400,
            detail="No active browser session. Start a session first with POST /session/start"
        )
    
    try:
        # Check if server is responding
        ping_result = browser_client.ping()
        if ping_result.get("status") != "success":
            raise HTTPException(status_code=503, detail="Browser server not responding")
        
        # Queue the workflow
        success = queue_workflow(browser_client, request.iterations)
        
        if success:
            return OperationResponse(
                success=True,
                message=f"Successfully queued {request.iterations} workflow execution(s)",
                details={"iterations": request.iterations}
            )
        else:
            return OperationResponse(
                success=False,
                message=f"Failed to queue workflow executions",
                details={"iterations": request.iterations}
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error queueing workflow: {str(e)}")


def main():
    """Run the API server."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="VastAI ComfyUI Automation API Server"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server port (default: %(default)s)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Starting VastAI ComfyUI Automation API server")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Docs: http://localhost:{args.port}/docs")
    
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
