# Browser-Agent

A Python-based AI-style agent capable of automating interactions with a Chromium/Brave browser using Playwright.

## Features

- Launch and control Chromium/Brave browser via Playwright
- Agent loop that observes, decides, and executes actions
- Rule-based policy (extensible to LLM-based policies)
- **Persistent browser server** for authenticated sessions
- Simple search task demonstration
- Comprehensive test coverage

## Installation

```bash
pip install -e .[dev]
playwright install chromium
```

## Usage

### Simple Search Task

Run a simple search task:

```bash
browser-agent simple-search "hello world"
```

Run with Brave browser:

```bash
browser-agent simple-search "hello world" --browser-exe "/usr/bin/brave-browser"
```

Run in non-headless mode:

```bash
browser-agent simple-search "hello world" --no-headless
```

### Browser Server

Start a persistent browser server that maintains authentication:

```bash
# Start server with initial URL
browser-agent server https://example.com --browser-exe /usr/bin/brave-browser

# Connect from Python
from browser_agent.server import BrowserClient
client = BrowserClient()
client.goto("https://example.com/page")
```

**Benefits:**
- 🔐 Authenticate once, run multiple scripts
- ⚡ No browser startup time between operations
- 🔧 Perfect for development and debugging

See [BROWSER_SERVER_GUIDE.md](docs/BROWSER_SERVER_GUIDE.md) for full documentation.

### Interactive Mode

Start a persistent browser session with a REPL for debugging and manual interaction:

```bash
# Start at a specific URL
browser-agent interactive https://example.com --browser-exe /usr/bin/brave-browser

# Or start without a URL
browser-agent interactive --browser-exe /usr/bin/brave-browser
```

**Benefits:**
- 🔐 Authenticate once, maintain session throughout
- 🐛 Debug selectors and test commands interactively
- 🔗 Extract links and save to JSON
- 🚀 Execute JavaScript on the page
- 📊 Inspect page elements (buttons, inputs, HTML)

**Available commands:** `goto`, `extract`, `click`, `type`, `wait`, `info`, `links`, `save`, `html`, `eval`, `buttons`, `inputs`, `help`, `quit`

See [INTERACTIVE_GUIDE.md](docs/INTERACTIVE_GUIDE.md) for full documentation.

## Examples

The `examples/` directory contains user-level implementations demonstrating how to use the browser-agent utility:

- **`examples/patreon/`** - Patreon content extraction scripts
  - Custom policies and task specs
  - Collection link extraction
  - Post content and attachment downloading
  - See `examples/patreon/README.md` for usage details

## Testing

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=browser_agent --cov-report=html
```

## Architecture

- **Agent Core**: Decides next actions based on observations
- **Browser Controller**: Playwright wrapper for browser automation
- **Browser Server**: Persistent browser for authenticated sessions
- **Task Layer**: Defines goals and success criteria
- **Observation Layer**: Structured browser state representation

## Project Structure

```
browser-agent/
├─ src/browser_agent/
│  ├─ agent/          # Agent logic and policies
│  ├─ browser/        # Browser controller and actions
│  ├─ server/         # Browser server and client
│  ├─ config.py       # Configuration management
│  └─ cli.py          # CLI interface
├─ examples/          # User-level implementations
│  └─ patreon/        # Patreon extraction example
└─ tests/             # Test suite
```
