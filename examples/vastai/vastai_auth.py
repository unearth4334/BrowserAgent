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


def load_credentials(credentials_file: Path) -> tuple[str, str, str, str]:
    """Load credentials, URL, and workflow path from the credentials file.
    
    Returns:
        tuple[str, str, str, str]: username, password, url, workflow_path
    """
    if not credentials_file.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {credentials_file}\n"
            "Please create it with format:\n"
            "  Line 1: username:password\n"
            "  Line 2: url\n"
            "  Line 3: workflow_path"
        )
    
    content = credentials_file.read_text().strip()
    username = None
    password = None
    url = None
    workflow_path = None
    
    # Parse the file looking for credentials, URL, and workflow
    non_comment_lines = []
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            non_comment_lines.append(line)
    
    # First line with colon is username:password
    if len(non_comment_lines) >= 1 and ":" in non_comment_lines[0]:
        username, password = non_comment_lines[0].split(":", 1)
        username = username.strip()
        password = password.strip()
    
    # Second line is URL
    if len(non_comment_lines) >= 2:
        url = non_comment_lines[1].strip()
    
    # Third line is workflow path (optional)
    if len(non_comment_lines) >= 3:
        workflow_path = non_comment_lines[2].strip()
    
    if not username or not password:
        raise ValueError(
            f"Invalid credentials format in {credentials_file}\n"
            "Expected format:\n"
            "  Line 1: username:password\n"
            "  Line 2: url\n"
            "  Line 3: workflow_path (optional)"
        )
    
    if not url:
        raise ValueError(
            f"URL not found in {credentials_file}\n"
            "Expected format:\n"
            "  Line 1: username:password\n"
            "  Line 2: url\n"
            "  Line 3: workflow_path (optional)"
        )
    
    return username, password, url, workflow_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Authenticate with vast.ai using HTTP basic auth"
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Vast.ai URL to authenticate with (overrides URL from credentials file)",
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
    
    # Load credentials, URL, and workflow
    try:
        username, password, url, workflow_path = load_credentials(args.credentials_file)
        print(f"Loaded credentials for user: {username}")
        print(f"Loaded URL: {url}")
        if workflow_path:
            print(f"Loaded workflow: {workflow_path}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    # Use command-line URL if provided, otherwise use from credentials file
    target_url = args.url if args.url else url
    
    # Create task spec
    task = VastAiAuthTaskSpec(
        target_url=target_url,
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
