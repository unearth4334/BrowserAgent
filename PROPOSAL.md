# Browser-Agent Project Proposal

## 1. Goal & Scope of v0

The initial objective of this project is to develop a **Python-based AI-style agent** capable of automating interactions with a Chromium/Brave browser using Playwright.

### v0 Prototype Capabilities

The agent should be able to:

- Launch a Chromium/Brave browser via Playwright  
- Navigate to a URL  
- Perform a simple interaction (e.g., type text and click a button)  
- Operate within an **agent loop** that:
  - Observes the current browser state  
  - Decides the next action  
  - Executes that action  
- Include **unit tests** and **integration tests** for:
  - Browser wrapper  
  - Agent logic  

The AI component can be rule-based initially but must support plugging in an LLM later.

---

## 2. High-Level Architecture

The system is structured into layered components for modularity and testability.

### **Agent Core**

Responsible for deciding *what to do next*, based on:

- Current task goal  
- Latest browser observation  
- Internal state or interaction history  

The agent exposes:

```python
run_task(task: TaskSpec)
```

---

### **Tool Layer: Browser Controller**

A thin wrapper over Playwright (or Selenium / CDP), responsible for:

- Launching and closing browser instances  
- Navigating pages  
- Querying the DOM and extracting structured data  
- Executing actions such as clicking, typing, waiting, etc.  

There is **no AI logic** at this layer.

---

### **Task / Workflow Layer**

Encapsulates an interaction goal and its constraints.

Example:

- “Open example.com and submit a form”

Defines:

- `is_done(obs)` — success criteria  
- `is_failed(obs)` — abort or error conditions  

---

### **Observation & Memory Layer**

Holds the agent’s structured perception of browser state:

- URL  
- Page title  
- Buttons, inputs  
- Key DOM snippets  

Also stores minimal historical “memory”:

- Past actions  
- Errors or state transitions  

---

### **Config & Logging**

- Configurable browser executable path  
- Headless or headful mode  
- Timeouts and settings  
- Structured event logs and action traces  

---

### **Tests**

- **Unit tests**:
  - Browser controller (with mocks)  
  - Agent decision logic  
- **Integration tests**:
  - Use static local HTML pages for determinism  
  - Validate actual browser interaction  

---

## 2.1 Data Flow (Conceptual)

### **1. User invokes agent**

```bash
python -m browser_agent.cli simple-form --url https://example.org/form
```

### **2. CLI Layer**

- Parses arguments  
- Constructs a `TaskSpec`  
- Instantiates `Agent` and `BrowserController`  

### **3. Agent Loop**

1. `obs = browser.get_observation()`  
2. `action = agent.decide(obs, task_state)`  
3. `browser.perform(action)`  
4. `task_state = task.update(obs, action)`  
5. Decide:
   - If `task.is_done(...)` → SUCCESS  
   - If `task.is_failed(...)` → FAIL  
   - Otherwise → repeat  

### **4. Shutdown**

- Cleanly closes browser  
- Emits results and logs  

---

## 3. Concept of Operations (ConOps)

### Example v0 Task

**Open DuckDuckGo and search for “hello world”.**

### Sequence:

1. User runs CLI:

```bash
browser-agent simple-search "hello world"
```

2. Agent launches Brave/Chromium  
3. Navigates to https://duckduckgo.com  
4. Agent:
   - Finds the search input  
   - Types query  
   - Clicks search or presses ENTER  

5. Agent observes results page  
6. Determines success if:
   - URL or title contains “hello world”  
   - Expected text appears  

Logs include:

- Step sequence  
- Selected actions  
- Timing and error information  

Tests assert:

- No exceptions  
- Expected URL reached  
- Expected results observed  

---

## 4. Tech Choices

| Category | Choice |
|---------|--------|
| Language | Python 3.11+ |
| Browser automation | Playwright |
| Browser | Chromium or Brave (via executable path) |
| CLI | typer (or argparse) |
| Tests | pytest |
| Linting | ruff + black |
| Typing | mypy or pyright |

---

## 5. Project Structure

A clean proposed layout:

```
browser-agent/
├─ pyproject.toml
├─ README.md
├─ .gitignore
├─ src/
│  └─ browser_agent/
│     ├─ __init__.py
│     ├─ config.py
│     ├─ cli.py
│     ├─ agent/
│     │  ├─ __init__.py
│     │  ├─ core.py
│     │  ├─ policy_simple.py
│     │  └─ task_spec.py
│     ├─ browser/
│     │  ├─ __init__.py
│     │  ├─ playwright_driver.py
│     │  ├─ observation.py
│     │  └─ actions.py
│     ├─ logging_utils.py
│     └─ utils/
│        └─ timeouts.py
├─ tests/
│  ├─ conftest.py
│  ├─ test_browser_driver.py
│  ├─ test_agent_policy.py
│  └─ test_end_to_end.py
└─ demo_pages/
   └─ simple_form.html
```

