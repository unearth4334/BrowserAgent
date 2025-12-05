from __future__ import annotations

import typer
from rich import print

from .config import Settings
from .browser.playwright_driver import PlaywrightBrowserController
from .agent.core import Agent
from .agent.task_spec import SimpleSearchTaskSpec

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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
