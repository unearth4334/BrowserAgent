#!/usr/bin/env python3
"""
Civitai Browser Server - Simple wrapper around main implementation.
"""
import sys
from pathlib import Path

# Add parent directory to path to import from main implementation
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from browser_agent.server.browser_server import BrowserServer, main

if __name__ == "__main__":
    # Civitai requires authentication, so start with wait_for_auth=True
    # and navigate to civitai.com for login
    import sys
    
    # Use provided browser path or default
    browser_exe = sys.argv[1] if len(sys.argv) > 1 else None
    
    server = BrowserServer(
        browser_exe=browser_exe,
        port=9999,
        log_file="/tmp/civitai_browser_server.log"
    )
    
    print("Starting browser server for Civitai...")
    print("You will be able to login before the server starts accepting commands.")
    
    server.start(
        initial_url="https://civitai.com/",
        wait_for_auth=True
    )
