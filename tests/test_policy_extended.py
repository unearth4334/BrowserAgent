from browser_agent.agent.policy_simple import SimpleRuleBasedPolicy
from browser_agent.agent.task_spec import SimpleSearchTaskSpec, TaskState
from browser_agent.browser.observation import PageObservation, InputInfo
from browser_agent.browser.actions import Navigate, Type


def test_policy_with_query_already_in_input():
    """Test that policy presses enter if query is already in input."""
    policy = SimpleRuleBasedPolicy()
    task = SimpleSearchTaskSpec(query="hello world")
    state = TaskState()
    inputs = [InputInfo(selector="input#search", name="q", value="hello world")]
    obs = PageObservation(
        url=task.initial_url(),
        title="DuckDuckGo",
        buttons=[],
        inputs=inputs
    )
    
    action = policy.decide(obs, task, state)
    assert isinstance(action, Type)
    assert action.text == "hello world"
    assert action.press_enter is True


def test_policy_with_partial_query_in_input():
    """Test that policy recognizes partial query match."""
    policy = SimpleRuleBasedPolicy()
    task = SimpleSearchTaskSpec(query="hello")
    state = TaskState()
    inputs = [InputInfo(selector="input#search", name="q", value="hello world")]
    obs = PageObservation(
        url=task.initial_url(),
        title="DuckDuckGo",
        buttons=[],
        inputs=inputs
    )
    
    action = policy.decide(obs, task, state)
    assert isinstance(action, Type)
    assert action.press_enter is True


def test_policy_no_inputs_available():
    """Test fallback when no inputs are available."""
    policy = SimpleRuleBasedPolicy()
    task = SimpleSearchTaskSpec(query="hello")
    state = TaskState()
    obs = PageObservation(
        url=task.initial_url(),
        title="DuckDuckGo",
        buttons=[],
        inputs=[]
    )
    
    action = policy.decide(obs, task, state)
    assert isinstance(action, Navigate)
    assert action.url == task.initial_url()


def test_policy_case_insensitive_matching():
    """Test that query matching is case insensitive."""
    policy = SimpleRuleBasedPolicy()
    task = SimpleSearchTaskSpec(query="HELLO")
    state = TaskState()
    inputs = [InputInfo(selector="input#search", name="q", value="hello")]
    obs = PageObservation(
        url=task.initial_url(),
        title="DuckDuckGo",
        buttons=[],
        inputs=inputs
    )
    
    action = policy.decide(obs, task, state)
    assert isinstance(action, Type)
    assert action.press_enter is True
