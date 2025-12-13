from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from ..browser.observation import PageObservation


@dataclass
class TaskState:
    steps: int = 0
    done: bool = False
    failed: bool = False
    reason: str | None = None


class BaseTaskSpec:
    goal_description: str = "Base task"

    def initial_url(self) -> str:
        raise NotImplementedError

    def is_done(self, obs: PageObservation, state: TaskState) -> bool:
        raise NotImplementedError

    def is_failed(self, obs: PageObservation, state: TaskState) -> bool:
        # Default: fail if too many steps
        return state.steps > 20


@dataclass
class SimpleSearchTaskSpec(BaseTaskSpec):
    """Task: open a search engine and search for a given query."""

    query: str
    goal_description: str = "Perform a simple web search"

    def initial_url(self) -> str:
        # For the prototype, use DuckDuckGo
        return "https://duckduckgo.com/"

    def is_done(self, obs: PageObservation, state: TaskState) -> bool:
        q = self.query.lower()
        return q in obs.title.lower() or q in obs.url.lower()


# Patreon task moved to examples/patreon
# @dataclass
# class PatreonCollectionTaskSpec(BaseTaskSpec):
#     """Task: navigate to Patreon, wait for authentication, then extract collection links."""
# 
#     collection_id: str
#     goal_description: str = "Extract links from Patreon collection"
#     authenticated: bool = False
#     navigated_to_collection: bool = False
#     extracted_links: bool = False
# 
#     def initial_url(self) -> str:
#         return "https://www.patreon.com/"
# 
#     def collection_url(self) -> str:
#         return f"https://www.patreon.com/collection/{self.collection_id}?view=expanded"
# 
#     def is_done(self, obs: PageObservation, state: TaskState) -> bool:
#         # Task is done when we've extracted links from the collection page
#         return (
#             self.authenticated
#             and self.navigated_to_collection
#             and self.extracted_links
#         )


@dataclass
class ComfyUIWorkflowTaskSpec(BaseTaskSpec):
    """Task: execute a ComfyUI workflow with specified parameters."""

    webui_url: str
    workflow_path: str | Path
    parameters: Dict[str, Any] | None = None
    goal_description: str = "Execute ComfyUI workflow"
    
    # State tracking
    workflow_loaded: bool = False
    parameters_set: bool = False
    execution_triggered: bool = False
    execution_completed: bool = False

    def initial_url(self) -> str:
        return self.webui_url

    def is_done(self, obs: PageObservation, state: TaskState) -> bool:
        # Task is done when workflow execution is complete
        return self.execution_completed

    def is_failed(self, obs: PageObservation, state: TaskState) -> bool:
        # Fail if we've exceeded max steps or if we're stuck
        if state.steps > 50:
            return True
        
        # Check if we're on the right page
        if not obs.url.startswith(self.webui_url):
            logger.warning("Not on ComfyUI page: %s", obs.url)
            return False
        
        return False


# Import logger for ComfyUIWorkflowTaskSpec
from ..logging_utils import get_logger
logger = get_logger(__name__)
