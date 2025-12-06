#!/usr/bin/env python3
"""
Browser Client - Send commands to a running browser server.

This allows you to control a persistent browser instance without re-authenticating.
"""
from __future__ import annotations

import json
import socket
import sys


class BrowserClient:
    """
    Client for communicating with a BrowserServer instance.
    
    Example:
        client = BrowserClient()
        
        # Check server is running
        result = client.ping()
        
        # Navigate to a URL
        result = client.goto("https://example.com")
        
        # Extract links
        result = client.extract("a[href*='/items/']")
        links = result.get('links', [])
    """
    
    def __init__(self, host: str = "localhost", port: int = 9999):
        """
        Initialize the browser client.
        
        Args:
            host: Server hostname (default: localhost)
            port: Server port (default: 9999)
        """
        self.host = host
        self.port = port
    
    def send_command(self, command: dict) -> dict:
        """Send a command to the browser server and get the response."""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.host, self.port))
            
            # Send command
            client_socket.sendall(json.dumps(command).encode())
            
            # Receive response
            data = client_socket.recv(8192)
            response = json.loads(data.decode())
            
            client_socket.close()
            return response
            
        except ConnectionRefusedError:
            return {
                "status": "error",
                "message": "Could not connect to browser server. Is it running?"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def goto(self, url: str) -> dict:
        """Navigate to a URL."""
        return self.send_command({"action": "goto", "url": url})
    
    def click(self, selector: str, timeout: int = 5000) -> dict:
        """Click an element."""
        return self.send_command({
            "action": "click",
            "selector": selector,
            "timeout": timeout
        })
    
    def wait(self, selector: str, timeout: int = 10000) -> dict:
        """Wait for an element to appear."""
        return self.send_command({
            "action": "wait",
            "selector": selector,
            "timeout": timeout
        })
    
    def extract(self, selector: str) -> dict:
        """Extract links matching a selector."""
        return self.send_command({
            "action": "extract",
            "selector": selector
        })
    
    def extract_html(self, selector: str) -> dict:
        """Extract HTML content from a selector."""
        return self.send_command({
            "action": "extract_html",
            "selector": selector
        })
    
    def eval_js(self, code: str) -> dict:
        """Execute JavaScript code and return the result."""
        return self.send_command({
            "action": "eval_js",
            "code": code
        })
    
    def download(self, url: str, save_path: str) -> dict:
        """Download a file from a URL."""
        return self.send_command({
            "action": "download",
            "url": url,
            "save_path": save_path
        })
    
    def info(self) -> dict:
        """Get current page info."""
        return self.send_command({"action": "info"})
    
    def ping(self) -> dict:
        """Check if server is alive."""
        return self.send_command({"action": "ping"})


def main():
    """Simple CLI for the browser client."""
    if len(sys.argv) < 2:
        print("Usage: python -m browser_agent.server.browser_client <command> [args...]")
        print("\nCommands:")
        print("  ping")
        print("  info")
        print("  goto <url>")
        print("  click <selector> [timeout_ms]")
        print("  wait <selector> [timeout_ms]")
        print("  extract <selector>")
        sys.exit(1)
    
    client = BrowserClient()
    command = sys.argv[1]
    
    if command == "ping":
        result = client.ping()
    elif command == "info":
        result = client.info()
    elif command == "goto":
        result = client.goto(sys.argv[2])
    elif command == "click":
        timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
        result = client.click(sys.argv[2], timeout)
    elif command == "wait":
        timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
        result = client.wait(sys.argv[2], timeout)
    elif command == "extract":
        result = client.extract(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
