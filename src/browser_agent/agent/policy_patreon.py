from __future__ import annotations

from ..browser.actions import Action, Navigate, WaitForUser, ExtractLinks, WaitForSelector
from ..browser.observation import PageObservation
from .task_spec import PatreonCollectionTaskSpec, TaskState
import time


class PatreonCollectionPolicy:
    """
    Policy for extracting links from a Patreon collection.
    
    Workflow:
    1. Navigate to patreon.com
    2. Wait for user to authenticate
    3. Navigate to collection page
    4. Extract links matching the pattern
    """

    def decide(
        self,
        obs: PageObservation,
        task: PatreonCollectionTaskSpec,
        state: TaskState,
    ) -> Action:
        # Step 1: Navigate to Patreon home if not there yet
        if not task.authenticated and not obs.url.startswith("https://www.patreon.com"):
            return Navigate(task.initial_url())

        # Step 2: Wait for user to authenticate
        if not task.authenticated and obs.url.startswith("https://www.patreon.com"):
            # Mark as authenticated after user confirms
            task.authenticated = True
            return WaitForUser(
                "Please log in to Patreon, then press Enter to continue..."
            )

        # Step 3: Navigate to the collection page
        if task.authenticated and not task.navigated_to_collection:
            task.navigated_to_collection = True
            return Navigate(task.collection_url())

        # Step 4: Wait for page content to load, then extract links
        if task.authenticated and task.navigated_to_collection and not task.extracted_links:
            # Try to wait for any links to appear on the page
            # Use a broad selector first to ensure content is loaded
            if state.steps == 4:  # First time on collection page
                return WaitForSelector("a[href*='/posts/']", timeout_ms=10000)
            else:
                # Now extract links - try multiple patterns
                task.extracted_links = True
                # Pattern 1: Links with collection parameter
                # Pattern 2: Any post links (fallback)
                return ExtractLinks(
                    f'a[href*="/posts/"][href*="collection={task.collection_id}"]'
                )

        # Fallback: navigate to initial URL
        return Navigate(task.initial_url())
