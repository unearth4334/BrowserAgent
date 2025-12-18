"""Mock BrowserClient for testing ComfyUI actions."""

from typing import Any, Dict, List
import json


class MockBrowserClient:
    """
    Mock BrowserClient for testing ComfyUI actions without a real browser.
    
    This mock simulates ComfyUI responses and tracks all JavaScript evaluations
    for verification in tests.
    """
    
    def __init__(self):
        """Initialize mock client."""
        self.eval_js_calls: List[str] = []
        self.goto_calls: List[str] = []
        self.ready_called: bool = False
        
        # Simulated state
        self.local_storage: Dict[str, str] = {}
        self.workflow_loaded: bool = False
        self.queue_clicked: bool = False
        self.queued_prompts: List[str] = []
        
        # Configuration
        self.simulate_errors: bool = False
        self.error_on_eval: bool = False
        self.error_on_queue_button: bool = False
    
    def ready(self) -> Dict[str, Any]:
        """Simulate ready call."""
        self.ready_called = True
        return {"status": "success"}
    
    def goto(self, url: str) -> Dict[str, Any]:
        """Simulate navigation."""
        self.goto_calls.append(url)
        return {"status": "success", "url": url}
    
    def eval_js(self, code: str) -> Dict[str, Any]:
        """
        Simulate JavaScript evaluation.
        
        This mock inspects the JavaScript code and returns appropriate
        simulated responses based on what the code is trying to do.
        """
        self.eval_js_calls.append(code)
        
        if self.error_on_eval:
            return {"status": "error", "error": "Simulated eval error"}
        
        # Detect localStorage.setItem calls
        if "localStorage.setItem" in code:
            # Extract chunk number and store it
            if "workflow_chunk_" in code:
                # Simple pattern matching for chunk storage
                import re
                match = re.search(r"workflow_chunk_(\d+)", code)
                if match:
                    chunk_num = match.group(1)
                    self.local_storage[f"workflow_chunk_{chunk_num}"] = "mock_data"
                return {
                    "status": "success",
                    "result": {"stored": True, "chunk": int(chunk_num)}
                }
        
        # Detect workflow loading (app.loadGraphData)
        if "app.loadGraphData" in code and "localStorage.getItem" in code:
            # Simulate successful workflow loading
            chunks_count = len([k for k in self.local_storage.keys() if k.startswith("workflow_chunk_")])
            self.workflow_loaded = True
            self.local_storage.clear()  # Simulate removal after loading
            return {
                "status": "success",
                "result": {"loaded": True, "chunks_loaded": chunks_count}
            }
        
        # Detect Queue Prompt button check
        if "Queue Prompt" in code and "querySelectorAll('button')" in code:
            if "found" in code and not "click()" in code:
                # Button existence check
                if self.error_on_queue_button:
                    return {"status": "success", "result": {"found": False}}
                return {"status": "success", "result": {"found": True, "text": "Queue Prompt"}}
            
            if "click()" in code:
                # Button click
                if self.error_on_queue_button:
                    return {"status": "success", "result": {"clicked": False, "error": "Button not found"}}
                
                self.queue_clicked = True
                # Simulate prompt ID generation
                prompt_id = f"test-prompt-{len(self.queued_prompts) + 1:04d}"
                self.queued_prompts.append(prompt_id)
                return {"status": "success", "result": {"clicked": True}}
        
        # Detect queue status check
        if "fetch('/queue')" in code:
            if self.queued_prompts:
                # Return most recent prompt
                return {
                    "status": "success",
                    "result": {
                        "found": True,
                        "prompt_id": self.queued_prompts[-1],
                        "location": "pending",
                        "queue_length": len(self.queued_prompts)
                    }
                }
            else:
                return {
                    "status": "success",
                    "result": {"found": False, "reason": "Queue is empty"}
                }
        
        # Detect ComfyUI app check
        if "window.app" in code and "loadGraphData" not in code:
            return {
                "status": "success",
                "result": {"app_exists": True}
            }
        
        # Default: return success with empty result
        return {"status": "success", "result": {}}
    
    def reset(self):
        """Reset mock state for new test."""
        self.eval_js_calls.clear()
        self.goto_calls.clear()
        self.ready_called = False
        self.local_storage.clear()
        self.workflow_loaded = False
        self.queue_clicked = False
        self.queued_prompts.clear()
        self.simulate_errors = False
        self.error_on_eval = False
        self.error_on_queue_button = False
