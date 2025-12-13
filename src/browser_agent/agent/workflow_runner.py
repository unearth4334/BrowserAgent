from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from ..browser.actions import (
    Navigate,
    WaitForSelector,
    Click,
    ExecuteJS,
    UploadFile,
    SetSlider,
    SelectOption,
    Type,
)
from ..browser.playwright_driver import BrowserController
from ..logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class WorkflowParameter:
    """Represents a parameter to be set in a workflow."""
    node_id: str
    field_name: str
    value: Any


class CanvasWorkflowRunner:
    """
    Runner for executing ComfyUI canvas workflows.
    
    This class handles:
    - Loading workflow JSON files
    - Setting workflow parameters
    - Triggering workflow execution
    - Waiting for completion
    """

    def __init__(
        self,
        browser: BrowserController,
        webui_url: str,
        completion_check_interval: float = 2.0,
        max_wait_time: float = 600.0,
    ):
        """
        Initialize the workflow runner.
        
        Args:
            browser: Browser controller instance
            webui_url: URL of the ComfyUI WebUI
            completion_check_interval: Time in seconds between completion checks
            max_wait_time: Maximum time in seconds to wait for workflow completion
        """
        self.browser = browser
        self.webui_url = webui_url
        self.completion_check_interval = completion_check_interval
        self.max_wait_time = max_wait_time
        self._workflow_data: Optional[Dict[str, Any]] = None
        self._parameters: list[WorkflowParameter] = []

    def load_workflow(self, workflow_path: str | Path) -> None:
        """
        Load a workflow from a JSON file.
        
        Args:
            workflow_path: Path to the workflow JSON file
        """
        workflow_path = Path(workflow_path)
        
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
        
        logger.info("Loading workflow from: %s", workflow_path)
        
        with open(workflow_path, "r") as f:
            self._workflow_data = json.load(f)
        
        logger.info("Workflow loaded successfully with %d nodes", len(self._workflow_data))

    def set_parameter(self, node_id: str, field_name: str, value: Any) -> None:
        """
        Set a parameter value for a workflow node.
        
        Args:
            node_id: ID of the node in the workflow
            field_name: Name of the field/parameter to set
            value: Value to set
        """
        logger.info("Setting parameter: node=%s, field=%s, value=%s", node_id, field_name, value)
        self._parameters.append(WorkflowParameter(node_id, field_name, value))

    def run(self) -> None:
        """
        Execute the workflow.
        
        This method:
        1. Navigates to the WebUI
        2. Loads the workflow
        3. Applies parameters
        4. Triggers execution
        """
        if self._workflow_data is None:
            raise RuntimeError("No workflow loaded. Call load_workflow() first.")
        
        logger.info("Navigating to WebUI: %s", self.webui_url)
        self.browser.perform(Navigate(self.webui_url))
        
        # Wait for the page to be ready
        logger.info("Waiting for WebUI to be ready...")
        self.browser.perform(WaitForSelector("body", timeout_ms=30000))
        
        # Load the workflow via JavaScript injection
        logger.info("Loading workflow into ComfyUI...")
        workflow_json = json.dumps(self._workflow_data)
        load_workflow_script = f"""
        (function() {{
            try {{
                const workflow = {workflow_json};
                if (typeof app !== 'undefined' && app.loadGraphData) {{
                    app.loadGraphData(workflow);
                    return 'Workflow loaded successfully';
                }} else {{
                    return 'ERROR: app.loadGraphData not available';
                }}
            }} catch (e) {{
                return 'ERROR: ' + e.message;
            }}
        }})();
        """
        self.browser.perform(ExecuteJS(load_workflow_script))
        
        # Apply parameters
        logger.info("Applying %d parameter(s)...", len(self._parameters))
        for param in self._parameters:
            self._apply_parameter(param)
        
        # Trigger workflow execution
        logger.info("Triggering workflow execution...")
        self._trigger_execution()

    def _apply_parameter(self, param: WorkflowParameter) -> None:
        """Apply a parameter to the workflow."""
        # This is a simplified implementation
        # In a real scenario, you'd need to:
        # 1. Find the node in the UI
        # 2. Click on it to open settings
        # 3. Find the specific field
        # 4. Set the value
        
        logger.info("Applying parameter: %s.%s = %s", param.node_id, param.field_name, param.value)
        
        # Example: Set parameter via JavaScript
        set_param_script = f"""
        (function() {{
            try {{
                if (typeof app !== 'undefined' && app.graph) {{
                    const node = app.graph.getNodeById({param.node_id});
                    if (node && node.widgets) {{
                        const widget = node.widgets.find(w => w.name === '{param.field_name}');
                        if (widget) {{
                            widget.value = {json.dumps(param.value)};
                            return 'Parameter set successfully';
                        }}
                    }}
                }}
                return 'ERROR: Could not set parameter';
            }} catch (e) {{
                return 'ERROR: ' + e.message;
            }}
        }})();
        """
        self.browser.perform(ExecuteJS(set_param_script))

    def _trigger_execution(self) -> None:
        """Trigger workflow execution by clicking the Queue button."""
        # Try to find and click the Queue/Run button
        # ComfyUI typically has a "Queue Prompt" button
        try:
            # Try multiple possible selectors
            queue_selectors = [
                "button:has-text('Queue Prompt')",
                "button#queue-button",
                "button[title*='Queue']",
                ".comfy-queue-btn",
            ]
            
            for selector in queue_selectors:
                try:
                    logger.debug("Trying queue button selector: %s", selector)
                    self.browser.perform(Click(selector))
                    logger.info("Workflow queued successfully")
                    return
                except Exception as e:
                    logger.debug("Selector %s failed: %s", selector, e)
                    continue
            
            # Fallback: Try JavaScript
            logger.warning("Could not find queue button, trying JavaScript fallback")
            queue_script = """
            (function() {
                if (typeof app !== 'undefined' && app.queuePrompt) {
                    app.queuePrompt();
                    return 'Queued via JS';
                }
                return 'ERROR: queuePrompt not available';
            })();
            """
            self.browser.perform(ExecuteJS(queue_script))
            
        except Exception as e:
            logger.error("Failed to trigger workflow execution: %s", e)
            raise RuntimeError("Could not trigger workflow execution") from e

    def wait_for_completion(self) -> bool:
        """
        Wait for workflow execution to complete.
        
        Returns:
            True if workflow completed successfully, False if timeout
        """
        logger.info("Waiting for workflow completion (max %d seconds)...", self.max_wait_time)
        
        start_time = time.time()
        
        while (time.time() - start_time) < self.max_wait_time:
            # Check if workflow is complete via JavaScript
            check_script = """
            (function() {
                if (typeof app !== 'undefined' && app.ui && app.ui.queue) {
                    const running = app.ui.queue.running || 0;
                    const pending = app.ui.queue.pending || 0;
                    return { running: running, pending: pending };
                }
                return { running: 0, pending: 0 };
            })();
            """
            
            try:
                self.browser.perform(ExecuteJS(check_script))
                result = self.browser.get_last_js_result()
                
                # If both running and pending are 0, workflow is complete
                if isinstance(result, dict) and result.get("running") == 0 and result.get("pending") == 0:
                    elapsed = time.time() - start_time
                    logger.info("Workflow completed in %.2f seconds", elapsed)
                    return True
                
                logger.debug("Workflow status: %s", result)
                
            except Exception as e:
                logger.warning("Error checking workflow status: %s", e)
            
            time.sleep(self.completion_check_interval)
        
        logger.warning("Workflow did not complete within %d seconds", self.max_wait_time)
        return False
