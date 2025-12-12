from __future__ import annotations

from ..browser.actions import Action, Navigate, WaitForSelector
from ..browser.observation import PageObservation
from .task_spec import ComfyUIWorkflowTaskSpec, TaskState
from .workflow_runner import CanvasWorkflowRunner
from ..logging_utils import get_logger

logger = get_logger(__name__)


class ComfyUIWorkflowPolicy:
    """
    Policy for executing ComfyUI workflows.
    
    This policy uses the CanvasWorkflowRunner to:
    1. Navigate to the WebUI
    2. Load the workflow
    3. Set parameters
    4. Trigger execution
    5. Wait for completion
    """

    def __init__(self):
        self._runner: CanvasWorkflowRunner | None = None

    def decide(
        self,
        obs: PageObservation,
        task: ComfyUIWorkflowTaskSpec,
        state: TaskState,
    ) -> Action:
        """
        Decide the next action based on current state.
        
        This is a simplified policy that relies on the CanvasWorkflowRunner
        to handle the actual workflow execution.
        """
        # If not at the WebUI yet, navigate there
        if not obs.url.startswith(task.webui_url):
            logger.info("Navigating to ComfyUI WebUI: %s", task.webui_url)
            return Navigate(task.webui_url)
        
        # Wait for the page to be ready
        if not task.workflow_loaded:
            logger.info("Waiting for WebUI to be ready...")
            return WaitForSelector("body", timeout_ms=30000)
        
        # This policy is primarily a coordinator
        # The actual workflow execution is handled by CanvasWorkflowRunner
        # through the CLI command
        
        # If we get here, just wait for the page
        return WaitForSelector("body", timeout_ms=5000)
