#!/usr/bin/env python3
"""Test the 'ready' command functionality."""

from browser_agent.server import BrowserClient
import time

def test_ready_command():
    """Test sending ready command to server."""
    client = BrowserClient(port=9999)
    
    print("Testing connection to server...")
    result = client.ping()
    print(f"Ping result: {result}\n")
    
    if result.get("waiting"):
        print("Server is waiting for 'ready' command")
        print("Sending 'ready' command...\n")
        
        ready_result = client.ready()
        print(f"Ready result: {ready_result}\n")
        
        # Wait a moment for server to process
        time.sleep(1)
        
        # Try ping again
        print("Testing connection after ready...")
        result = client.ping()
        print(f"Ping result: {result}\n")
    
    # Get current page info
    print("Getting page info...")
    info = client.info()
    print(f"URL: {info.get('url')}")
    print(f"Title: {info.get('title')}")

if __name__ == "__main__":
    test_ready_command()
