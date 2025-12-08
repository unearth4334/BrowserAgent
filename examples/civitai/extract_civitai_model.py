#!/usr/bin/env python3
"""
Extract Civitai model information and generate markdown documentation.
"""
from __future__ import annotations

import sys
import json
import re
import yaml
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from browser_agent.server.browser_client import BrowserClient

from rich import print
from rich.console import Console

console = Console()


def load_base_model_mappings() -> dict:
    """Load base model mappings from YAML configuration."""
    config_path = Path(__file__).parent / "base_model_mappings.yml"
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config.get('mappings', {}), config.get('default', {})
    except Exception as e:
        print(f"[yellow]Warning: Could not load base model mappings: {e}[/yellow]")
        return {}, {"ecosystem": "", "basemodel": ""}


def extract_model_info(client: BrowserClient, model_url: str) -> dict:
    """Extract model information from Civitai page."""
    info = {
        "display_name": "",
        "version": "",
        "published": "",
        "creator": "",
        "ecosystem": "",
        "basemodel": "",
        "model_id": "",
        "version_id": "",
        "vae": "",
        "resolution": "",
        "cfg_scale": "",
        "sampling_steps": "",
        "denoising_strength": "",
        "sampler": "",
        "clip_skip": "",
        "notes": "",
        "positive_prompt": "",
        "negative_prompt": "",
        "upscaler": "",
        "hires_steps": "",
        "upscale": "",
    }
    
    # Extract model ID and version ID from URL
    match = re.search(r'/models/(\d+)(?:\?modelVersionId=(\d+))?', model_url)
    if match:
        info["model_id"] = match.group(1)
        info["version_id"] = match.group(2) or ""
    
    # Navigate to page
    print(f"[cyan]→[/cyan] Navigating to model page...")
    result = client.goto(model_url)
    if result.get("status") != "success":
        print(f"[red]✗ Navigation failed: {result.get('message')}[/red]")
        return info
    
    print(f"[green]✓ Loaded: {result.get('title')}[/green]")
    
    # Wait for content
    import time
    time.sleep(3)
    
    # Extract model name from h1
    print("[cyan]→[/cyan] Extracting model name...")
    result = client.extract_html("h1")
    if result.get("status") == "success":
        html = result.get("html", "")
        # Strip HTML tags
        name = re.sub(r'<[^>]+>', '', html).strip()
        info["display_name"] = name
        print(f"[dim]  Name: {name}[/dim]")
    
    # Try to extract version information
    print("[cyan]→[/cyan] Extracting version info...")
    # Look for the selected version button (has cyan icon)
    result = client.extract_html('button[data-variant="filled"]:has([color="cyan"])')
    if result.get("status") == "success":
        html = result.get("html", "")
        # Extract text content from the button label
        # The version text is after the icon, in the format: "VXVII - CrystalClear (Realism)"
        version_match = re.search(r'>([^<>]+(?:\([^)]+\))?)</', html)
        if version_match:
            version_text = version_match.group(1).strip()
            # Clean up any extra whitespace
            version_text = re.sub(r'\s+', ' ', version_text)
            info["version"] = version_text
            print(f"[dim]  Version: {info['version']}[/dim]")
    
    # Extract accordion/details content for recommended settings
    print("[cyan]→[/cyan] Looking for recommended settings...")
    
    # Try various selectors that might contain the settings
    setting_selectors = [
        '[class*="accordion"]',
        '[role="region"]',
        'dl',
        '[class*="detail"]',
        '[class*="info"]',
    ]
    
    for selector in setting_selectors:
        result = client.extract_html(selector)
        if result.get("status") == "success":
            html = result.get("html", "")
            
            # Look for common setting patterns
            if "cfg" in html.lower():
                cfg_match = re.search(r'cfg[^:]*:\s*(\d+(?:\.\d+)?)', html, re.IGNORECASE)
                if cfg_match:
                    info["cfg_scale"] = cfg_match.group(1)
            
            if "steps" in html.lower():
                steps_match = re.search(r'steps[^:]*:\s*(\d+)', html, re.IGNORECASE)
                if steps_match:
                    info["sampling_steps"] = steps_match.group(1)
            
            if "clip skip" in html.lower():
                clip_match = re.search(r'clip\s*skip[^:]*:\s*(\d+)', html, re.IGNORECASE)
                if clip_match:
                    info["clip_skip"] = clip_match.group(1)
            
            if "sampler" in html.lower():
                sampler_match = re.search(r'sampler[^:]*:\s*([^<\n]+)', html, re.IGNORECASE)
                if sampler_match:
                    info["sampler"] = sampler_match.group(1).strip()
    
    # Extract base model and ecosystem from the table
    print("[cyan]→[/cyan] Detecting ecosystem and base model...")
    result = client.extract_html('[class*="Table"]')
    if result.get("status") == "success":
        html = result.get("html", "")
        
        # Look for "Base Model" label followed by the model name
        # The structure is: <td>Base Model</td><td>...<p>SDXL 1.0</p>...</td>
        base_model_match = re.search(r'Base Model</p>.*?<td[^>]*>.*?<p[^>]*>([^<]+?)(?:<!--.*?-->)?\s*</p>', html, re.IGNORECASE | re.DOTALL)
        if base_model_match:
            base_model_str = base_model_match.group(1).strip()
            print(f"[dim]  Found Base Model: {base_model_str}[/dim]")
            
            # Load mappings and find match
            mappings, default = load_base_model_mappings()
            
            # Try exact match first
            if base_model_str in mappings:
                info["ecosystem"] = mappings[base_model_str]["ecosystem"]
                info["basemodel"] = mappings[base_model_str]["basemodel"]
            else:
                # Try case-insensitive match
                found = False
                for key, value in mappings.items():
                    if key.lower() == base_model_str.lower():
                        info["ecosystem"] = value["ecosystem"]
                        info["basemodel"] = value["basemodel"]
                        found = True
                        break
                
                if not found:
                    print(f"[yellow]  Warning: No mapping found for '{base_model_str}', using defaults[/yellow]")
                    info["ecosystem"] = default["ecosystem"]
                    info["basemodel"] = default["basemodel"]
    
    print(f"[dim]  Ecosystem: {info['ecosystem'] or 'unknown'}[/dim]")
    print(f"[dim]  Base Model: {info['basemodel'] or 'unknown'}[/dim]")
    
    # Extract published date from the table
    print("[cyan]→[/cyan] Extracting published date...")
    result = client.extract_html('[class*="Table"]')
    if result.get("status") == "success":
        html = result.get("html", "")
        # Look for "Published" label followed by date
        published_match = re.search(r'Published</p>.*?<td[^>]*>([^<]+)</td>', html, re.IGNORECASE | re.DOTALL)
        if published_match:
            date_str = published_match.group(1).strip()
            # Convert "Jun 20, 2025" to "2025-06-20"
            try:
                from datetime import datetime as dt
                parsed_date = dt.strptime(date_str, "%b %d, %Y")
                info["published"] = parsed_date.strftime("%Y-%m-%d")
                print(f"[dim]  Published: {info['published']}[/dim]")
            except:
                print(f"[dim]  Published: {date_str} (could not parse)[/dim]")
    
    return info


