"""
Patreon-specific task specifications.

These task specs define the goals and completion criteria for Patreon-related tasks.
"""
from __future__ import annotations

from dataclasses import dataclass

from browser_agent.browser.observation import PageObservation
from browser_agent.agent.task_spec import BaseTaskSpec, TaskState


@dataclass
class PatreonCollectionTaskSpec(BaseTaskSpec):
    """Task: navigate to Patreon, wait for authentication, then extract collection links."""

    collection_id: str
    goal_description: str = "Extract links from Patreon collection"
    authenticated: bool = False
    navigated_to_collection: bool = False
    extracted_links: bool = False

    def initial_url(self) -> str:
        return "https://www.patreon.com/"

    def collection_url(self) -> str:
        return f"https://www.patreon.com/collection/{self.collection_id}?view=expanded"

    def is_done(self, obs: PageObservation, state: TaskState) -> bool:
        # Task is done when we've extracted links from the collection page
        return (
            self.authenticated
            and self.navigated_to_collection
            and self.extracted_links
        )
