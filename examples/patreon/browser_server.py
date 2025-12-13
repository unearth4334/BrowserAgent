#!/usr/bin/env python3
"""
Browser Server - Maintains a persistent browser instance that can be controlled remotely.

This server keeps a browser open and listens for commands via a simple socket interface.
This allows you to authenticate once and run multiple extraction scripts without
re-authenticating each time.

This is a wrapper around the main BrowserServer implementation.
"""
from browser_agent.server.browser_server import BrowserServer


def main():
    import sys
    
    # Parse command line arguments (legacy format support)
    browser_exe = sys.argv[1] if len(sys.argv) > 1 else "/usr/bin/brave-browser"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9999
    initial_url = sys.argv[3] if len(sys.argv) > 3 else "https://www.patreon.com"
    
    # Create and start server with wait for authentication
    server = BrowserServer(browser_exe=browser_exe, port=port)
    server.start(initial_url=initial_url, wait_for_auth=True)


if __name__ == "__main__":
    main()