The `src/` layout prevents import ambiguity and follows modern Python packaging conventions.

---

## 6. Minimum Viable Prototype (MVP)

The smallest working version of the system must include:

- `PlaywrightBrowserController` (browser wrapper)  
- `SimpleSearchTaskSpec`  
- `SimpleRuleBasedPolicy`  
- CLI entrypoint:  
  ```bash
  browser-agent simple-search --query "hello world"
  ```

Must successfully:

- Launch Brave/Chromium  
- Navigate  
- Type  
- Click  
- Recognize success criteria  
- Pass the included tests  

Once these are working, the agent loop is validated.

---

## 7. TODO List to Reach v0 Prototype

### **Phase 0 — Scaffolding**

- [ ] Initialize repo  
- [ ] Add `pyproject.toml` with dependencies  
- [ ] Run `playwright install chromium`  
- [ ] Create package scaffolding  
- [ ] Add initial README with goals and architecture  

---

### **Phase 1 — Browser Controller**

- [ ] Implement `actions.py`  
- [ ] Implement `observation.py`  
- [ ] Implement `playwright_driver.py`  
- [ ] Add basic integration test using `simple_form.html`  

---

### **Phase 2 — Tasks & Agent Core**

- [ ] Implement `BaseTaskSpec`  
- [ ] Implement `SimpleSearchTaskSpec`  
- [ ] Implement rule-based policy  
- [ ] Implement `Agent.run_task` loop  
- [ ] Mock-browser tests for policy & agent logic  

---

### **Phase 3 — CLI & Configuration**

- [ ] Implement `config.py`  
- [ ] Implement `cli.py` (simple-search command)  
- [ ] Write CLI integration test  

---

### **Phase 4 — Testing & QA**

- [ ] Add pytest config  
- [ ] Add coverage tooling  
- [ ] Achieve 80%+ test coverage  
- [ ] Optional static analysis (ruff, mypy)  

---

### **Phase 5 — Nice-to-Hhave Enhancements**

- [ ] Generic LLM policy support  
- [ ] JSON logging for replay  
- [ ] Robust DOM role-based selectors  

---

## Summary

This design provides a clean, extensible, production-ready foundation for an “AI agent that controls a browser.” It isolates logic into clear layers, provides testing hooks, and supports expansion toward full LLM-based autonomous browsing.

Below is a copy-pasteable project skeleton: pyproject.toml, package layout, minimal code, and a few tests. It gives you:

A Playwright-based browser controller (Chromium/Brave).

A simple rule-based agent that performs a search.

A CLI command: browser-agent simple-search "hello world".

Initial pytest test coverage (unit-ish) you can grow later.

1. Directory layout

Create this structure:

browser-agent/
├─ pyproject.toml
├─ README.md
├─ .gitignore
├─ src/
│  └─ browser_agent/
│     ├─ __init__.py
│     ├─ config.py
│     ├─ cli.py
│     ├─ logging_utils.py          # (empty stub for now)
│     ├─ browser/
│     │  ├─ __init__.py
│     │  ├─ actions.py
│     │  ├─ observation.py
│     │  └─ playwright_driver.py
│     └─ agent/
│        ├─ __init__.py
│        ├─ core.py
│        ├─ policy_simple.py
│        └─ task_spec.py
└─ tests/
   ├─ conftest.py
   ├─ test_actions.py
   ├─ test_policy_simple.py
   └─ test_agent_mock_browser.py

2. pyproject.toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "browser-agent"
version = "0.1.0"
description = "Prototype AI-style agent controlling a Chromium/Brave browser via Playwright"
requires-python = ">=3.11"
dependencies = [
  "playwright>=1.47.0",
  "typer>=0.12.0",
  "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
  "pytest-cov>=5.0.0",
  "ruff>=0.5.0",
  "mypy>=1.10.0",
]

[project.scripts]
browser-agent = "browser_agent.cli:main"


After installing:

pip install -e .[dev]
playwright install chromium

3. Core package files
src/browser_agent/__init__.py
__all__ = ["__version__"]

__version__ = "0.1.0"

src/browser_agent/config.py
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass
class Settings:
    """Global configuration for the browser agent."""

    browser_executable_path: str | None = None
    headless: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        exe = os.getenv("BROWSER_AGENT_BROWSER_EXE") or None
        headless_raw = os.getenv("BROWSER_AGENT_HEADLESS", "1")

        return cls(
            browser_executable_path=exe,
            headless=headless_raw.lower() not in ("0", "false", "no"),
        )

