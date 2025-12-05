from browser_agent.agent.policy_simple import SimpleRuleBasedPolicy
from browser_agent.agent.task_spec import SimpleSearchTaskSpec, TaskState
from browser_agent.browser.observation import PageObservation, InputInfo, ButtonInfo
from browser_agent.browser.actions import Navigate, Type


def _make_obs(url: str, inputs: list[InputInfo] | None = None) -> PageObservation:
    return PageObservation(
        url=url,
        title="",
        buttons=[],
        inputs=inputs or [],
    )


def test_policy_navigates_to_initial_url_if_not_there():
    policy = SimpleRuleBasedPolicy()
    task = SimpleSearchTaskSpec(query="hello")
    state = TaskState()
    obs = _make_obs(url="https://other-site.com")

    action = policy.decide(obs, task, state)
    assert isinstance(action, Navigate)
    assert action.url == task.initial_url()


def test_policy_types_query_into_first_input():
    policy = SimpleRuleBasedPolicy()
    task = SimpleSearchTaskSpec(query="hello")
    state = TaskState()
    inputs = [InputInfo(selector="input#search", name="q", value="")]
    obs = _make_obs(url=task.initial_url(), inputs=inputs)

    action = policy.decide(obs, task, state)
    assert isinstance(action, Type)
    assert action.text == "hello"
    assert action.press_enter is True
