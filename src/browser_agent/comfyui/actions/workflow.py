"""Workflow-related actions for ComfyUI."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Literal, Optional
import json
import time

from browser_agent.server.browser_client import BrowserClient
from browser_agent.comfyui.exceptions import WorkflowLoadError, QueueError


@dataclass
class LoadWorkflowAction:
    """
    Load a workflow into ComfyUI.
    
    This action loads a workflow JSON file into the ComfyUI interface using the
    UI-native method (localStorage chunking), which preserves all metadata and
    is compatible with all custom nodes including WidgetToString.
    
    Attributes:
        workflow_source: Path to workflow JSON file or dict with workflow data
        method: Loading method - "ui_native" (default), "api", or "hybrid"
        chunk_size: Size of localStorage chunks (default: 50000)
    """
    workflow_source: Path | dict
    method: Literal["ui_native", "api", "hybrid"] = "ui_native"
    chunk_size: int = 50000
    
    def execute(self, client: BrowserClient) -> Dict[str, Any]:
        """
        Execute the load workflow action.
        
        Args:
            client: BrowserClient instance
            
        Returns:
            Dict with execution result: {"success": bool, "node_count": int, ...}
            
        Raises:
            WorkflowLoadError: If workflow fails to load
        """
        if self.method == "ui_native":
            return self._load_ui_native(client)
        elif self.method == "api":
            return self._load_api(client)
        elif self.method == "hybrid":
            return self._load_hybrid(client)
        else:
            raise ValueError(f"Unknown load method: {self.method}")
    
    def _load_workflow_data(self) -> dict:
        """Load workflow data from source."""
        if isinstance(self.workflow_source, dict):
            return self.workflow_source
        
        workflow_path = Path(self.workflow_source)
        if not workflow_path.exists():
            raise WorkflowLoadError(f"Workflow file not found: {workflow_path}")
        
        try:
            with open(workflow_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise WorkflowLoadError(f"Invalid JSON in workflow file: {e}")
    
    def _load_ui_native(self, client: BrowserClient) -> Dict[str, Any]:
        """
        Load workflow using UI-native method (localStorage chunking).
        
        This is the most compatible method as it preserves all UI metadata.
        Based on queue_workflow_ui_click.py implementation.
        """
        # Load workflow data
        workflow = self._load_workflow_data()
        node_count = len(workflow.get("nodes", []))
        
        # Convert to JSON string
        ui_json_str = json.dumps(workflow)
        
        # Split into chunks for localStorage
        chunks = [
            ui_json_str[i:i+self.chunk_size] 
            for i in range(0, len(ui_json_str), self.chunk_size)
        ]
        
        # Store chunks in localStorage
        for i, chunk in enumerate(chunks):
            # Escape special characters for JavaScript string
            escaped = chunk.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
            
            result = client.eval_js(f"""
            () => {{
                localStorage.setItem('workflow_chunk_{i}', '{escaped}');
                return {{stored: true, chunk: {i}}};
            }}
            """)
            
            if result.get("status") != "success":
                raise WorkflowLoadError(f"Failed to store chunk {i}: {result}")
        
        # Load workflow from localStorage into ComfyUI
        time.sleep(0.5)  # Brief pause before loading
        
        result = client.eval_js(f"""
        async () => {{
            try {{
                const app = window.app;
                
                if (!app) {{
                    return {{error: 'ComfyUI app instance not found'}};
                }}
                
                // Reconstruct workflow from chunks
                let workflowStr = '';
                let i = 0;
                while (true) {{
                    const chunk = localStorage.getItem('workflow_chunk_' + i);
                    if (chunk === null) break;
                    workflowStr += chunk;
                    localStorage.removeItem('workflow_chunk_' + i);
                    i++;
                }}
                
                if (!workflowStr) {{
                    return {{error: 'No workflow data found in localStorage'}};
                }}
                
                const workflowData = JSON.parse(workflowStr);
                await app.loadGraphData(workflowData);
                
                return {{loaded: true, chunks_loaded: i}};
            }} catch (e) {{
                return {{error: 'Load failed: ' + e.message}};
            }}
        }}
        """)
        
        if result.get("status") != "success":
            raise WorkflowLoadError(f"JavaScript execution failed: {result}")
        
        result_data = result.get("result", {})
        if "error" in result_data:
            raise WorkflowLoadError(result_data["error"])
        
        time.sleep(2)  # Wait for workflow to fully load
        
        return {
            "success": True,
            "node_count": node_count,
            "chunks": len(chunks),
            "method": "ui_native",
        }
    
    def _load_api(self, client: BrowserClient) -> Dict[str, Any]:
        """Load workflow using HTTP API method."""
        # Placeholder for API method implementation
        raise NotImplementedError("API method not yet implemented")
    
    def _load_hybrid(self, client: BrowserClient) -> Dict[str, Any]:
        """Load workflow using hybrid method."""
        # Placeholder for hybrid method implementation
        raise NotImplementedError("Hybrid method not yet implemented")


@dataclass
class QueueWorkflowAction:
    """
    Queue a workflow for execution in ComfyUI.
    
    This action clicks the "Queue Prompt" button in the ComfyUI UI to queue
    the currently loaded workflow for execution.
    
    Attributes:
        method: Queuing method - "ui_click" (default) or "http_api"
        wait_after_click: Seconds to wait after clicking (default: 1.0)
    """
    method: Literal["ui_click", "http_api"] = "ui_click"
    wait_after_click: float = 1.0
    
    def execute(self, client: BrowserClient) -> Dict[str, Any]:
        """
        Execute the queue workflow action.
        
        Args:
            client: BrowserClient instance
            
        Returns:
            Dict with execution result: {"success": bool, "clicked": bool, ...}
            
        Raises:
            QueueError: If workflow fails to queue
        """
        if self.method == "ui_click":
            return self._queue_ui_click(client)
        elif self.method == "http_api":
            return self._queue_http_api(client)
        else:
            raise ValueError(f"Unknown queue method: {self.method}")
    
    def _queue_ui_click(self, client: BrowserClient) -> Dict[str, Any]:
        """
        Queue workflow by clicking the UI button.
        
        This is the most compatible method as it triggers all UI-side
        event handlers and metadata processing.
        """
        # First, verify the Queue Prompt button exists
        result = client.eval_js("""
        () => {
            const buttons = document.querySelectorAll('button');
            for (let btn of buttons) {
                if (btn.textContent.trim() === 'Queue Prompt') {
                    return {found: true, text: btn.textContent};
                }
            }
            return {found: false};
        }
        """)
        
        if result.get("status") != "success":
            raise QueueError(f"Failed to check for Queue button: {result}")
        
        if not result.get("result", {}).get("found"):
            raise QueueError("Queue Prompt button not found - is ComfyUI loaded?")
        
        # Click the Queue Prompt button
        result = client.eval_js("""
        () => {
            const buttons = document.querySelectorAll('button');
            for (let btn of buttons) {
                if (btn.textContent.trim() === 'Queue Prompt') {
                    btn.click();
                    return {clicked: true};
                }
            }
            return {clicked: false, error: 'Button disappeared'};
        }
        """)
        
        if result.get("status") != "success":
            raise QueueError(f"Failed to click Queue button: {result}")
        
        result_data = result.get("result", {})
        if not result_data.get("clicked"):
            error = result_data.get("error", "Unknown error")
            raise QueueError(f"Failed to click Queue button: {error}")
        
        time.sleep(self.wait_after_click)
        
        return {
            "success": True,
            "clicked": True,
            "method": "ui_click",
        }
    
    def _queue_http_api(self, client: BrowserClient) -> Dict[str, Any]:
        """Queue workflow using HTTP API."""
        # Placeholder for HTTP API method
        raise NotImplementedError("HTTP API method not yet implemented")


@dataclass
class GetPromptIDAction:
    """
    Get the prompt ID of the most recently queued workflow.
    
    This action queries the ComfyUI queue to retrieve the prompt ID of the
    most recently queued workflow.
    
    Attributes:
        timeout: Maximum seconds to wait for prompt ID (default: 10.0)
        check_interval: Seconds between checks (default: 0.5)
    """
    timeout: float = 10.0
    check_interval: float = 0.5
    
    def execute(self, client: BrowserClient) -> Dict[str, Any]:
        """
        Execute the get prompt ID action.
        
        Args:
            client: BrowserClient instance
            
        Returns:
            Dict with result: {"success": bool, "prompt_id": str|None, ...}
        """
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            result = client.eval_js("""
            async () => {
                try {
                    const response = await fetch('/queue');
                    const data = await response.json();
                    
                    // Check pending queue first (most recent)
                    if (data.queue_pending && data.queue_pending.length > 0) {
                        const latest = data.queue_pending[data.queue_pending.length - 1];
                        return {
                            found: true,
                            prompt_id: latest[1],
                            location: 'pending',
                            queue_length: data.queue_pending.length
                        };
                    }
                    
                    // Check running queue
                    if (data.queue_running && data.queue_running.length > 0) {
                        const latest = data.queue_running[data.queue_running.length - 1];
                        return {
                            found: true,
                            prompt_id: latest[1],
                            location: 'running'
                        };
                    }
                    
                    return {found: false, reason: 'Queue is empty'};
                } catch (e) {
                    return {error: e.message};
                }
            }
            """)
            
            if result.get("status") == "success":
                result_data = result.get("result", {})
                
                if result_data.get("found"):
                    return {
                        "success": True,
                        "prompt_id": result_data.get("prompt_id"),
                        "location": result_data.get("location"),
                        "queue_length": result_data.get("queue_length"),
                    }
                
                if "error" in result_data:
                    # Non-fatal error, might just be timing
                    pass
            
            time.sleep(self.check_interval)
        
        # Timeout reached
        return {
            "success": False,
            "prompt_id": None,
            "reason": f"Timeout after {self.timeout}s",
        }
