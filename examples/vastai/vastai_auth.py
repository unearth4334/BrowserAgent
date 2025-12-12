#!/usr/bin/env python3
"""
Vast.ai authentication script using browser-agent.

This script demonstrates how to authenticate with a vast.ai instance using
HTTP basic auth credentials.

Usage:
    python examples/vastai/vastai_auth.py [--headless] [--url URL]

Prerequisites:
    - Update vastai_credentials.txt with your username:password
    - Playwright must be installed (playwright install chromium)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from browser_agent.agent.core import Agent
from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.config import Settings

# Import from local module
from task_spec_vastai import VastAiAuthTaskSpec
from policy_vastai import VastAiAuthPolicy


def load_credentials(credentials_file: Path) -> tuple[str, str]:
    """Load credentials from the credentials file."""
    if not credentials_file.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {credentials_file}\n"
            "Please create it with format: username:password"
        )
    
    content = credentials_file.read_text().strip()
    # Skip comments and empty lines
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            if ":" in line:
                username, password = line.split(":", 1)
                return username.strip(), password.strip()
    
    raise ValueError(
        f"Invalid credentials format in {credentials_file}\n"
        "Expected format: username:password"
    )


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Authenticate with vast.ai using HTTP basic auth"
    )
    parser.add_argument(
        "--url",
        default="https://disks-gba-says-facts.trycloudflare.com/",
        help="Vast.ai URL to authenticate with (default: %(default)s)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode",
    )
    parser.add_argument(
        "--credentials-file",
        type=Path,
        default=project_root / "vastai_credentials.txt",
        help="Path to credentials file (default: vastai_credentials.txt)",
    )
    
    args = parser.parse_args()
    
    # Load credentials
    try:
        username, password = load_credentials(args.credentials_file)
        print(f"Loaded credentials for user: {username}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    # Create task spec
    task = VastAiAuthTaskSpec(
        target_url=args.url,
        username=username,
        password=password,
    )
    
    # Create policy
    policy = VastAiAuthPolicy()
    
    # Create agent
    agent = Agent(policy=policy)
    
    # Configure settings
    settings = Settings.from_env()
    settings.headless = args.headless
    
    print(f"\n🚀 Starting authentication with {args.url}")
    print(f"   Headless mode: {settings.headless}")
    print()
    
    # Run the agent
    with PlaywrightBrowserController(settings) as browser:
        result = agent.run_task(browser, task)
        
        if result == "success":
            print("\n✅ Successfully authenticated!")
            print(f"   Final URL: {browser.observe().url}")
            print(f"   Page title: {browser.observe().title}")
            print("\nBrowser will remain open. Press Enter to close...")
            input()
        elif result == "failed":
            print("\n❌ Authentication failed!")
            print(f"   Current URL: {browser.observe().url}")
            print(f"   Page title: {browser.observe().title}")
        else:
            print(f"\n⚠️  Task incomplete: {result}")
    
    return 0 if result == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
