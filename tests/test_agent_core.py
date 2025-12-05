from browser_agent.agent.core import Agent, TaskResult
from browser_agent.agent.task_spec import TaskState, SimpleSearchTaskSpec
from browser_agent.browser.observation import PageObservation
from browser_agent.browser.actions import Navigate, Type
from browser_agent.agent.policy_simple import SimpleRuleBasedPolicy


def test_task_result():
    obs = PageObservation(url="https://example.com", title="Example", buttons=[], inputs=[])
    result = TaskResult(success=True, reason="Completed", final_observation=obs)
    
    assert result.success is True
    assert result.reason == "Completed"
    assert result.final_observation == obs


def test_task_result_no_observation():
    result = TaskResult(success=False, reason="Failed", final_observation=None)
    
    assert result.success is False
    assert result.reason == "Failed"
    assert result.final_observation is None


def test_agent_initialization_with_default_policy():
    agent = Agent()
    assert isinstance(agent.policy, SimpleRuleBasedPolicy)
    assert agent.max_steps == 20


def test_agent_initialization_with_custom_max_steps():
    agent = Agent(max_steps=10)
    assert agent.max_steps == 10


def test_agent_max_steps_exceeded():
    """Test that agent fails when max steps is exceeded."""
    from typing import List
    from dataclasses import dataclass
    from browser_agent.agent.task_spec import BaseTaskSpec
    from browser_agent.browser.actions import Action
    
    @dataclass
    class NeverDoneTask(BaseTaskSpec):
        def initial_url(self) -> str:
            return "https://example.com/"
        
        def is_done(self, obs: PageObservation, state: TaskState) -> bool:
            return False  # Never done
        
        def is_failed(self, obs: PageObservation, state: TaskState) -> bool:
            return False  # Never fails on its own
    
    class MockBrowser:
        def __init__(self):
            self.actions: List[Action] = []
            self.started = False
        
        def start(self):
            self.started = True
        
        def stop(self):
            self.started = False
        
        def get_observation(self) -> PageObservation:
            return PageObservation(
                url="https://example.com/",
                title="Example",
                buttons=[],
                inputs=[]
            )
        
        def perform(self, action: Action):
            self.actions.append(action)
    
    agent = Agent(max_steps=3)
    task = NeverDoneTask()
    browser = MockBrowser()
    
    result = agent.run_task(task, browser)
    
    assert result.success is False
    assert result.reason == "Max steps exceeded"
    assert len(browser.actions) == 3


def test_agent_task_failed():
    """Test that agent detects task failure."""
    from typing import List
    from dataclasses import dataclass
    from browser_agent.agent.task_spec import BaseTaskSpec
    from browser_agent.browser.actions import Action
    
    @dataclass
    class FailingTask(BaseTaskSpec):
        def initial_url(self) -> str:
            return "https://example.com/"
        
        def is_done(self, obs: PageObservation, state: TaskState) -> bool:
            return False
        
        def is_failed(self, obs: PageObservation, state: TaskState) -> bool:
            return state.steps >= 2  # Fail after 2 steps
    
    class MockBrowser:
        def __init__(self):
            self.actions: List[Action] = []
        
        def start(self):
            pass
        
        def stop(self):
            pass
        
        def get_observation(self) -> PageObservation:
            return PageObservation(
                url="https://example.com/",
                title="Example",
                buttons=[],
                inputs=[]
            )
        
        def perform(self, action: Action):
            self.actions.append(action)
    
    agent = Agent(max_steps=10)
    task = FailingTask()
    browser = MockBrowser()
    
    result = agent.run_task(task, browser)
    
    assert result.success is False
    assert result.reason == "Task failed"
    assert len(browser.actions) == 1  # Only one action before failure detected
