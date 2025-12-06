from __future__ import annotations

import typer
from rich import print

from .config import Settings
from .browser.playwright_driver import PlaywrightBrowserController
from .agent.core import Agent
from .agent.task_spec import SimpleSearchTaskSpec
from .interactive_session import InteractiveBrowserSession
from .server.browser_server import BrowserServer

app = typer.Typer(help="Browser agent CLI")


@app.command()
def simple_search(
    query: str = typer.Argument(..., help="Search query string"),
    headless: bool = typer.Option(
        True, "--headless/--no-headless", help="Run browser in headless mode"
    ),
    browser_exe: str | None = typer.Option(
        None, help="Path to Brave/Chromium executable (optional)"
    ),
):
    """
    Run the simple search demo task.

    Example:
        browser-agent simple-search "hello world"
    """
    env_settings = Settings.from_env()
    settings = Settings(
        browser_executable_path=browser_exe or env_settings.browser_executable_path,
        headless=headless if browser_exe is not None else env_settings.headless,
    )

    controller = PlaywrightBrowserController(
        executable_path=settings.browser_executable_path,
        headless=settings.headless,
    )
    task = SimpleSearchTaskSpec(query=query)
    agent = Agent()

    try:
        result = agent.run_task(task, controller)
        if result.success:
            print(f"[green]Success:[/green] {result.reason}")
            if result.final_observation:
                print(f"Final URL: {result.final_observation.url}")
                print(f"Title: {result.final_observation.title}")
        else:
            print(f"[red]Failure:[/red] {result.reason}")
    finally:
        controller.stop()


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
        browser-agent interactive https://example.com --browser-exe /usr/bin/brave-browser
        
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
def server(
    url: str | None = typer.Argument(None, help="Initial URL to navigate to (optional)"),
    port: int = typer.Option(9999, help="Port to listen on"),
    browser_exe: str | None = typer.Option(
        None, help="Path to Brave/Chromium executable (optional)"
    ),
    no_wait: bool = typer.Option(
        False, "--no-wait", help="Don't wait for user input before starting server"
    ),
):
    """
    Start a persistent browser server.

    The server maintains a browser instance and accepts commands via socket.
    This is useful for workflows that require authentication - authenticate once,
    then run multiple scripts against the authenticated session.

    Example:
        browser-agent server https://example.com --browser-exe /usr/bin/brave-browser
        
    Then connect from another terminal using BrowserClient:
        from browser_agent.server import BrowserClient
        client = BrowserClient()
        client.goto("https://example.com/page")
    """
    env_settings = Settings.from_env()
    browser_path = browser_exe or env_settings.browser_executable_path

    browser_server = BrowserServer(browser_exe=browser_path, port=port)
    browser_server.start(initial_url=url, wait_for_auth=not no_wait)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
