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
    """Abstract base class for task specifications.
    
    Subclasses must implement:
    - initial_url(): Return the starting URL for the task
    - is_done(): Determine if the task has been completed successfully
    - is_failed(): Optionally override to define custom failure conditions
    """
    goal_description: str = "Base task"

    def initial_url(self) -> str:
        raise NotImplementedError

    def is_done(self, obs: PageObservation, state: TaskState) -> bool:
        raise NotImplementedError

    def is_failed(self, obs: PageObservation, state: TaskState) -> bool:
        # Default: fail if too many steps
        return state.steps > 20
