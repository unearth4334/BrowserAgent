#!/usr/bin/env python3
"""
Extract all posts from a Patreon collection.
This script processes all posts in a collection sequentially.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from browser_client import BrowserClient
from extract_patreon_content_client import (
    load_collection_data,
    extract_post_content,
    extract_attachments,
    save_post_content,
    download_attachments,
    sanitize_filename
)
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn


def main():
    if len(sys.argv) < 2:
        print("[red]Usage: extract_all_posts.py <collection_id> [start_index][/red]")
        print("\nExamples:")
        print("  # Extract all posts from beginning")
        print("  python scripts/extract_all_posts.py 1611241")
        print("")
        print("  # Resume from post index 5")
        print("  python scripts/extract_all_posts.py 1611241 5")
        print("")
        print("[yellow]Note: The browser server must be running first![/yellow]")
        print("  python scripts/browser_server.py /usr/bin/brave-browser")
        sys.exit(1)
    
    collection_id = sys.argv[1]
    start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    print(f"[bold cyan]Patreon Collection Batch Extractor[/bold cyan]")
    print(f"Collection ID: {collection_id}\n")
    
    # Connect to browser server
    client = BrowserClient()
    
    print("Connecting to browser server...")
    result = client.ping()
    if result.get("status") != "success":
        print(f"[red]✗ Could not connect to browser server[/red]")
        print("[yellow]Start the server first:[/yellow]")
        print("  python scripts/browser_server.py /usr/bin/brave-browser")
        return
    print("[green]✓ Connected to browser server[/green]\n")
    
    # Load collection data
    print("Loading collection data...")
    try:
        collection_data = load_collection_data(collection_id)
    except FileNotFoundError as e:
        print(f"[red]✗ {e}[/red]")
        return
    
    links = collection_data.get("links", [])
    if not links:
        print("[red]✗ No links found in collection data[/red]")
        return
    
    print(f"[green]✓ Found {len(links)} posts[/green]")
    if start_index > 0:
        print(f"[yellow]Starting from post {start_index + 1}/{len(links)}[/yellow]")
    print("")
    
    # Process each post
    successful = 0
    failed = []
    skipped = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=None
    ) as progress:
        task = progress.add_task("[cyan]Processing posts...", total=len(links) - start_index)
        
        for i in range(start_index, len(links)):
            post_url = links[i]
            post_id = post_url.split("/posts/")[1].split("?")[0] if "/posts/" in post_url else "unknown"
            
            print(f"\n[bold]Post {i + 1}/{len(links)}[/bold] (ID: {post_id})")
            print(f"[dim]URL: {post_url}[/dim]")
            
            try:
                # Extract content
                print("[cyan]→[/cyan] Extracting content...")
                content = extract_post_content(client, post_url, "")
                
                if not content:
                    print("[red]✗ Failed to extract content[/red]")
                    failed.append((post_id, post_url, "Content extraction failed"))
                    progress.update(task, advance=1)
                    time.sleep(2)  # Brief pause before next post
                    continue
                
                # Extract post name from title
                post_title = content.get("title", "Unknown")
                post_name = post_title.split("|")[0].strip() if "|" in post_title else post_title
                
                # Check if already processed
                folder_name = f"POST_{post_id}_{sanitize_filename(post_name)}"
                output_dir = Path("outputs/patreon") / folder_name
                
                if output_dir.exists():
                    html_file = output_dir / f"{post_id}-desc.html"
                    if html_file.exists():
                        print(f"[yellow]⊘ Already extracted, skipping[/yellow]")
                        skipped += 1
                        progress.update(task, advance=1)
                        continue
                
                # Extract attachments
                print("[cyan]→[/cyan] Extracting attachments...")
                attachments = extract_attachments(client)
                
                # Save content
                print("[cyan]→[/cyan] Saving content...")
                save_post_content(post_id, post_name, post_url, collection_id, content, attachments)
                
                # Download attachments
                if attachments:
                    print("[cyan]→[/cyan] Downloading attachments...")
                    downloaded = download_attachments(client, attachments, output_dir)
                    print(f"[green]✓ Downloaded {len(downloaded)}/{len(attachments)} file(s)[/green]")
                else:
                    print("[dim]No attachments to download[/dim]")
                
                successful += 1
                print(f"[green]✓ Post {i + 1} complete[/green]")
                
            except KeyboardInterrupt:
                print(f"\n[yellow]Interrupted by user[/yellow]")
                print(f"\nTo resume from this point, run:")
                print(f"  python scripts/extract_all_posts.py {collection_id} {i}")
                break
            
            except Exception as e:
                print(f"[red]✗ Error processing post: {e}[/red]")
                failed.append((post_id, post_url, str(e)))
            
            finally:
                progress.update(task, advance=1)
                time.sleep(1)  # Brief pause between posts to avoid rate limiting
    
    # Summary
    print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    print(f"[bold]Extraction Summary[/bold]")
    print(f"[bold cyan]{'='*60}[/bold cyan]")
    print(f"[green]✓ Successful:[/green] {successful}")
    print(f"[yellow]⊘ Skipped:[/yellow] {skipped}")
    print(f"[red]✗ Failed:[/red] {len(failed)}")
    print(f"[bold]Total processed:[/bold] {successful + skipped + len(failed)}/{len(links)}")
    
    if failed:
        print(f"\n[bold red]Failed Posts:[/bold red]")
        for post_id, url, error in failed:
            print(f"  • Post {post_id}: {error}")
            print(f"    {url}")


if __name__ == "__main__":
    # Add parent directory to path to import other scripts
    sys.path.insert(0, str(Path(__file__).parent))
    main()
