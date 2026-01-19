---
name: createCatalogPage
description: Extract metadata from a URL and create a formatted catalog page
argument-hint: URL of the resource to catalog
---
Create a catalog page for the resource at the specified URL.

Steps:
1. Ensure the browser server is running (start if needed on the configured port)
2. Determine the resource type from the page (check title or content indicators)
3. Select and run the appropriate extraction script for that resource type
4. Extract relevant metadata including:
   - Creator/author
   - Name and version
   - Type/category and base model
   - Published date
   - Special attributes (trigger words, settings, etc.)
5. Generate a markdown file with structured frontmatter and content sections
6. Copy the file to the target directory following the naming convention
7. Confirm successful creation with key extracted metadata

If automated extraction times out, try manual navigation to verify page accessibility before retrying.

## Resource Type Detection

Identify the resource type from the page title or content:
- **LoRA**: Title contains "LoRA" (e.g., "Model Name | Stable Diffusion XL LoRA | Civitai")
- **Checkpoint**: Title contains "Checkpoint" (e.g., "Model Name | Stable Diffusion Checkpoint | Civitai")

## Extraction Scripts

Based on resource type, use the appropriate script:
- **Checkpoints**: `examples/civitai/extract_civitai_model.py`
- **LoRAs**: `examples/civitai/extract_civitai_lora.py`

Both scripts accept a Civitai URL with model ID and version ID:
```bash
/path/to/.venv/bin/python examples/civitai/extract_civitai_[model|lora].py 'https://civitai.com/models/{id}?modelVersionId={version_id}'
```

## Naming Conventions

### Checkpoints
Format: `CHKPT-{Name}-{Basemodel} ({version}).md`

Examples:
- `CHKPT-DAMN!-Illustrious (v2.0).md`
- `CHKPT-IllustrijEVO-Illustrious (Illust_v2).md`
- `CHKPT-BetterDays-Illustrious (v2.md`

### LoRAs
Format: `LoRA-{Name}-{Basemodel} ({version}).md`

Examples:
- `LoRA-Aoimoku-SDXL (XL).md`
- `LoRA-PolaroidSpirit-Pony (v1).md`
- `LoRA-PerfectFingering-SD15 (Wan2_2 high-low pair).md`

**Note**: For high-low pair LoRAs, include the pairing information in the version field.

## Target Directories

Files must be copied to the appropriate location in the Obsidian vault:

- **Checkpoints**: `/home/sdamk/.obsidian/AI/Visual/Checkpoints/checkpoints/`
- **LoRAs**: `/home/sdamk/.obsidian/AI/Visual/LoRAs/loras/`

## Base Model Mapping

The extraction scripts use `base_model_mappings.yml` to map Civitai's base model strings to standardized ecosystem/basemodel/hashtag values:

Example mappings:
- `"SDXL 1.0"` → ecosystem: `sdxl`, basemodel: `sdxl1.0`, hashtag: `SDXL1_0`
- `"Pony"` → ecosystem: `pony`, basemodel: `pony`, hashtag: `Pony`
- `"Illustrious"` → ecosystem: `illustrious`, basemodel: `illustrious`, hashtag: `Illustrious`

The hashtag is used in the markdown heading format: `# {ModelName} #{Hashtag}`

## Output Structure

Extraction scripts generate files in: `outputs/civitai/model_{id}_{version_id}/`

Files generated:
- Checkpoints: `checkpoint_{id}_{version_id}.md`
- LoRAs: `lora_{id}_{version_id}.md`

These temporary files must be copied to the target directories with proper naming.

## Troubleshooting

### Navigation Timeouts
If extraction fails with "Timeout 30000ms exceeded":
1. Try manual navigation to verify page is accessible:
   ```python
   from browser_agent.server.browser_client import BrowserClient
   client = BrowserClient('localhost', 9999)
   client.goto('https://civitai.com/models/{id}?modelVersionId={version_id}')
   ```
2. Check page title to confirm resource type
3. Retry extraction with correct script

### Server Conflicts
If port 9999 is already in use, the server will prompt to terminate the existing process:
```
Found process on port 9999 (PID: xxxxx)
Terminate this process and start new server? [y/N]:
```
