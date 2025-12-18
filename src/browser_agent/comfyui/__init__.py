"""
ComfyUI integration package for browser_agent.

This package provides high-level abstractions for automating ComfyUI workflows
through browser automation.
"""

from browser_agent.comfyui.actions.workflow import (
    LoadWorkflowAction,
    QueueWorkflowAction,
    GetPromptIDAction,
)
from browser_agent.comfyui.exceptions import (
    ComfyUIError,
    WorkflowLoadError,
    QueueError,
)

__version__ = "0.1.0"

__all__ = [
    "LoadWorkflowAction",
    "QueueWorkflowAction",
    "GetPromptIDAction",
    "ComfyUIError",
    "WorkflowLoadError",
    "QueueError",
]
