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
            
            # Receive response (handle larger responses in chunks)
            chunks = []
            while True:
                chunk = client_socket.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
                # Try to parse - if successful, we have the full response
                try:
                    full_data = b''.join(chunks)
                    response = json.loads(full_data.decode())
                    break
                except json.JSONDecodeError:
                    # Need more data
                    continue
            
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
    
    def ready(self) -> dict:
        """Signal the server that it's ready to proceed (clears wait state)."""
        return self.send_command({"action": "ready"})
    
    def get_log_file(self) -> dict:
        """Get the path to the server's log file."""
        return self.send_command({"action": "get_log_file"})
    
    def screenshot(self, path: str) -> dict:
        """Take a screenshot of the current page."""
        return self.send_command({
            "action": "screenshot",
            "path": path
        })


def main():
    """Simple CLI for the browser client."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Browser client for controlling a running browser server",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("-f", "--follow", action="store_true", help="Follow log output (like tail -f)")
    parser.add_argument("--tail", action="store_true", help="Show last N lines and exit")
    parser.add_argument("-n", "--lines", type=int, default=10, help="Number of lines to show (default: 10)")
    
    # Handle legacy command-line format for backward compatibility
    if len(sys.argv) < 2:
        print("Usage: python -m browser_agent.server.browser_client <command> [args...]")
        print("\nCommands:")
        print("  ping                      - Check if server is alive")
        print("  ready                     - Signal server is ready to proceed")
        print("  info                      - Get current page info")
        print("  goto <url>                - Navigate to URL")
        print("  click <selector> [timeout] - Click an element")
        print("  wait <selector> [timeout]  - Wait for an element")
        print("  extract <selector>         - Extract links")
        print("  logs [-f] [-n N] [--tail]  - View server logs")
        sys.exit(1)
    
    # Special handling for logs command with flags
    if sys.argv[1] == "logs":
        args = parser.parse_args(["logs"] + sys.argv[2:])
        _handle_logs_command(args)
        return
    
    # Parse for other commands (backward compatibility)
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
    
    client = BrowserClient()
    command = sys.argv[1]
    
    if command == "ping":
        result = client.ping()
    elif command == "ready":
        result = client.ready()
    elif command == "info":
        result = client.info()
    elif command == "goto":
        if len(sys.argv) < 3:
            print("Error: goto requires a URL")
            sys.exit(1)
        result = client.goto(sys.argv[2])
    elif command == "click":
        if len(sys.argv) < 3:
            print("Error: click requires a selector")
            sys.exit(1)
        timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
        result = client.click(sys.argv[2], timeout)
    elif command == "wait":
        if len(sys.argv) < 3:
            print("Error: wait requires a selector")
            sys.exit(1)
        timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
        result = client.wait(sys.argv[2], timeout)
    elif command == "extract":
        if len(sys.argv) < 3:
            print("Error: extract requires a selector")
            sys.exit(1)
        result = client.extract(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    print(json.dumps(result, indent=2))


def _handle_logs_command(args):
    """Handle the logs command with follow/tail options."""
    import time
    import os
    
    client = BrowserClient()
    
    # Get log file path from server
    result = client.get_log_file()
    if result.get("status") not in ("success", "waiting") or not result.get("log_file"):
        print(f"Error: {result.get('message', 'Could not get log file path')}")
        sys.exit(1)
    
    log_file = result.get("log_file")
    if not log_file or not os.path.exists(log_file):
        print(f"Error: Log file not found: {log_file}")
        sys.exit(1)
    
    if args.follow:
        # Follow mode: tail -f behavior
        print(f"Following {log_file} (Ctrl+C to stop)...\n")
        try:
            with open(log_file, 'r') as f:
                # Go to end of file
                f.seek(0, os.SEEK_END)
                while True:
                    line = f.readline()
                    if line:
                        print(line, end='')
                    else:
                        time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopped following logs")
    elif args.tail:
        # Tail mode: show last N lines and exit
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-args.lines:]:
                print(line, end='')
    else:
        # Default: show last N lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-args.lines:]:
                print(line, end='')


if __name__ == "__main__":
    main()
