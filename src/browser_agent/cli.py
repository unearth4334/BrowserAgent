from __future__ import annotations

import typer
from rich import print

from .config import Settings
from .browser.playwright_driver import PlaywrightBrowserController
from .interactive_session import InteractiveBrowserSession
from .agent.core import Agent
from .agent.task_spec_grok import GrokDownloadTaskSpec, GrokNavigateTaskSpec
from .agent.policy_grok import GrokVisionPolicy

app = typer.Typer(help="Browser Agent - Core browser automation framework")


@app.command()
def interactive(
    url: str | None = typer.Argument(None, help="Initial URL to navigate to (optional)"),
    headless: bool = typer.Option(
        False, "--headless/--no-headless", help="Run browser in headless mode"
    ),
    browser_exe: str | None = typer.Option(
        None, help="Path to Brave/Chromium executable (optional)"
    ),
):
    """
    Start an interactive browser session.

    This opens a persistent browser and provides a REPL for debugging
    and interacting with web pages. The browser stays open between commands,
    maintaining authentication and page state.

    Example:
        browser-agent interactive https://www.patreon.com --browser-exe /usr/bin/brave-browser
        
    Available commands in the interactive session:
        - goto, extract, click, type, wait, info, links, save, html, eval
        - Type 'help' in the session for full command list
    """
    env_settings = Settings.from_env()
    settings = Settings(
        browser_executable_path=browser_exe or env_settings.browser_executable_path,
        headless=headless,
    )

    controller = PlaywrightBrowserController(
        executable_path=settings.browser_executable_path,
        headless=settings.headless,
    )
    
    session = InteractiveBrowserSession(controller)
    
    # If a URL was provided, navigate to it after starting
    if url:
        controller.start()
        from .browser.actions import Navigate
        controller.perform(Navigate(url))
        session.start()
    else:
        session.start()


@app.command()
def grok_download(
    novnc_url: str = typer.Option(
        "http://localhost:6080/vnc.html",
        help="URL of the noVNC viewer containing Grok browser"
    ),
    download_dir: str = typer.Option(
        "./grok_downloads",
        help="Directory to save downloaded images/videos"
    ),
    max_downloads: int = typer.Option(
        0,
        help="Maximum number of items to download (0 = unlimited)"
    ),
    target_type: str = typer.Option(
        "both",
        help="Type of content to download: image, video, or both"
    ),
    screenshot_dir: str = typer.Option(
        "./grok_screenshots",
        help="Directory to save screenshots for vision analysis"
    ),
    headless: bool = typer.Option(
        False, "--headless/--no-headless", help="Run browser in headless mode"
    ),
    browser_exe: str | None = typer.Option(
        None, help="Path to Brave/Chromium executable (optional)"
    ),
):
    """
    Download images/videos from Grok via noVNC container.
    
    This command automates downloading content from Grok's imagine/favorites
    tileview by controlling your browser to interact with a noVNC session.
    
    Prerequisites:
    - Grok must be open in a container running noVNC (default: http://localhost:6080/vnc.html)
    - You should already be logged in to Grok in that browser session
    - Navigate to the favorites or imagine page before running this command
    
    Example:
        browser-agent grok-download --download-dir ./my_grok_images --max-downloads 10
    
    Note: Vision analysis is not yet implemented. The agent will take screenshots
    and wait for manual input. Future versions will include automatic tile detection.
    """
    env_settings = Settings.from_env()
    settings = Settings(
        browser_executable_path=browser_exe or env_settings.browser_executable_path,
        headless=headless,
    )
    
    # Create task spec
    task = GrokDownloadTaskSpec(
        novnc_url=novnc_url,
        download_dir=download_dir,
        max_downloads=max_downloads,
        target_type=target_type,
    )
    
    # Create policy
    policy = GrokVisionPolicy(screenshot_dir=screenshot_dir)
    
    # Create browser controller
    controller = PlaywrightBrowserController(
        executable_path=settings.browser_executable_path,
        headless=settings.headless,
    )
    
    # Create and run agent
    agent = Agent(
        browser=controller,
        policy=policy,
        max_steps=100,
    )
    
    print(f"[bold green]Starting Grok download task...[/bold green]")
    print(f"noVNC URL: {novnc_url}")
    print(f"Download directory: {download_dir}")
    print(f"Screenshot directory: {screenshot_dir}")
    print()
    
    result = agent.run_task(task)
    
    if result.success:
        print(f"[bold green]✓ Task completed successfully![/bold green]")
    else:
        print(f"[bold red]✗ Task failed: {result.reason}[/bold red]")


@app.command()
def grok_setup(
    novnc_url: str = typer.Option(
        "http://localhost:6080/vnc.html",
        help="URL of the noVNC viewer containing Grok browser"
    ),
    target_page: str = typer.Option(
        "favorites",
        help="Grok page to navigate to: imagine or favorites"
    ),
    headless: bool = typer.Option(
        False, "--headless/--no-headless", help="Run browser in headless mode"
    ),
    browser_exe: str | None = typer.Option(
        None, help="Path to Brave/Chromium executable (optional)"
    ),
):
    """
    Helper command to set up and verify noVNC connection to Grok.
    
    This opens the noVNC viewer and waits for you to manually navigate
    to the target Grok page. Use this to verify your setup before running
    the download command.
    
    Example:
        browser-agent grok-setup --target-page favorites
    """
    env_settings = Settings.from_env()
    settings = Settings(
        browser_executable_path=browser_exe or env_settings.browser_executable_path,
        headless=headless,
    )
    
    # Create task spec
    task = GrokNavigateTaskSpec(
        novnc_url=novnc_url,
        target_grok_page=target_page,
    )
    
    # Create policy
    policy = GrokVisionPolicy()
    
    # Create browser controller
    controller = PlaywrightBrowserController(
        executable_path=settings.browser_executable_path,
        headless=settings.headless,
    )
    
    # Create and run agent
    agent = Agent(
        browser=controller,
        policy=policy,
        max_steps=10,
    )
    
    print(f"[bold green]Setting up Grok access via noVNC...[/bold green]")
    print(f"noVNC URL: {novnc_url}")
    print(f"Target page: {target_page}")
    print()
    
    result = agent.run_task(task)
    
    if result.success:
        print(f"[bold green]✓ Setup complete![/bold green]")
    else:
        print(f"[bold yellow]Setup exited: {result.reason}[/bold yellow]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
