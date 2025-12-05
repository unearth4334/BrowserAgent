from __future__ import annotations

import typer
from rich import print

from .config import Settings
from .browser.playwright_driver import PlaywrightBrowserController
from .agent.core import Agent
from .agent.task_spec import SimpleSearchTaskSpec, PatreonCollectionTaskSpec
from .agent.policy_patreon import PatreonCollectionPolicy
from .interactive_session import InteractiveBrowserSession

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
def patreon_collection(
    collection_id: str = typer.Argument(..., help="Patreon collection ID"),
    headless: bool = typer.Option(
        False, "--headless/--no-headless", help="Run browser in headless mode"
    ),
    browser_exe: str | None = typer.Option(
        None, help="Path to Brave/Chromium executable (optional)"
    ),
):
    """
    Extract links from a Patreon collection.

    This command will:
    1. Open Patreon in your browser
    2. Pause for you to authenticate
    3. Navigate to the specified collection
    4. Extract all post links from that collection

    Example:
        browser-agent patreon-collection 1611241 --browser-exe /usr/bin/brave-browser
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
    task = PatreonCollectionTaskSpec(collection_id=collection_id)
    agent = Agent(policy=PatreonCollectionPolicy(), max_steps=10)

    try:
        result = agent.run_task(task, controller)
        if result.success:
            print(f"[green]Success:[/green] {result.reason}")
            if result.final_observation:
                print(f"Final URL: {result.final_observation.url}")
            
            # Display extracted links
            links = controller.get_extracted_links()
            if links:
                print(f"\n[bold]Found {len(links)} links:[/bold]")
                for link in links:
                    print(f"  • {link}")
            else:
                print("[yellow]No links found matching the pattern.[/yellow]")
                print("[dim]Tip: The page might use different selectors. Try inspecting the page HTML to verify the link structure.[/dim]")
                # Try a broader extraction as fallback
                print("\n[dim]Attempting broader search for any post links...[/dim]")
                from browser_agent.browser.actions import ExtractLinks
                controller.perform(ExtractLinks('a[href*="/posts/"]'))
                fallback_links = controller.get_extracted_links()
                if fallback_links:
                    print(f"\n[bold]Found {len(fallback_links)} post links (without collection filter):[/bold]")
                    for link in fallback_links[:20]:  # Show first 20
                        print(f"  • {link}")
                    if len(fallback_links) > 20:
                        print(f"  ... and {len(fallback_links) - 20} more")
                else:
                    print("[yellow]No post links found at all. The page structure may have changed.[/yellow]")
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
