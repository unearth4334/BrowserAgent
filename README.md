# Browser-Agent

A Python-based AI-style agent capable of automating interactions with a Chromium/Brave browser using Playwright.

## Features

- Launch and control Chromium/Brave browser via Playwright
- Agent loop that observes, decides, and executes actions
- Rule-based policy (extensible to LLM-based policies)
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

### Interactive Mode (NEW!)

Start a persistent browser session with a REPL for debugging and manual interaction:

```bash
# Start at a specific URL
browser-agent interactive https://www.patreon.com --browser-exe /usr/bin/brave-browser

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

See [INTERACTIVE_GUIDE.md](INTERACTIVE_GUIDE.md) for full documentation.

### Patreon Collection Extraction

Extract links from a Patreon collection (automated):

```bash
browser-agent patreon-collection 1611241 --browser-exe /usr/bin/brave-browser
```

Or use interactive mode (recommended - maintains authentication):

```bash
browser-agent interactive https://www.patreon.com --browser-exe /usr/bin/brave-browser
# Then use: goto, wait, extract, save commands
```

See [PATREON_QUICK_START.md](PATREON_QUICK_START.md) for detailed Patreon workflow.

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
- **Task Layer**: Defines goals and success criteria
- **Observation Layer**: Structured browser state representation

## Project Structure

```
browser-agent/
├─ src/browser_agent/
│  ├─ agent/          # Agent logic and policies
│  ├─ browser/        # Browser controller and actions
│  ├─ config.py       # Configuration management
│  └─ cli.py          # CLI interface
└─ tests/             # Test suite
```
