#!/bin/bash
# Test script for interactive mode - simulates user typing commands

cd /home/sdamk/dev/BrowserAgent

# Start server in foreground, send commands via a pipe
{
    echo "Starting server in foreground mode..."
    sleep 3
    echo "status"  # Type 'status' command
    sleep 2
    echo "help"    # Type 'help' command
    sleep 2
    echo "ready"   # Type 'ready' to continue
    sleep 2
} | timeout 15 .venv/bin/python -m browser_agent.server.browser_server --wait 2>&1 | head -100
