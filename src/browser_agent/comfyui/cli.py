"""ComfyUI CLI commands."""
from __future__ import annotations

import typer
from pathlib import Path
from rich import print
from rich.console import Console

from ..server.browser_server import BrowserServer
from .config import ComfyUIConfig

console = Console()


def parse_credentials_file(file_path: str) -> dict[str, str]:
    """
    Parse credentials file in vastai format.
    
    Expected format (non-comment lines):
        Line 1: username:password
        Line 2: url
        Line 3: workflow_path (optional)
    
    Args:
        file_path: Path to credentials file
        
    Returns:
        Dict with keys: username, password, url, workflow_path (if present)
    """
    result = {}
    cred_path = Path(file_path)
    
    if not cred_path.exists():
        return result
    
    non_comment_lines = []
    with open(cred_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                non_comment_lines.append(line)
    
    if len(non_comment_lines) >= 1 and ':' in non_comment_lines[0]:
        username, password = non_comment_lines[0].split(':', 1)
        result['username'] = username
        result['password'] = password
    
    if len(non_comment_lines) >= 2:
        result['url'] = non_comment_lines[1]
    
    if len(non_comment_lines) >= 3:
        result['workflow_path'] = non_comment_lines[2]
    
    return result


def parse_credentials(credentials_str: str) -> tuple[str, str] | None:
    """
    Parse credentials from string or file.
    
    Args:
        credentials_str: Either "username:password" or path to credentials file
        
    Returns:
        Tuple of (username, password) or None if not found
    """
    # Check if it's a file path
    cred_path = Path(credentials_str)
    if cred_path.exists():
        data = parse_credentials_file(credentials_str)
        if 'username' in data and 'password' in data:
            return (data['username'], data['password'])
        console.print(f"[yellow]Warning: No credentials found in {credentials_str}[/yellow]")
        return None
    
    # Otherwise treat as username:password string
    if ':' in credentials_str:
        parts = credentials_str.split(':', 1)
        return (parts[0], parts[1])
    
    console.print(f"[yellow]Warning: Invalid credentials format: {credentials_str}[/yellow]")
    return None


def open_browser(
    comfyui_url: str | None = typer.Option(None, help="ComfyUI URL (e.g., http://localhost:8188)"),
    credentials: str | None = typer.Option(None, help="Credentials as 'user:pass' or path to credentials file"),
    headless: bool = typer.Option(False, help="Run browser in headless mode"),
    browser_exe: str | None = typer.Option(None, help="Path to browser executable"),
    port: int = typer.Option(9999, help="Port for browser server"),
):
    """
    Open ComfyUI in a browser server.
    
    The browser will stay open and you can interact with it. The server
    listens on the specified port for remote commands.
    
    Examples:
        # Open with credentials file (auto-reads URL from file)
        browser-agent comfyui open --credentials vastai_credentials.txt
        
        # Open with explicit URL and credentials
        browser-agent comfyui open --comfyui-url http://localhost:8188 --credentials user:pass
        
        # Open in headless mode
        browser-agent comfyui open --credentials vastai_credentials.txt --headless
    """
    # Parse credentials if provided (may include URL)
    username = None
    password = None
    url_from_file = None
    
    if credentials:
        # Check if it's a file - if so, try to read URL from it
        cred_path = Path(credentials)
        if cred_path.exists():
            cred_data = parse_credentials_file(credentials)
            if 'username' in cred_data and 'password' in cred_data:
                username = cred_data['username']
                password = cred_data['password']
                console.print(f"[green]✓ Credentials loaded: {username}[/green]")
            
            if 'url' in cred_data:
                url_from_file = cred_data['url']
                console.print(f"[green]✓ URL from file: {url_from_file}[/green]")
        else:
            # Parse as username:password string
            creds = parse_credentials(credentials)
            if creds:
                username, password = creds
                console.print(f"[green]✓ Credentials loaded: {username}[/green]")
            else:
                console.print("[yellow]⚠ Continuing without credentials[/yellow]")
    
    # Determine final URL (explicit flag overrides file)
    final_url = comfyui_url or url_from_file
    
    if not final_url:
        console.print("[red]Error: No URL provided. Use --comfyui-url or provide a credentials file with a URL.[/red]")
        raise typer.Exit(code=1)
    
    console.print(f"\n[bold cyan]🚀 Opening ComfyUI Browser Server[/bold cyan]")
    console.print(f"URL: {final_url}")
    console.print(f"Headless: {headless}")
    console.print(f"Port: {port}\n")
    
    # Create browser server
    server = BrowserServer(
        browser_exe=browser_exe,
        port=port,
        headless=headless,
    )
    
    # Build URL with auth if provided
    url = final_url
    if username and password:
        # Parse URL to inject auth
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        
        # Add auth to netloc
        netloc_with_auth = f"{username}:{password}@{parsed.hostname}"
        if parsed.port:
            netloc_with_auth += f":{parsed.port}"
        
        # Reconstruct URL
        url = urlunparse((
            parsed.scheme,
            netloc_with_auth,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        console.print(f"[dim]Authenticated URL prepared[/dim]\n")
    
    # Start server with ComfyUI URL
    console.print(f"[bold]Starting browser and navigating to ComfyUI...[/bold]")
    try:
        server.start(initial_url=url, wait_for_auth=False)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


# Create the comfyui subcommand group
comfyui_app = typer.Typer(help="ComfyUI browser automation commands")
comfyui_app.command("open")(open_browser)


if __name__ == "__main__":
    comfyui_app()
