"""Simple rule-based policy for basic browser automation tasks."""

from __future__ import annotations

from ..browser.actions import Action, Navigate, Click, Type, WaitForSelector
from ..browser.observation import PageObservation
from .task_spec import BaseTaskSpec, TaskState
from ..logging_utils import get_logger

logger = get_logger(__name__)


class SimpleRuleBasedPolicy:
    """A basic policy for simple browser automation.
    
    This policy provides default behavior:
    - Navigate to initial URL
    - Click on first button if available
    - Fill first input if available
    
    It's meant as a default fallback and for testing.
    For real tasks, use a specific policy (e.g., GrokVisionPolicy).
    """
    
    def decide(
        self,
        obs: PageObservation,
        task: BaseTaskSpec,
        state: TaskState
    ) -> Action:
        """Decide next action based on simple rules."""
        
        # Step 0: Navigate to initial URL
        if state.steps == 0:
            initial_url = task.initial_url()
            logger.info("Navigating to initial URL: %s", initial_url)
            return Navigate(initial_url)
        
        # Wait for page to load
        if state.steps == 1:
            return WaitForSelector("body", timeout_ms=5000)
        
        # Try to interact with first input
        if obs.inputs and state.steps == 2:
            first_input = obs.inputs[0]
            logger.info("Typing into first input: %s", first_input.selector)
            return Type(first_input.selector, "test", press_enter=False)
        
        # Try to click first button
        if obs.buttons and state.steps == 3:
            first_button = obs.buttons[0]
            logger.info("Clicking first button: %s", first_button.selector)
            return Click(first_button.selector)
        
        # Default: wait for selector to give time for page changes
        return WaitForSelector("body", timeout_ms=2000)
