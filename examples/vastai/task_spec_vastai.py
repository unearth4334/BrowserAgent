"""
Vast.ai-specific task specifications.

These task specs define the goals and completion criteria for vast.ai-related tasks.
"""
from __future__ import annotations

from dataclasses import dataclass

from browser_agent.browser.observation import PageObservation
from browser_agent.agent.task_spec import BaseTaskSpec, TaskState


@dataclass
class VastAiAuthTaskSpec(BaseTaskSpec):
    """Task: navigate to vast.ai URL and authenticate using HTTP basic auth."""

    target_url: str
    username: str
    password: str
    goal_description: str = "Authenticate with vast.ai using HTTP basic auth"
    authenticated: bool = False

    def initial_url(self) -> str:
        """Return the URL with embedded credentials for HTTP basic auth."""
        # Parse the URL to extract scheme and the rest
        # Format: https://username:password@domain/path
        if "://" in self.target_url:
            scheme, rest = self.target_url.split("://", 1)
            return f"{scheme}://{self.username}:{self.password}@{rest}"
        else:
            # Fallback if no scheme specified
            return f"https://{self.username}:{self.password}@{self.target_url}"

    def is_done(self, obs: PageObservation, state: TaskState) -> bool:
        """Task is done when we've successfully authenticated and loaded the page."""
        # Check if we're on the target domain and not seeing auth prompts
        # For vast.ai, successful auth means we see the page content
        if not self.authenticated:
            return False
        
        # Simple check: if we have buttons or inputs on the page, we're likely authenticated
        return len(obs.buttons) > 0 or len(obs.inputs) > 0 or "dashboard" in obs.url.lower()

    def is_failed(self, obs: PageObservation, state: TaskState) -> bool:
        """Task fails if we exceed max steps or see auth failure indicators."""
        # Fail after too many steps
        if state.steps_taken > 10:
            return True
        
        # Check for auth failure indicators (e.g., "Unauthorized", "401", etc.)
        if any(keyword in obs.title.lower() for keyword in ["unauthorized", "forbidden", "error"]):
            return True
        
        return False
