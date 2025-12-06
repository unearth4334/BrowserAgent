from __future__ import annotations

import json
from rich.console import Console
from rich.table import Table

from .browser.playwright_driver import PlaywrightBrowserController
from .browser.actions import Navigate, Click, Type, WaitForSelector, ExtractLinks
from .logging_utils import get_logger

logger = get_logger(__name__)


class InteractiveBrowserSession:
    """
    Interactive browser session that maintains a persistent browser connection.
    
    Commands:
    - goto <url>              Navigate to a URL
    - extract <selector>      Extract links matching CSS selector
    - click <selector>        Click an element
    - type <selector> <text>  Type text into an element
    - wait <selector>         Wait for an element to appear
    - info                    Show current page info
    - links                   Show last extracted links
    - save <filename>         Save extracted links to JSON file
    - html                    Show page HTML (first 1000 chars)
    - eval <js>               Evaluate JavaScript on the page
    - help                    Show available commands
    - quit                    Close browser and exit
    """

    def __init__(self, controller: PlaywrightBrowserController):
        self.controller = controller
        self.console = Console()
        self.extracted_links: list[str] = []
        self.running = False

    def start(self):
        """Start the interactive session."""
        self.controller.start()
        self.running = True
        
        self.console.print("[bold green]🌐 Interactive Browser Session Started[/bold green]")
        self.console.print("[dim]Type 'help' for available commands, 'quit' to exit[/dim]\n")
        
        # Show initial page info
        self._show_info()
        
        # Main REPL loop
        while self.running:
            try:
                command = input("\n[browser] > ").strip()
                if not command:
                    continue
                
                self._handle_command(command)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'quit' to exit[/yellow]")
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                logger.exception("Command error")
        
        self.controller.stop()
        self.console.print("\n[dim]Browser session ended[/dim]")

    def _handle_command(self, command: str):
        """Handle a single command."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "help":
            self._show_help()
        elif cmd == "quit" or cmd == "exit":
            self.running = False
        elif cmd == "goto":
            if not args:
                self.console.print("[yellow]Usage: goto <url>[/yellow]")
                return
            self.controller.perform(Navigate(args))
            self._show_info()
        elif cmd == "extract":
            if not args:
                self.console.print("[yellow]Usage: extract <css-selector>[/yellow]")
                return
            self.controller.perform(ExtractLinks(args))
            self.extracted_links = self.controller.get_extracted_links()
            self.console.print(f"[green]Extracted {len(self.extracted_links)} links[/green]")
            if self.extracted_links:
                for i, link in enumerate(self.extracted_links[:10], 1):
                    self.console.print(f"  {i}. {link}")
                if len(self.extracted_links) > 10:
                    self.console.print(f"  ... and {len(self.extracted_links) - 10} more")
        elif cmd == "click":
            if not args:
                self.console.print("[yellow]Usage: click <css-selector>[/yellow]")
                return
            self.controller.perform(Click(args))
            self.console.print("[green]Clicked element[/green]")
            self._show_info()
        elif cmd == "type":
            parts = args.split(maxsplit=1)
            if len(parts) < 2:
                self.console.print("[yellow]Usage: type <css-selector> <text>[/yellow]")
                return
            selector, text = parts
            self.controller.perform(Type(selector, text))
            self.console.print(f"[green]Typed text into {selector}[/green]")
        elif cmd == "wait":
            if not args:
                self.console.print("[yellow]Usage: wait <css-selector>[/yellow]")
                return
            timeout_ms = 10000
            # Check if args has a timeout like "selector 5000"
            wait_parts = args.rsplit(maxsplit=1)
            if len(wait_parts) == 2 and wait_parts[1].isdigit():
                args = wait_parts[0]
                timeout_ms = int(wait_parts[1])
            self.controller.perform(WaitForSelector(args, timeout_ms=timeout_ms))
            self.console.print(f"[green]Element appeared: {args}[/green]")
        elif cmd == "info":
            self._show_info()
        elif cmd == "links":
            self._show_links()
        elif cmd == "save":
            if not args:
                self.console.print("[yellow]Usage: save <filename.json>[/yellow]")
                return
            self._save_links(args)
        elif cmd == "html":
            self._show_html()
        elif cmd == "eval":
            if not args:
                self.console.print("[yellow]Usage: eval <javascript-code>[/yellow]")
                return
            self._eval_js(args)
        elif cmd == "buttons":
            self._show_buttons()
        elif cmd == "inputs":
            self._show_inputs()
        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")
            self.console.print("[dim]Type 'help' for available commands[/dim]")

    def _show_help(self):
        """Show available commands."""
        table = Table(title="Available Commands", show_header=True)
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")
        
        commands = [
            ("goto <url>", "Navigate to a URL"),
            ("extract <selector>", "Extract links matching CSS selector"),
            ("click <selector>", "Click an element"),
            ("type <selector> <text>", "Type text into an element"),
            ("wait <selector> [ms]", "Wait for element (default 10s timeout)"),
            ("info", "Show current page info"),
            ("links", "Show last extracted links"),
            ("save <file.json>", "Save extracted links to JSON file"),
            ("html", "Show page HTML (first 1000 chars)"),
            ("eval <js>", "Evaluate JavaScript on the page"),
            ("buttons", "Show available buttons on page"),
            ("inputs", "Show available input fields on page"),
            ("help", "Show this help message"),
            ("quit", "Close browser and exit"),
        ]
        
        for cmd, desc in commands:
            table.add_row(cmd, desc)
        
        self.console.print(table)

    def _show_info(self):
        """Show current page information."""
        obs = self.controller.get_observation()
        
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("URL", obs.url)
        table.add_row("Title", obs.title)
        table.add_row("Buttons", str(len(obs.buttons)))
        table.add_row("Inputs", str(len(obs.inputs)))
        
        self.console.print(table)

    def _show_links(self):
        """Show extracted links."""
        if not self.extracted_links:
            self.console.print("[yellow]No links extracted yet. Use 'extract <selector>' first.[/yellow]")
            return
        
        self.console.print(f"[bold]Extracted {len(self.extracted_links)} links:[/bold]")
        for i, link in enumerate(self.extracted_links, 1):
            self.console.print(f"  {i}. {link}")

    def _save_links(self, filename: str):
        """Save extracted links to a JSON file."""
        if not self.extracted_links:
            self.console.print("[yellow]No links to save[/yellow]")
            return
        
        try:
            with open(filename, 'w') as f:
                json.dump({
                    'url': self.controller.get_observation().url,
                    'count': len(self.extracted_links),
                    'links': self.extracted_links
                }, f, indent=2)
            self.console.print(f"[green]Saved {len(self.extracted_links)} links to {filename}[/green]")
        except Exception as e:
            self.console.print(f"[red]Error saving file: {e}[/red]")

    def _show_html(self):
        """Show page HTML (truncated)."""
        if self.controller._page:
            html = self.controller._page.content()
            self.console.print("[bold]Page HTML (first 1000 chars):[/bold]")
            self.console.print(html[:1000])
            if len(html) > 1000:
                self.console.print(f"[dim]... ({len(html) - 1000} more characters)[/dim]")

    def _eval_js(self, js_code: str):
        """Evaluate JavaScript on the page."""
        if self.controller._page:
            try:
                result = self.controller._page.evaluate(js_code)
                self.console.print("[bold]Result:[/bold]")
                self.console.print(result)
            except Exception as e:
                self.console.print(f"[red]JavaScript error: {e}[/red]")

    def _show_buttons(self):
        """Show available buttons on the page."""
        obs = self.controller.get_observation()
        if not obs.buttons:
            self.console.print("[yellow]No buttons found on page[/yellow]")
            return
        
        table = Table(title="Buttons", show_header=True)
        table.add_column("#", style="cyan")
        table.add_column("Selector", style="yellow")
        table.add_column("Text", style="white")
        
        for i, btn in enumerate(obs.buttons[:20], 1):
            table.add_row(str(i), btn.selector, btn.text[:50])
        
        if len(obs.buttons) > 20:
            self.console.print(f"[dim]Showing first 20 of {len(obs.buttons)} buttons[/dim]")
        
        self.console.print(table)

    def _show_inputs(self):
        """Show available input fields on the page."""
        obs = self.controller.get_observation()
        if not obs.inputs:
            self.console.print("[yellow]No input fields found on page[/yellow]")
            return
        
        table = Table(title="Input Fields", show_header=True)
        table.add_column("#", style="cyan")
        table.add_column("Selector", style="yellow")
        table.add_column("Name", style="white")
        table.add_column("Value", style="dim")
        
        for i, inp in enumerate(obs.inputs[:20], 1):
            table.add_row(
                str(i), 
                inp.selector, 
                inp.name or "(no name)",
                (inp.value or "")[:30]
            )
        
        if len(obs.inputs) > 20:
            self.console.print(f"[dim]Showing first 20 of {len(obs.inputs)} inputs[/dim]")
        
        self.console.print(table)
