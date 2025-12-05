#!/usr/bin/env python3
"""
Browser Server - Maintains a persistent browser instance that can be controlled remotely.

This server keeps a browser open and listens for commands via a simple socket interface.
This allows you to authenticate once and run multiple extraction scripts without
re-authenticating each time.
"""
from __future__ import annotations

import json
import socket
import threading
from pathlib import Path

from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.browser.actions import Navigate, Click, WaitForSelector, ExtractLinks, ExtractHTML
from rich import print
from rich.console import Console


class BrowserServer:
    def __init__(self, browser_exe: str = "/usr/bin/brave-browser", port: int = 9999):
        self.port = port
        self.browser_exe = browser_exe
        self.controller: PlaywrightBrowserController | None = None
        self.console = Console()
        self.running = False
        
    def start(self):
        """Start the browser and server."""
        self.console.print(f"[bold cyan]🌐 Browser Server Starting[/bold cyan]")
        self.console.print(f"Port: {self.port}")
        self.console.print(f"Browser: {self.browser_exe}\n")
        
        # Start browser
        self.controller = PlaywrightBrowserController(
            executable_path=self.browser_exe,
            headless=False,
        )
        self.controller.start()
        self.console.print("[green]✓ Browser started[/green]")
        
        # Navigate to Patreon for authentication
        self.controller.perform(Navigate("https://www.patreon.com"))
        self.console.print("[yellow]Please authenticate in the browser...[/yellow]")
        input("Press Enter once you're logged in to start the server...\n")
        
        # Start socket server
        self.running = True
        self.console.print(f"\n[bold green]✓ Server ready on port {self.port}[/bold green]")
        self.console.print("[dim]Waiting for commands... (Ctrl+C to stop)[/dim]\n")
        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', self.port))
        server_socket.listen(5)
        server_socket.settimeout(1.0)  # Allow checking for shutdown
        
        try:
            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    # Handle client directly in main thread (not in a separate thread)
                    # This is necessary because Playwright sync API doesn't work across threads
                    self.handle_client(client_socket)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.console.print(f"[red]Error accepting connection: {e}[/red]")
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Shutting down...[/yellow]")
        finally:
            server_socket.close()
            if self.controller:
                self.controller.stop()
            self.console.print("[dim]Server stopped[/dim]")
    
    def handle_client(self, client_socket: socket.socket):
        """Handle a client connection."""
        try:
            # Receive command
            data = client_socket.recv(4096)
            if not data:
                return
            
            command = json.loads(data.decode())
            self.console.print(f"[cyan]← Command:[/cyan] {command.get('action')}")
            
            # Execute command in main thread
            response = self.execute_command(command)
            
            # Send response
            client_socket.sendall(json.dumps(response).encode())
            self.console.print(f"[green]→ Response:[/green] {response.get('status')}")
            
        except Exception as e:
            error_response = {"status": "error", "message": str(e)}
            try:
                client_socket.sendall(json.dumps(error_response).encode())
            except:
                pass
            self.console.print(f"[red]Error: {e}[/red]")
            import traceback
            traceback.print_exc()
        finally:
            client_socket.close()
    
    def execute_command(self, command: dict) -> dict:
        """Execute a command and return the result."""
        action = command.get("action")
        
        try:
            if action == "goto":
                url = command.get("url")
                self.controller.perform(Navigate(url))
                obs = self.controller.get_observation()
                return {
                    "status": "success",
                    "url": obs.url,
                    "title": obs.title
                }
            
            elif action == "click":
                selector = command.get("selector")
                timeout = command.get("timeout", 5000)
                if self.controller._page:
                    self.controller._page.click(selector, timeout=timeout)
                return {"status": "success"}
            
            elif action == "wait":
                selector = command.get("selector")
                timeout = command.get("timeout", 10000)
                self.controller.perform(WaitForSelector(selector, timeout_ms=timeout))
                return {"status": "success"}
            
            elif action == "extract":
                selector = command.get("selector")
                self.controller.perform(ExtractLinks(selector))
                links = self.controller.get_extracted_links()
                return {
                    "status": "success",
                    "count": len(links),
                    "links": links
                }
            
            elif action == "extract_html":
                selector = command.get("selector")
                self.controller.perform(ExtractHTML(selector))
                html = self.controller.get_extracted_html()
                if not html:
                    return {
                        "status": "error",
                        "message": f"No element found matching selector: {selector}",
                        "html": "",
                        "length": 0
                    }
                return {
                    "status": "success",
                    "html": html,
                    "length": len(html)
                }
            
            elif action == "eval_js":
                # Execute JavaScript and return result
                js_code = command.get("code")
                if self.controller._page:
                    result = self.controller._page.evaluate(js_code)
                    return {
                        "status": "success",
                        "result": result
                    }
                else:
                    return {"status": "error", "message": "No page available"}
            
            elif action == "info":
                obs = self.controller.get_observation()
                return {
                    "status": "success",
                    "url": obs.url,
                    "title": obs.title,
                    "buttons": len(obs.buttons),
                    "inputs": len(obs.inputs)
                }
            
            elif action == "ping":
                return {"status": "success", "message": "pong"}
            
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}


def main():
    import sys
    
    browser_exe = sys.argv[1] if len(sys.argv) > 1 else "/usr/bin/brave-browser"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9999
    
    server = BrowserServer(browser_exe=browser_exe, port=port)
    server.start()


if __name__ == "__main__":
    main()
