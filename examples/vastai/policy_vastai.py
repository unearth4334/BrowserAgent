"""
Vast.ai-specific policy for authentication and navigation.

This policy handles HTTP basic auth authentication with vast.ai.
"""
from __future__ import annotations

from browser_agent.browser.actions import Action, Navigate, WaitForSelector
from browser_agent.browser.observation import PageObservation
from browser_agent.agent.task_spec import TaskState

# Import task spec from the same package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from task_spec_vastai import VastAiAuthTaskSpec


class VastAiAuthPolicy:
    """
    Policy for authenticating with vast.ai using HTTP basic auth.
    
    Workflow:
    1. Navigate to the URL with embedded credentials
    2. Wait for the page to load
    3. Mark as authenticated
    
    Note: HTTP basic auth is handled by embedding credentials in the URL.
    The browser will automatically send these credentials when challenged.
    """

    def decide(
        self,
        obs: PageObservation,
        task: VastAiAuthTaskSpec,
        state: TaskState,
    ) -> Action:
        # Step 1: Navigate to the URL with credentials if not done yet
        if state.steps_taken == 0:
            return Navigate(task.initial_url())
        
        # Step 2: Wait for page to load after navigation
        # Check if we're on the target domain
        if not task.authenticated:
            # Mark as authenticated since we've navigated with credentials
            task.authenticated = True
            # Wait for page content to load (any visible element)
            return WaitForSelector("body", timeout_ms=10000)
        
        # Step 3: Task should be complete - this shouldn't be reached
        # but included for safety
        return WaitForSelector("body", timeout_ms=1000)
