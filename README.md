# Browser-Agent Core Framework

A Python-based browser automation framework with a layered agent architecture using Playwright. Provides reusable infrastructure for building browser automation applications.

## Features

- **Browser Server/Client Architecture**: Persistent browser sessions with socket-based communication
- **Protocol-Based Design**: `BrowserController` and `Policy` protocols for extensibility
- **Multi-Browser Support**: Chromium, Brave, Firefox, WebKit via Playwright
- **Headless Mode**: Full support for containerized environments (Docker, cloud instances)
- **Agent Framework**: Observe-decide-act loop with pluggable policy system
- **Interactive Session**: REPL for debugging and manual browser control
- **Comprehensive Test Infrastructure**: Mock browser patterns, fixtures, and integration tests

## Installation

```bash
pip install -e .[dev]
playwright install chromium
```

## Usage

### Interactive Browser Session

Start a persistent browser session with a REPL for debugging and manual interaction:

```bash
# Start at a specific URL
browser-agent interactive https://example.com --browser-exe /usr/bin/brave-browser

# Or start without a URL
browser-agent interactive --browser-exe /usr/bin/brave-browser
```

**Available commands:** `goto`, `extract`, `click`, `type`, `wait`, `info`, `links`, `save`, `html`, `eval`, `buttons`, `inputs`, `help`, `quit`

See [docs/INTERACTIVE_GUIDE.md](docs/INTERACTIVE_GUIDE.md) for full documentation.

### Browser Server Mode

Run a persistent browser server that accepts commands over a socket:

```python
from browser_agent.network.browser_server import BrowserServer

server = BrowserServer(port=9999)
server.run()
```

Connect from a client:

```python
from browser_agent.network.browser_client import BrowserClient

client = BrowserClient(host="localhost", port=9999)
client.navigate("https://example.com")
obs = client.observe()
```

See [docs/BROWSER_SERVER_GUIDE.md](docs/BROWSER_SERVER_GUIDE.md) for details.

## Configuration

BrowserAgent supports extensive configuration via environment variables:

```bash
# Browser settings
export BROWSER_AGENT_BROWSER_EXE=/usr/bin/brave-browser  # Custom browser path
export BROWSER_AGENT_HEADLESS=1                           # 1=headless, 0=headful
export BROWSER_AGENT_BROWSER_TYPE=chromium                # chromium, firefox, or webkit

# Timeout settings (in milliseconds)
export BROWSER_AGENT_LAUNCH_TIMEOUT=15000
export BROWSER_AGENT_NAVIGATION_TIMEOUT=30000

# Wait strategy for navigation
export BROWSER_AGENT_DEFAULT_WAIT=load                    # load, domcontentloaded, or networkidle

# Extra launch arguments (comma-separated)
export BROWSER_AGENT_EXTRA_ARGS="--no-sandbox,--disable-gpu"
```

### Docker/Containerized Environments

For headless Chromium in Docker containers, the following launch arguments are automatically applied:

```bash
--no-sandbox
--disable-setuid-sandbox
--disable-dev-shm-usage
--disable-gpu
```

You can override these by setting `BROWSER_AGENT_EXTRA_ARGS`.

## Testing

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=browser_agent --cov-report=html
```

## Architecture

This is a **layered agent system** for browser automation:

1. **Browser Server/Client**: Optional persistent browser with socket-based remote control
2. **Browser Controller**: Playwright wrapper (`PlaywrightBrowserController`) implementing the `BrowserController` protocol
3. **Agent Core**: Orchestrates observe-decide-act loop via `run_task()`
4. **Policy Layer**: Decision logic (`Policy` protocol) - maps observations to actions
5. **Task Specs**: Define goals via `initial_url()`, `is_done()`, `is_failed()` methods
6. **Actions & Observations**: Structured browser operations and state representation

**Key Design Principles:**
- Browser layer is AI-agnostic (no decision logic)
- Protocol-based abstractions enable testing and extensibility
- Clear separation between infrastructure and application logic

## Project Structure

```
src/browser_agent/
├── agent/
│   ├── core.py              # Agent loop, Policy protocol
│   └── task_spec.py         # BaseTaskSpec abstract class
├── browser/
│   ├── actions.py           # Action dataclasses (Navigate, Click, Type, etc.)
│   ├── observation.py       # PageObservation, structured state
│   └── playwright_driver.py # BrowserController implementation
├── network/
│   ├── browser_server.py    # Persistent browser server
│   └── browser_client.py    # Client for remote browser control
├── config.py                # Settings and configuration
├── logging_utils.py         # Logging utilities
├── interactive_session.py   # Interactive REPL
└── cli.py                   # CLI entry point

tests/
├── conftest.py              # Shared test fixtures
├── test_agent_mock_browser.py # Canonical mock testing pattern
├── test_playwright_driver.py  # Integration tests
├── test_browser_server.py     # Server tests
└── ...                        # Other core infrastructure tests

docs/
├── PROPOSAL.md              # Original design document
├── BROWSER_SERVER_GUIDE.md  # Server/client usage
├── INTERACTIVE_GUIDE.md     # Interactive session docs
└── ...                      # Other core documentation
```

## Building Applications

This framework is designed to be extended with application-specific:
- **Policy implementations**: Implement the `Policy` protocol for custom decision logic
- **Task specifications**: Extend `BaseTaskSpec` for specific automation goals
- **CLI commands**: Add application-specific commands to separate entry points

See [docs/PROPOSAL.md](docs/PROPOSAL.md) for architecture details and design rationale.

## Testing

Core infrastructure tests:

```bash
pytest
```

With coverage:

```bash
pytest --cov=browser_agent --cov-report=html
```

**Mock Browser Pattern**: Use `MockBrowser` implementing `BrowserController` protocol for unit testing agent logic without real browsers. See [tests/test_agent_mock_browser.py](tests/test_agent_mock_browser.py) for the canonical example.
