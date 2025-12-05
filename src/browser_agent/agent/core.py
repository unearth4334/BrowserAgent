from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..browser.observation import PageObservation
from ..browser.playwright_driver import BrowserController
from .task_spec import BaseTaskSpec, TaskState
from .policy_simple import SimpleRuleBasedPolicy
from ..logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class TaskResult:
    success: bool
    reason: str
    final_observation: PageObservation | None


class Policy(Protocol):
    def decide(
        self, obs: PageObservation, task: BaseTaskSpec, state: TaskState
    ):  # -> Action, but we keep it generic
        ...


class Agent:
    def __init__(self, policy: Policy | None = None, max_steps: int = 20):
        self.policy = policy or SimpleRuleBasedPolicy()  # type: ignore[arg-type]
        self.max_steps = max_steps

    def run_task(
        self, task: BaseTaskSpec, browser: BrowserController
    ) -> TaskResult:
        browser.start()
        state = TaskState()

        obs = browser.get_observation()
        while state.steps < self.max_steps:
            state.steps += 1

            if task.is_done(obs, state):
                state.done = True
                logger.info("Task completed successfully in %d steps", state.steps)
                return TaskResult(True, "Task completed", obs)

            if task.is_failed(obs, state):
                state.failed = True
                logger.warning("Task failed in %d steps", state.steps)
                return TaskResult(False, state.reason or "Task failed", obs)

            action = self.policy.decide(obs, task, state)
            browser.perform(action)
            obs = browser.get_observation()

        logger.warning("Max steps exceeded")
        return TaskResult(False, "Max steps exceeded", obs)