def generate_markdown(info: dict) -> str:
    """Generate markdown documentation from extracted info."""
    
    # Generate AIR URN
    air_urn = ""
    if info["ecosystem"] and info["model_id"] and info["version_id"]:
        air_urn = f"urn:air:{info['ecosystem']}:checkpoint:civitai:{info['model_id']}@{info['version_id']}"
    
    # Generate image path
    image_path = ""
    if info["model_id"] and info["version_id"]:
        image_path = f"Visual/Checkpoints/images/{info['model_id']}@{info['version_id']}.jpg"
    
    # Current date for published field (if not extracted)
    published_date = info.get("published") or datetime.now().strftime("%Y-%m-%d")
    
    # Build markdown
    md = f"""---
tags:
  - checkpoint
aliases:
  - {info['display_name'] or '_DisplayName_'}
version: {info['version'] or '_version_'}
published: {published_date}
creator: {info['creator'] or ''}
ecosystem: {info['ecosystem'] or '<sd / sdxl / flux1 / wan / etc.>'}
basemodel: {info['basemodel'] or '<sd1.5 / pony / sdxl1.0 / illustrious / wan-2.1 / flux1D>'}
type: checkpoint
AIR: {air_urn or f"urn:air:_ecosystem_:checkpoint:civitai:_modelId_@_versionId_"}
image: {image_path or 'Visual/Checkpoints/images/_modelId_@_versionId_.jpg'}
---

# {info['display_name'] or '_DisplayName_'} #{info['basemodel'] or '_Basemodel_'}

## [`{info['version'] or '_version_'}`][{info['version'] or '_version_'}]

### 🔧 Recommended Settings

| Setting            | Value                                       |
| ------------------ | ------------------------------------------ |
| **VAE**            | {info['vae'] or ''}                         |
| **Resolution**     | {info['resolution'] or '` `x` `'}           |
| **CFG Scale**      | {info['cfg_scale'] or '` `'}                |
| **Sampling Steps** | {info['sampling_steps'] or '` `'}           |
| **Denoising Strength**| {info['denoising_strength'] or '` `'}    |
| **Sampler**        | {info['sampler'] or '` : ` or ` : `'}       |
| **Clip Skip**      | {info['clip_skip'] or '` `'}                |

### 📝 Notes

> {info['notes'] or '...'}

---

#### ➕ Positive Prompt Template
```
{info['positive_prompt']}
```

#### ➖ Negative Prompt Template
```
{info['negative_prompt']}
```

#### 🧰 Upscaler Settings

- **Upscaler:** {info['upscaler'] or '` `'}
- **Hires Steps:** {info['hires_steps'] or '` `'}
- **Upscale:** {info['upscale'] or '` `'}
- **Denoising Strength:** {info['denoising_strength'] or '` `'}
- **Clip Skip:** {info['clip_skip'] or '` `'}

### 📥 Download

```bash
civitdl "https://civitai.com/models/{info['model_id']}?modelVersionId={info['version_id']}" "$UI_HOME"/models/Stable-diffusion
```

```bash
wget -P "$UI_HOME"/models/Stable-diffusion \\
  https://huggingface.co/...
```

[{info['version'] or '_version_'}]:https://civitai.com/models/{info['model_id']}?modelVersionId={info['version_id']}
"""
    
    return md


