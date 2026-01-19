from __future__ import annotations

import typer
from rich import print

from .config import Settings
from .browser.playwright_driver import PlaywrightBrowserController
from .interactive_session import InteractiveBrowserSession

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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
