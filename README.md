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
