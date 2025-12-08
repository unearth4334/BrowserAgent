#!/usr/bin/env python3
"""
Browser Client - Send commands to a running browser server.

This allows you to control a persistent browser instance without re-authenticating.

This is a wrapper around the main BrowserClient implementation.
"""
from browser_agent.server.browser_client import BrowserClient


def main():
    """CLI entry point - wrapper for the main client."""
    from browser_agent.server.browser_client import main as client_main
    client_main()


if __name__ == "__main__":
    main()
