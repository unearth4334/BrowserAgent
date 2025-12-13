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
import traceback

from ..browser.playwright_driver import PlaywrightBrowserController
from ..browser.actions import Navigate, WaitForSelector, ExtractLinks, ExtractHTML
from rich import print
from rich.console import Console


class BrowserServer:
    """
    A persistent browser server that accepts commands via socket.
    
    This enables workflows where authentication is needed once, then multiple
    scripts can interact with the authenticated browser session.
    
    Example:
        server = BrowserServer(browser_exe="/usr/bin/brave-browser", port=9999)
        server.start(initial_url="https://example.com")
    """
    
    def __init__(self, browser_exe: str | None = None, port: int = 9999, log_file: str | None = None, headless: bool = False):
        """
        Initialize the browser server.
        
        Args:
            browser_exe: Path to browser executable (optional)
            port: Port to listen on (default: 9999)
            log_file: Path to log file (optional, defaults to /tmp/browser_server_{port}.log)
            headless: Run browser in headless mode (default: False)
        """
        self.port = port
        self.browser_exe = browser_exe
        self.headless = headless
        self.log_file = log_file or f"/tmp/browser_server_{port}.log"
        self.controller: PlaywrightBrowserController | None = None
        self.console = Console()
        self.running = False
        self.waiting_for_ready = False
        self.in_foreground = True  # Track if we're in foreground mode
    
    def _log(self, message: str, level: str = "INFO"):
        """Log a message to the log file."""
        import logging
        logger = logging.getLogger(__name__)
        if level == "INFO":
            logger.info(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "ERROR":
            logger.error(message)
        
    def start(self, initial_url: str | None = None, wait_for_auth: bool = True):
        """
        Start the browser and server.
        
        Args:
            initial_url: URL to navigate to initially (optional)
            wait_for_auth: Whether to wait for user input before starting server
        """
        # Set up file logging
        import logging
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self._log(f"Server starting on port {self.port}")
        
        self.console.print(f"[bold cyan]🌐 Browser Server Starting[/bold cyan]")
        self.console.print(f"Port: {self.port}")
        if self.browser_exe:
            self.console.print(f"Browser: {self.browser_exe}")
        self.console.print(f"Log file: {self.log_file}\n")
        
        # Start browser
        self.controller = PlaywrightBrowserController(
            executable_path=self.browser_exe,
            headless=self.headless,
        )
        self.controller.start()
        self.console.print("[green]✓ Browser started[/green]")
        
        # Navigate to initial URL if provided
        if initial_url:
            self.controller.perform(Navigate(initial_url))
            self.console.print(f"[dim]Navigated to {initial_url}[/dim]")
        
        # Start socket server first
        self.running = True
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', self.port))
        server_socket.listen(5)
        server_socket.settimeout(0.1)  # Short timeout for responsive commands
        
        # Check if we're running in foreground (part of shell's foreground process group)
        import sys
        import os
        try:
            # If we're in the foreground process group, we're interactive
            is_foreground = os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno())
        except:
            # If we can't determine, assume background
            is_foreground = False
        
        # Handle wait_for_auth
        if wait_for_auth:
            self.waiting_for_ready = True
            if is_foreground:
                # Foreground mode - print message and show interactive prompts
                self.console.print("\n[yellow]⏸  Waiting for authentication...[/yellow]")
                self.console.print("[dim]Type 'ready' to continue, 'background' to detach, or 'help' for commands[/dim]")
            else:
                # Background mode - print message but no interactive prompts
                self.console.print("\n[yellow]⏸  Waiting for 'ready' command from client...[/yellow]")
                self.console.print(f"[dim]Send: python -m browser_agent.server.browser_client ready[/dim]")
            
            self._wait_for_ready(server_socket, is_foreground)
        
        self.console.print(f"\n[bold green]✓ Server ready on port {self.port}[/bold green]")
        
        self._run_server_loop(server_socket)
    
    def _wait_for_ready(self, server_socket: socket.socket, is_foreground: bool = True):
        """Wait for 'ready' command from interactive prompt or client."""
        import sys
        import select
        
        # Print initial prompt once
        prompt_needed = is_foreground
        
        try:
            while self.waiting_for_ready and self.running:
                # Print prompt only when needed (initially or after processing a command)
                if prompt_needed:
                    sys.stdout.write("\n> ")
                    sys.stdout.flush()
                    prompt_needed = False
                
                # Use select to wait for either socket connection or stdin input
                readable = [server_socket]
                if is_foreground:
                    readable.append(sys.stdin)
                
                try:
                    ready_to_read, _, _ = select.select(readable, [], [], 0.1)
                except (select.error, TypeError, ValueError):
                    # Handle select errors (e.g., interrupted system call, mock objects)
                    # For socket timeout, try direct accept
                    try:
                        client_socket, address = server_socket.accept()
                        self._handle_client_during_wait(client_socket)
                        if not self.waiting_for_ready:
                            return
                    except socket.timeout:
                        pass
                    except Exception as e:
                        if self.running:
                            self.console.print(f"\n[red]Error: {e}[/red]")
                            prompt_needed = is_foreground
                    continue
                
                # Check if server socket has a connection
                if server_socket in ready_to_read:
                    try:
                        client_socket, address = server_socket.accept()
                        self._handle_client_during_wait(client_socket)
                        if not self.waiting_for_ready:
                            return
                    except socket.timeout:
                        pass
                    except Exception as e:
                        if self.running:
                            self.console.print(f"\n[red]Error: {e}[/red]")
                            prompt_needed = is_foreground  # Re-prompt after error
                
                # Check if stdin has input (only in foreground)
                if is_foreground and sys.stdin in ready_to_read:
                    command = sys.stdin.readline().strip().lower()
                    if command == "ready":
                        self.waiting_for_ready = False
                        self.console.print("[green]✓ Server proceeding to main loop[/green]")
                        return
                    elif command in ("background", "detach", "bg"):
                        self.waiting_for_ready = False
                        self.console.print("[green]✓ Entering background mode - server still running[/green]")
                        self.console.print("[dim]Process is now ready to be backgrounded. Press Ctrl+Z then type 'bg'[/dim]")
                        self.in_foreground = False
                        # Close stdin to allow proper backgrounding
                        try:
                            sys.stdin.close()
                        except:
                            pass
                        return
                    elif command == "quit" or command == "exit":
                        self.console.print("[yellow]Stopping server...[/yellow]")
                        self.running = False
                        self.waiting_for_ready = False
                        return
                    elif command == "help":
                        self.console.print("\n[bold]Available Commands:[/bold]")
                        self.console.print("  [cyan]ready[/cyan]      - Continue to main server loop")
                        self.console.print("  [cyan]background[/cyan] - Exit foreground mode, keep server running")
                        self.console.print("  [cyan]detach[/cyan]     - Same as background")
                        self.console.print("  [cyan]status[/cyan]     - Show current page info")
                        self.console.print("  [cyan]quit[/cyan]       - Stop the server and exit")
                        prompt_needed = True  # Show new prompt after help
                    elif command == "status":
                        if self.controller:
                            obs = self.controller.get_observation()
                            self.console.print("\n[bold]Current Page:[/bold]")
                            self.console.print(f"  URL: [cyan]{obs.url}[/cyan]")
                            self.console.print(f"  Title: [dim]{obs.title}[/dim]")
                        prompt_needed = True  # Show new prompt after status
                    elif command:
                        self.console.print(f"[yellow]Unknown command: {command}[/yellow]")
                        self.console.print("[dim]Type 'ready' to continue, 'help' for commands[/dim]")
                        prompt_needed = True  # Show new prompt after unknown command
                        
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Shutting down...[/yellow]")
            self.running = False
            self.waiting_for_ready = False
    
    def _handle_client_during_wait(self, client_socket: socket.socket):
        """Handle client connections while waiting for ready."""
        try:
            data = client_socket.recv(65536)
            if not data:
                return
            
            command = json.loads(data.decode())
            action = command.get("action")
            
            if action == "ready":
                self.waiting_for_ready = False
                response = {"status": "success", "message": "Server is now ready"}
                self.console.print("\n[green]✓ Received 'ready' from client, proceeding to main loop[/green]")
            elif action == "ping":
                response = {"status": "success", "message": "pong", "waiting": True}
            elif action == "get_log_file":
                response = {"status": "success", "log_file": self.log_file, "waiting": True}
            elif action == "status":
                if self.controller:
                    obs = self.controller.get_observation()
                    response = {
                        "status": "success",
                        "url": obs.url,
                        "title": obs.title,
                        "waiting": True
                    }
                else:
                    response = {"status": "error", "message": "No controller"}
            else:
                response = {
                    "status": "waiting",
                    "message": "Server is waiting for 'ready' command. Send action='ready' to proceed."
                }
            
            client_socket.sendall(json.dumps(response).encode())
        except Exception as e:
            error_response = {"status": "error", "message": str(e)}
            try:
                client_socket.sendall(json.dumps(error_response).encode())
            except:
                pass
        finally:
            client_socket.close()
    
    def _run_server_loop(self, server_socket: socket.socket):
        """Run the server loop with interactive command prompt."""
        import threading
        import sys
        import os
        import select
        
        # Check if we're running in foreground initially
        try:
            is_foreground = os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno())
            self.in_foreground = is_foreground
        except:
            self.in_foreground = False
        
        # Print available commands
        self.console.print("\n[bold]Interactive Commands:[/bold]")
        self.console.print("  [cyan]status[/cyan]     - Show current page info")
        self.console.print("  [cyan]background[/cyan] - Exit foreground mode (keep server running)")
        self.console.print("  [cyan]quit[/cyan]       - Stop the server and exit")
        self.console.print("  [cyan]help[/cyan]       - Show this help message")
        self.console.print(f"\n[dim]Server is listening for client connections on port {self.port}[/dim]")
        
        if not self.in_foreground:
            self.console.print("[dim](Running in background mode - use client commands or send SIGTERM to stop)[/dim]")
        
        # Print initial prompt once
        prompt_needed = self.in_foreground
        
        try:
            while self.running:
                # Print prompt only when needed (initially or after processing a command)
                if prompt_needed and self.in_foreground:
                    sys.stdout.write("\n> ")
                    sys.stdout.flush()
                    prompt_needed = False
                
                # Use select to wait for either socket connection or stdin input
                readable = [server_socket]
                if self.in_foreground:
                    readable.append(sys.stdin)
                
                try:
                    ready_to_read, _, _ = select.select(readable, [], [], 0.1)
                except (select.error, TypeError, ValueError):
                    # Handle select errors (e.g., interrupted system call, mock objects)
                    # For socket timeout, try direct accept
                    try:
                        client_socket, address = server_socket.accept()
                        self._handle_client(client_socket)
                    except socket.timeout:
                        pass
                    except Exception as e:
                        if self.running:
                            self.console.print(f"\n[red]Error accepting connection: {e}[/red]")
                            prompt_needed = self.in_foreground
                    continue
                
                # Check if server socket has a connection
                if server_socket in ready_to_read:
                    try:
                        client_socket, address = server_socket.accept()
                        self._handle_client(client_socket)
                    except socket.timeout:
                        pass
                    except Exception as e:
                        if self.running:
                            self.console.print(f"\n[red]Error accepting connection: {e}[/red]")
                            prompt_needed = self.in_foreground  # Re-prompt after error
                
                # Check if stdin has input (only in foreground)
                if self.in_foreground and sys.stdin in ready_to_read:
                    command = sys.stdin.readline().strip().lower()
                    if command:
                        should_break = self._handle_interactive_command(command)
                        if should_break:
                            break
                        # Only prompt again if still in foreground (command might have changed it)
                        prompt_needed = self.in_foreground
                
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Shutting down...[/yellow]")
        finally:
            server_socket.close()
            if self.controller:
                self.controller.stop()
            self.console.print("[dim]Server stopped[/dim]")
    
    def _handle_interactive_command(self, command: str) -> bool:
        """Handle interactive commands from the console.
        
        Returns:
            bool: True if should break from main loop, False to continue
        """
        if command == "quit" or command == "exit":
            self.console.print("[yellow]Stopping server...[/yellow]")
            self.running = False
            return True  # Break from loop to stop server
        
        elif command in ("background", "detach", "bg"):
            self.console.print("[green]✓ Entering background mode - server still running[/green]")
            self.console.print("[dim]Process is now ready to be backgrounded. Press Ctrl+Z then type 'bg'[/dim]")
            self.in_foreground = False  # Disable foreground mode
            # Close stdin to allow proper backgrounding
            try:
                sys.stdin.close()
            except:
                pass
            return False  # Don't break, continue running in background
        
        elif command == "status":
            if self.controller:
                obs = self.controller.get_observation()
                self.console.print("\n[bold]Current Page:[/bold]")
                self.console.print(f"  URL: [cyan]{obs.url}[/cyan]")
                self.console.print(f"  Title: [dim]{obs.title}[/dim]")
                self.console.print(f"  Buttons: {len(obs.buttons)}")
                self.console.print(f"  Inputs: {len(obs.inputs)}")
            else:
                self.console.print("[red]No browser controller active[/red]")
            return False  # Don't break, continue
        
        elif command == "help":
            self.console.print("\n[bold]Available Commands:[/bold]")
            self.console.print("  [cyan]status[/cyan]     - Show current page info")
            self.console.print("  [cyan]background[/cyan] - Exit foreground mode, keep server running")
            self.console.print("  [cyan]detach[/cyan]     - Same as background")
            self.console.print("  [cyan]quit[/cyan]       - Stop the server and exit")
            self.console.print("  [cyan]help[/cyan]       - Show this help message")
            return False  # Don't break, continue
        
        elif command:
            self.console.print(f"[yellow]Unknown command: {command}[/yellow]")
            self.console.print("[dim]Type 'help' for available commands[/dim]")
            return False  # Don't break, continue
        
        return False  # Default: don't break
    
    def _handle_client(self, client_socket: socket.socket):
        """Handle a client connection."""
        try:
            # Receive command (increased buffer for larger commands)
            data = client_socket.recv(65536)
            if not data:
                return
            
            command = json.loads(data.decode())
            self.console.print(f"[cyan]← Command:[/cyan] {command.get('action')}")
            
            # Execute command in main thread
            response = self._execute_command(command)
            
            # Send response
            client_socket.sendall(json.dumps(response).encode())
            self.console.print(f"[green]→ Response:[/green] {response.get('status')}")
            
        except Exception as e:
            error_response = {"status": "error", "message": str(e)}
            try:
                client_socket.sendall(json.dumps(error_response).encode())
            except OSError:
                pass
            self.console.print(f"[red]Error: {e}[/red]")
            traceback.print_exc()
        finally:
            client_socket.close()
    
    def _execute_command(self, command: dict) -> dict:
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
            
            elif action == "download":
                # Download a file using Playwright's download mechanism
                url = command.get("url")
                save_path = command.get("save_path")
                
                if not self.controller._page:
                    return {"status": "error", "message": "No page available"}
                
                try:
                    # Use page.expect_download() with navigation
                    with self.controller._page.expect_download() as download_info:
                        # Navigate to the download URL using goto (safer than JS eval)
                        self.controller._page.goto(url)
                    
                    download = download_info.value
                    download.save_as(save_path)
                    
                    return {
                        "status": "success",
                        "path": save_path,
                        "suggested_filename": download.suggested_filename
                    }
                except Exception as e:
                    return {"status": "error", "message": f"Download failed: {str(e)}"}
            
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
            
            elif action == "get_log_file":
                return {"status": "success", "log_file": self.log_file}
            
            elif action == "screenshot":
                # Take a screenshot of the current page
                screenshot_path = command.get("path")
                if not screenshot_path:
                    return {"status": "error", "message": "No path provided for screenshot"}
                
                if self.controller._page:
                    try:
                        self.controller._page.screenshot(path=screenshot_path)
                        return {
                            "status": "success",
                            "path": screenshot_path,
                            "message": f"Screenshot saved to {screenshot_path}"
                        }
                    except Exception as e:
                        return {"status": "error", "message": f"Screenshot failed: {str(e)}"}
                else:
                    return {"status": "error", "message": "No page available"}
            
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}


def main():
    """CLI entry point for the browser server."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Start a persistent browser server")
    parser.add_argument("--browser-exe", type=str, default=None, help="Path to browser executable")
    parser.add_argument("--port", type=int, default=9999, help="Port to listen on")
    parser.add_argument("--initial-url", type=str, default=None, help="Initial URL to navigate to")
    parser.add_argument("--wait", action="store_true", help="Wait for 'ready' command before accepting other commands")
    parser.add_argument("--log-file", type=str, default=None, help="Log file path (default: /tmp/browser_server_{port}.log)")
    
    args = parser.parse_args()
    
    server = BrowserServer(browser_exe=args.browser_exe, port=args.port, log_file=args.log_file)
    server.start(initial_url=args.initial_url, wait_for_auth=args.wait)


if __name__ == "__main__":
    main()
