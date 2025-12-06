from __future__ import annotations

from dataclasses import dataclass
from typing import List

from browser_agent.agent.core import Agent, TaskResult
from browser_agent.agent.task_spec import BaseTaskSpec, TaskState
from browser_agent.browser.actions import Action, Navigate
from browser_agent.browser.observation import PageObservation


@dataclass
class DummyTask(BaseTaskSpec):
    call_count: int = 0

    def initial_url(self) -> str:
        return "https://example.com/"

    def is_done(self, obs: PageObservation, state: TaskState) -> bool:
        # End immediately once we observe the initial URL once
        return obs.url == self.initial_url() and state.steps >= 1


class MockBrowser:
    def __init__(self) -> None:
        self.actions: List[Action] = []
        self.started = False
        self.obs = PageObservation(
            url="about:blank",
            title="Blank",
            buttons=[],
            inputs=[],
        )

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.started = False

    def get_observation(self) -> PageObservation:
        return self.obs

    def perform(self, action: Action) -> None:
        self.actions.append(action)
        if isinstance(action, Navigate):
            # Update observation to reflect navigation
            self.obs = PageObservation(
                url=action.url,
                title="Example",
                buttons=[],
                inputs=[],
            )


def test_agent_with_mock_browser_runs_and_completes():
    agent = Agent(max_steps=5)
    task = DummyTask()
    browser = MockBrowser()

    result: TaskResult = agent.run_task(task, browser)

    assert result.success is True
    assert browser.started is False or browser.started is True  # don't care after stop
    assert any(isinstance(a, Navigate) for a in browser.actions)
