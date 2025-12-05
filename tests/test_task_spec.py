from browser_agent.agent.task_spec import (
    BaseTaskSpec,
    SimpleSearchTaskSpec,
    TaskState,
)
from browser_agent.browser.observation import PageObservation
import pytest


def test_task_state_defaults():
    state = TaskState()
    assert state.steps == 0
    assert state.done is False
    assert state.failed is False
    assert state.reason is None


def test_task_state_with_values():
    state = TaskState(steps=5, done=True, failed=False, reason="Success")
    assert state.steps == 5
    assert state.done is True
    assert state.failed is False
    assert state.reason == "Success"


def test_base_task_spec_not_implemented():
    task = BaseTaskSpec()
    state = TaskState()
    obs = PageObservation(url="", title="", buttons=[], inputs=[])
    
    with pytest.raises(NotImplementedError):
        task.initial_url()
    
    with pytest.raises(NotImplementedError):
        task.is_done(obs, state)


def test_base_task_spec_is_failed_after_many_steps():
    task = BaseTaskSpec()
    state = TaskState(steps=21)
    obs = PageObservation(url="", title="", buttons=[], inputs=[])
    
    assert task.is_failed(obs, state) is True


def test_base_task_spec_is_not_failed_within_limit():
    task = BaseTaskSpec()
    state = TaskState(steps=10)
    obs = PageObservation(url="", title="", buttons=[], inputs=[])
    
    assert task.is_failed(obs, state) is False


def test_simple_search_task_spec_initial_url():
    task = SimpleSearchTaskSpec(query="hello")
    assert task.initial_url() == "https://duckduckgo.com/"


def test_simple_search_task_spec_is_done_by_url():
    task = SimpleSearchTaskSpec(query="python")
    state = TaskState()
    obs = PageObservation(
        url="https://duckduckgo.com/?q=python",
        title="Search Results",
        buttons=[],
        inputs=[]
    )
    
    assert task.is_done(obs, state) is True


def test_simple_search_task_spec_is_done_by_title():
    task = SimpleSearchTaskSpec(query="python")
    state = TaskState()
    obs = PageObservation(
        url="https://duckduckgo.com/",
        title="python at DuckDuckGo",
        buttons=[],
        inputs=[]
    )
    
    assert task.is_done(obs, state) is True


def test_simple_search_task_spec_is_not_done():
    task = SimpleSearchTaskSpec(query="python")
    state = TaskState()
    obs = PageObservation(
        url="https://duckduckgo.com/",
        title="DuckDuckGo",
        buttons=[],
        inputs=[]
    )
    
    assert task.is_done(obs, state) is False


def test_simple_search_task_spec_case_insensitive():
    task = SimpleSearchTaskSpec(query="PyThOn")
    state = TaskState()
    obs = PageObservation(
        url="https://duckduckgo.com/?q=python",
        title="Search",
        buttons=[],
        inputs=[]
    )
    
    assert task.is_done(obs, state) is True