def main():
    if len(sys.argv) < 2:
        print("[red]Usage: extract_civitai_model.py <model_url>[/red]")
        print("\nExample:")
        print("  python examples/civitai/extract_civitai_model.py 'https://civitai.com/models/277058?modelVersionId=1920523'")
        print("\n[yellow]Note: The browser server must be running and you must be logged in![/yellow]")
        print("  python examples/civitai/browser_server.py /usr/bin/brave-browser")
        sys.exit(1)
    
    model_url = sys.argv[1]
    
    print(f"[bold cyan]Civitai Model Extractor[/bold cyan]")
    print(f"Model URL: {model_url}\n")
    
    # Connect to browser server
    client = BrowserClient()
    
    print("[bold]Step 1:[/bold] Connecting to browser server...")
    result = client.ping()
    if result.get("status") != "success":
        print("[red]✗ Could not connect to browser server[/red]")
        print("[yellow]Please start the server first:[/yellow]")
        print("  python examples/civitai/browser_server.py /usr/bin/brave-browser")
        sys.exit(1)
    print("[green]✓ Connected[/green]")
    
    # Extract model information
    print(f"\n[bold]Step 2:[/bold] Extracting model information...")
    info = extract_model_info(client, model_url)
    
    # Generate markdown
    print(f"\n[bold]Step 3:[/bold] Generating markdown...")
    markdown = generate_markdown(info)
    
    # Save to file
    model_id = info['model_id'] or 'unknown'
    version_id = info['version_id'] or 'unknown'
    output_dir = Path(f"outputs/civitai/model_{model_id}_{version_id}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"model_{model_id}_{version_id}.md"
    
    with output_file.open('w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"[bold green]✓ Saved to: {output_file}[/bold green]")
    
    # Also print to console
    print("\n" + "="*60)
    print(markdown)
    print("="*60)


if __name__ == "__main__":
    main()
