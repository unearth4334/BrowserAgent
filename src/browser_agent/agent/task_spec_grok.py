"""Grok-specific task specifications for downloading images and videos from Grok.

This module provides task specs for interacting with Grok's imagine/favorites
tileview through a noVNC container to bypass CAPTCHA restrictions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from ..browser.observation import PageObservation
from .task_spec import BaseTaskSpec, TaskState


@dataclass
class GrokDownloadTaskSpec(BaseTaskSpec):
    """Task for downloading images/videos from Grok's tileview via noVNC.
    
    This task:
    1. Navigates to the noVNC viewer (containing the Grok browser session)
    2. Uses screenshot-based vision to identify tiles
    3. Clicks on tiles to download images/videos
    4. Tracks downloaded items
    
    Attributes:
        novnc_url: URL of the noVNC viewer (e.g., http://localhost:6080/vnc.html)
        download_dir: Local directory to save downloaded images/videos
        max_downloads: Maximum number of items to download (0 = unlimited)
        target_type: Type of content to download ("image", "video", or "both")
    """
    novnc_url: str = "http://localhost:6080/vnc.html"
    download_dir: str = "./grok_downloads"
    max_downloads: int = 0  # 0 = unlimited
    target_type: str = "both"  # "image", "video", or "both"
    
    goal_description: str = "Download images/videos from Grok via noVNC"
    
    def __post_init__(self):
        # Create download directory if it doesn't exist
        os.makedirs(self.download_dir, exist_ok=True)
    
    def initial_url(self) -> str:
        """Start at the noVNC viewer URL."""
        return self.novnc_url
    
    def is_done(self, obs: PageObservation, state: TaskState) -> bool:
        """Task is done when we've downloaded the target number of items.
        
        For now, this is a placeholder - actual completion detection will
        be based on tracking downloaded items in the policy/state.
        """
        # TODO: Implement actual completion tracking based on downloads
        return False
    
    def is_failed(self, obs: PageObservation, state: TaskState) -> bool:
        """Fail if we can't reach the noVNC viewer or exceed step limit."""
        # Check if we're not on the expected page
        if not obs.url.startswith(self.novnc_url.split('/vnc.html')[0]):
            return True
        
        # Fail after more steps than default
        return state.steps > 100


@dataclass
class GrokNavigateTaskSpec(BaseTaskSpec):
    """Simple task to navigate to Grok pages within noVNC.
    
    This is a helper task for setting up the Grok session manually
    before running automated downloads.
    
    Attributes:
        novnc_url: URL of the noVNC viewer
        target_grok_page: Which Grok page to navigate to ("imagine" or "favorites")
    """
    novnc_url: str = "http://localhost:6080/vnc.html"
    target_grok_page: str = "favorites"  # "imagine" or "favorites"
    
    goal_description: str = "Navigate to Grok page in noVNC"
    
    def initial_url(self) -> str:
        """Start at the noVNC viewer URL."""
        return self.novnc_url
    
    def is_done(self, obs: PageObservation, state: TaskState) -> bool:
        """For this task, we just wait for user confirmation.
        
        The user should manually navigate to the target page in the VNC browser,
        then the agent will wait for confirmation.
        """
        # This will be handled by WaitForUser actions
        return state.done
    
    def is_failed(self, obs: PageObservation, state: TaskState) -> bool:
        """Fail if we can't reach the noVNC viewer."""
        if not obs.url.startswith(self.novnc_url.split('/vnc.html')[0]):
            return True
        return state.steps > 10
