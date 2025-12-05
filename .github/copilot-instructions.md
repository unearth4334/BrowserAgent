# Browser-Agent AI Development Guide

## Architecture Overview

This is a **layered agent system** for browser automation using Playwright. The agent follows an observe-decide-act loop:

1. **Agent Core** (`agent/core.py`): Orchestrates the loop via `run_task()` - observes browser state, calls policy to decide next action, executes action, checks completion
2. **Policy Layer** (`agent/policy_simple.py`): Decision logic that maps `(Observation, Task, State) -> Action`. Currently rule-based, designed for LLM integration later
3. **Browser Controller** (`browser/playwright_driver.py`): Playwright wrapper - NO AI logic, pure browser operations (navigate, click, type, observe DOM)
4. **Task Specs** (`agent/task_spec.py`): Define task goals via `initial_url()`, `is_done()`, `is_failed()` methods
5. **Observation** (`browser/observation.py`): Structured browser state (URL, title, buttons, inputs) - NOT raw DOM dumps

**Critical separation**: Browser layer is AI-agnostic. All decision logic lives in Policy/Agent layers.

## Development Workflow

### Environment Setup
```bash
# Install in editable mode with dev dependencies
pip install -e .[dev]

# Install Playwright browsers
playwright install chromium
```

### Running the Agent
```bash
# Basic usage (headless DuckDuckGo search)
browser-agent simple-search "query text"

# With custom browser (e.g., Brave)
browser-agent simple-search "query" --browser-exe /usr/bin/brave-browser --no-headless

# Environment-based config
export BROWSER_AGENT_BROWSER_EXE=/usr/bin/brave-browser
export BROWSER_AGENT_HEADLESS=0
```

### Testing Strategy

**Run tests with coverage** (preferred workflow):
```bash
pytest --cov=browser_agent --cov-report=html
```

**Test Structure**:
- `test_*_mock_browser.py`: Unit tests with mock browsers for agent logic
- `test_playwright_driver.py`: Integration tests with real browser (uses static HTML)
- Mock browser pattern: Create `MockBrowser` implementing `BrowserController` protocol, track actions in list, update observations in `perform()`

**Example mock browser** (see `test_agent_mock_browser.py`):
```python
class MockBrowser:
    def __init__(self):
        self.actions = []
        self.obs = PageObservation(...)
    
    def perform(self, action):
        self.actions.append(action)
        if isinstance(action, Navigate):
            self.obs = PageObservation(url=action.url, ...)
```

## Code Patterns & Conventions

### Action Types (Union of dataclasses)
All browser actions are immutable dataclasses in `browser/actions.py`: `Navigate`, `Click`, `Type`, `WaitForSelector`. Use union type `Action` for type hints.

### Protocol-Based Abstractions
- `BrowserController` protocol in `playwright_driver.py` enables testing without real browsers
- `Policy` protocol in `agent/core.py` allows pluggable decision logic
- Use `@runtime_checkable` for protocols that need `isinstance()` checks

### Logging Pattern
```python
from ..logging_utils import get_logger
logger = get_logger(__name__)

# Use throughout: logger.info(), logger.debug(), logger.warning()
```

### TaskSpec Pattern
Extend `BaseTaskSpec` with three methods:
- `initial_url() -> str`: Starting point
- `is_done(obs, state) -> bool`: Success criteria (e.g., query in title/URL)
- `is_failed(obs, state) -> bool`: Failure/timeout conditions

**Example**: `SimpleSearchTaskSpec` succeeds when query appears in title/URL after typing into first input and pressing Enter.

### Configuration
`config.py` uses `Settings.from_env()` pattern:
- `BROWSER_AGENT_BROWSER_EXE`: Custom browser path
- `BROWSER_AGENT_HEADLESS`: "0"/"false"/"no" for headful mode
- CLI args override environment settings

## Adding New Features

### New Action Type
1. Add dataclass to `browser/actions.py` and update `Action` union
2. Handle in `PlaywrightBrowserController.perform()`
3. Add tests in `test_actions.py`

### New Task Type
1. Create dataclass extending `BaseTaskSpec` in `task_spec.py`
2. Implement `initial_url()`, `is_done()`, `is_failed()`
3. Add CLI command in `cli.py` following `simple_search` pattern
4. Write mock browser tests first

### New Policy
1. Implement `decide(obs, task, state) -> Action` method
2. Pass to `Agent(policy=YourPolicy())`
3. Test with various observation scenarios using mock browsers

## Key Files Reference

- `src/browser_agent/cli.py`: Entry point, typer CLI, demonstrates task execution flow
- `src/browser_agent/agent/core.py`: Main agent loop (`run_task`), step counting, completion checking
- `src/browser_agent/browser/playwright_driver.py`: Browser abstraction, DOM observation extraction
- `tests/test_agent_mock_browser.py`: Canonical example of mock-based agent testing
- `docs/PROPOSAL.md`: Original design doc with detailed architecture rationale

## Python Specifics

- **Python 3.11+** required (uses `|` union syntax)
- **Type hints**: Extensive use of `from __future__ import annotations` for forward refs
- **No external AI/LLM dependencies yet**: Policy layer is designed for future LLM integration but currently rule-based
- **Dataclasses**: Preferred over dicts for structured data (observations, actions, configs)
