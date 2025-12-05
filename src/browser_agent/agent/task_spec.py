from __future__ import annotations

from dataclasses import dataclass

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