src/browser_agent/logging_utils.py (stub for later)
from __future__ import annotations

import logging

LOGGER_NAME = "browser_agent"


def get_logger(name: str | None = None) -> logging.Logger:
    logger = logging.getLogger(name or LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

4. Browser layer
src/browser_agent/browser/actions.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass
class Navigate:
    url: str


@dataclass
class Click:
    selector: str


@dataclass
class Type:
    selector: str
    text: str
    press_enter: bool = False


@dataclass
class WaitForSelector:
    selector: str
    timeout_ms: int = 5000


Action = Union[Navigate, Click, Type, WaitForSelector]

src/browser_agent/browser/observation.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ButtonInfo:
    selector: str
    text: str


@dataclass
class InputInfo:
    selector: str
    name: Optional[str]
    value: Optional[str]


@dataclass
class PageObservation:
    url: str
    title: str
    buttons: List[ButtonInfo]
    inputs: List[InputInfo]
    raw_html: Optional[str] = None

src/browser_agent/browser/__init__.py
from .actions import Action, Navigate, Click, Type, WaitForSelector
from .observation import PageObservation, ButtonInfo, InputInfo

__all__ = [
    "Action",
    "Navigate",
    "Click",
    "Type",
    "WaitForSelector",
    "PageObservation",
    "ButtonInfo",
    "InputInfo",
]

src/browser_agent/browser/playwright_driver.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable

from playwright.sync_api import sync_playwright, Browser as PWBrowser, Page

from .actions import Action, Navigate, Click, Type, WaitForSelector
from .observation import PageObservation, ButtonInfo, InputInfo
from ..logging_utils import get_logger

logger = get_logger(__name__)


@runtime_checkable
class BrowserController(Protocol):
    """Abstract browser controller interface."""

    def start(self) -> None:  # pragma: no cover - interface only
        ...

    def stop(self) -> None:  # pragma: no cover - interface only
        ...

    def get_observation(self) -> PageObservation:
        ...

    def perform(self, action: Action) -> None:
        ...


@dataclass
class PlaywrightBrowserController:
    """Playwright-based implementation of BrowserController."""

    executable_path: Optional[str] = None
    headless: bool = True

    _playwright: Optional[object] = field(default=None, init=False)
    _browser: Optional[PWBrowser] = field(default=None, init=False)
    _page: Optional[Page] = field(default=None, init=False)

    def start(self) -> None:
        if self._browser is not None:
            return

        logger.info("Starting Playwright browser (headless=%s)", self.headless)
        self._playwright = sync_playwright().start()
        browser_type = self._playwright.chromium

        launch_args: dict = {"headless": self.headless}
        if self.executable_path:
            launch_args["executable_path"] = self.executable_path

        self._browser = browser_type.launch(**launch_args)
        self._page = self._browser.new_page()
        logger.info("Browser started")

    def stop(self) -> None:
        logger.info("Stopping browser")
        if self._page:
            self._page.close()
            self._page = None
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def get_observation(self) -> PageObservation:
        assert self._page is not None, "Browser not started"
        page = self._page

        buttons: list[ButtonInfo] = []
        for el in page.query_selector_all("button, input[type=submit]"):
            try:
                text = el.inner_text().strip()
            except Exception:
                text = ""
            selector = el.evaluate(
                "el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '')"
            )
            buttons.append(ButtonInfo(selector=selector, text=text))

        inputs: list[InputInfo] = []
        for el in page.query_selector_all(
            "input[type=text], input:not([type]), textarea"
        ):
            selector = el.evaluate(
                "el => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '')"
            )
            name = el.get_attribute("name")
            value = el.get_attribute("value")
            inputs.append(InputInfo(selector=selector, name=name, value=value))

        obs = PageObservation(
            url=page.url,
            title=page.title(),
            buttons=buttons,
            inputs=inputs,
            raw_html=None,
        )
        logger.debug("Observation: %s", obs)
        return obs

    def perform(self, action: Action) -> None:
        assert self._page is not None, "Browser not started"
        page = self._page

        logger.info("Performing action: %s", action)

        if isinstance(action, Navigate):
            page.goto(action.url, wait_until="load")
        elif isinstance(action, Click):
            page.click(action.selector)
        elif isinstance(action, Type):
            page.fill(action.selector, action.text)
            if action.press_enter:
                page.press(action.selector, "Enter")
        elif isinstance(action, WaitForSelector):
            page.wait_for_selector(action.selector, timeout=action.timeout_ms)
        else:  # pragma: no cover - safety
            raise ValueError(f"Unknown action type {action}")

5. Agent layer
src/browser_agent/agent/task_spec.py
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

src/browser_agent/agent/policy_simple.py
from __future__ import annotations

from ..browser.actions import Action, Navigate, Type
from ..browser.observation import PageObservation
from .task_spec import SimpleSearchTaskSpec, TaskState


class SimpleRuleBasedPolicy:
    """
    Minimal rule-based "agent policy".
    Decides next Action based on current observation and task.
    """

    def decide(
        self,
        obs: PageObservation,
        task: SimpleSearchTaskSpec,
        state: TaskState,
    ) -> Action:
        # If not at the search page yet, navigate there
        if not obs.url.startswith(task.initial_url()):
            return Navigate(task.initial_url())

        # If any input already contains the query, just press Enter on it
        for inp in obs.inputs:
            if inp.value and task.query.lower() in inp.value.lower():
                return Type(selector=inp.selector, text=inp.value, press_enter=True)

        # Otherwise, type into the first available input and press Enter
        if obs.inputs:
            selector = obs.inputs[0].selector
            return Type(selector=selector, text=task.query, press_enter=True)

        # Fallback: refresh the initial URL
        return Navigate(task.initial_url())

src/browser_agent/agent/core.py
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

src/browser_agent/agent/__init__.py
from .core import Agent, TaskResult
from .task_spec import BaseTaskSpec, SimpleSearchTaskSpec, TaskState

__all__ = ["Agent", "TaskResult", "BaseTaskSpec", "SimpleSearchTaskSpec", "TaskState"]

6. CLI
src/browser_agent/cli.py
from __future__ import annotations

import typer
from rich import print

from .config import Settings
from .browser.playwright_driver import PlaywrightBrowserController
from .agent.core import Agent
from .agent.task_spec import SimpleSearchTaskSpec

app = typer.Typer(help="Browser agent CLI")


@app.command()
def simple_search(
    query: str = typer.Argument(..., help="Search query string"),
    headless: bool = typer.Option(
        True, "--headless/--no-headless", help="Run browser in headless mode"
    ),
    browser_exe: str | None = typer.Option(
        None, help="Path to Brave/Chromium executable (optional)"
    ),
):
    """
    Run the simple search demo task.

    Example:
        browser-agent simple-search "hello world"
    """
    env_settings = Settings.from_env()
    settings = Settings(
        browser_executable_path=browser_exe or env_settings.browser_executable_path,
        headless=headless if browser_exe is not None else env_settings.headless,
    )

    controller = PlaywrightBrowserController(
        executable_path=settings.browser_executable_path,
        headless=settings.headless,
    )
    task = SimpleSearchTaskSpec(query=query)
    agent = Agent()

    try:
        result = agent.run_task(task, controller)
        if result.success:
            print(f"[green]Success:[/green] {result.reason}")
            if result.final_observation:
                print(f"Final URL: {result.final_observation.url}")
                print(f"Title: {result.final_observation.title}")
        else:
            print(f"[red]Failure:[/red] {result.reason}")
    finally:
        controller.stop()


def main() -> None:
    app()


if __name__ == "__main__":
    main()

7. Tests
tests/conftest.py
# For now, empty; you can add shared fixtures later.

tests/test_actions.py
from browser_agent.browser.actions import Navigate, Click, Type, WaitForSelector


def test_action_dataclasses_init():
    n = Navigate(url="https://example.com")
    c = Click(selector="#btn")
    t = Type(selector="#input", text="hello", press_enter=True)
    w = WaitForSelector(selector="#ready", timeout_ms=1234)

    assert n.url == "https://example.com"
    assert c.selector == "#btn"
    assert t.text == "hello"
    assert t.press_enter is True
    assert w.timeout_ms == 1234

tests/test_policy_simple.py
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

tests/test_agent_mock_browser.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from browser_agent.agent.core import Agent, TaskResult
from browser_agent.agent.task_spec import BaseTaskSpec, TaskState
from browser_agent.browser.actions import Action, Navigate
from browser_agent.browser.observation import PageObservation, ButtonInfo, InputInfo


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

8. Running it

From the project root:

# Install in editable mode with dev deps
pip install -e .[dev]

# Install Playwright’s Chromium driver
playwright install chromium

# Run tests
pytest

# Try the demo agent (will use Chromium; to use Brave, pass --browser-exe)
browser-agent simple-search "hello world" --headless


To point at Brave:

browser-agent simple-search "hello world" --browser-exe "/usr/bin/brave-browser"


(or whatever path Brave uses on your system).

This gives you a working end-to-end skeleton:

You already have an “agent → browser → page → observation → new action” loop.

You can now:

Swap in different TaskSpecs,

Add richer Observations (roles, ARIA labels, etc.),

Replace SimpleRuleBasedPolicy with an LLM-backed policy while keeping the same interfaces.