from __future__ import annotations

import json
import typer
from rich import print
from pathlib import Path

from .config import Settings
from .browser.playwright_driver import PlaywrightBrowserController
from .agent.core import Agent
from .agent.task_spec import SimpleSearchTaskSpec, PatreonCollectionTaskSpec, ComfyUIWorkflowTaskSpec
from .agent.policy_patreon import PatreonCollectionPolicy
from .agent.policy_comfyui import ComfyUIWorkflowPolicy
from .agent.workflow_runner import CanvasWorkflowRunner
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


@app.command()
def run_canvas(
    workflow: str = typer.Argument(..., help="Path to the workflow JSON file"),
    webui_url: str = typer.Option(
        "http://localhost:8188",
        help="URL of the ComfyUI WebUI"
    ),
    params: str | None = typer.Option(
        None,
        help='JSON string with parameters, e.g. \'{"node_1": {"field": "value"}}\''
    ),
    headless: bool = typer.Option(
        True, "--headless/--no-headless", help="Run browser in headless mode"
    ),
    browser_exe: str | None = typer.Option(
        None, help="Path to Brave/Chromium executable (optional)"
    ),
    max_wait: int = typer.Option(
        600, help="Maximum time in seconds to wait for workflow completion"
    ),
):
    """
    Execute a ComfyUI canvas workflow.
    
    This command will:
    1. Launch a headless browser
    2. Navigate to the ComfyUI WebUI
    3. Load the specified workflow
    4. Apply any parameters
    5. Trigger execution
    6. Wait for completion
    
    Example:
        browser-agent run-canvas /path/to/workflow.json \\
            --webui-url http://localhost:8188 \\
            --params '{"3": {"seed": 42}, "4": {"steps": 20}}'
    """
    env_settings = Settings.from_env()
    settings = Settings(
        browser_executable_path=browser_exe or env_settings.browser_executable_path,
        headless=headless,
    )
    
    # Parse parameters if provided
    parameters = {}
    if params:
        try:
            parameters = json.loads(params)
        except json.JSONDecodeError as e:
            print(f"[red]Error:[/red] Invalid JSON in params: {e}")
            raise typer.Exit(code=1)
    
    # Create controller with enhanced settings for headless mode
    controller = PlaywrightBrowserController(
        executable_path=settings.browser_executable_path,
        headless=settings.headless,
        browser_type=settings.browser_type,
        launch_timeout=settings.launch_timeout,
        navigation_timeout=settings.navigation_timeout,
        default_wait=settings.default_wait,
        extra_launch_args=settings.extra_launch_args,
        screenshot_on_error=True,
    )
    
    try:
        # Start the browser
        controller.start()
        
        # Create workflow runner
        runner = CanvasWorkflowRunner(
            browser=controller,
            webui_url=webui_url,
            max_wait_time=float(max_wait),
        )
        
        # Load workflow
        print(f"[blue]Loading workflow:[/blue] {workflow}")
        runner.load_workflow(workflow)
        
        # Set parameters
        if parameters:
            print(f"[blue]Applying parameters...[/blue]")
            for node_id, fields in parameters.items():
                for field_name, value in fields.items():
                    runner.set_parameter(node_id, field_name, value)
        
        # Execute workflow
        print(f"[blue]Executing workflow...[/blue]")
        runner.run()
        
        # Wait for completion
        print(f"[blue]Waiting for completion (max {max_wait}s)...[/blue]")
        success = runner.wait_for_completion()
        
        if success:
            print(f"[green]Success:[/green] Workflow completed successfully")
            raise typer.Exit(code=0)
        else:
            print(f"[yellow]Warning:[/yellow] Workflow did not complete within timeout")
            raise typer.Exit(code=2)
            
    except FileNotFoundError as e:
        print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(code=1)
    finally:
        controller.stop()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
