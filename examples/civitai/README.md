# Civitai Model Extractor

Extract model information from Civitai and generate markdown documentation.

## Setup

1. **Start the browser server** (with authentication):
   ```bash
   python examples/civitai/browser_server.py /usr/bin/brave-browser
   ```
   
   This will:
   - Open a browser window at https://civitai.com/
   - Wait for you to login
   - Prompt you to press Enter when ready
   - Start the server to accept commands

2. **Login to Civitai** in the browser window that opens

3. **Press Enter** in the terminal to start the server

## Usage

### Examine a Model Page Structure

Use this to understand what data is available on a model page:

```bash
python examples/civitai/examine_civitai.py 'https://civitai.com/models/277058?modelVersionId=1920523'
```

This will:
- Extract HTML from various sections
- Save HTML files to `outputs/civitai/` for inspection
- Show what selectors found content

### Extract Model Information

Extract model info and generate markdown documentation:

```bash
python examples/civitai/extract_civitai_model.py 'https://civitai.com/models/277058?modelVersionId=1920523'
```

This will:
- Extract model name, version, settings, etc.
- Generate a markdown file with the template format
- Save to `outputs/civitai/model_<modelId>_<versionId>.md`
- Print the generated markdown to console

### Send Commands Directly

You can also use the browser client to send commands directly:

```bash
# Navigate to a model
python examples/civitai/browser_client.py goto 'https://civitai.com/models/277058?modelVersionId=1920523'

# Extract HTML from a selector
python examples/civitai/browser_client.py extract_html 'h1'

# Get page info
python examples/civitai/browser_client.py info

# Wait for an element
python examples/civitai/browser_client.py wait '[class*="accordion"]' 5000

# View server logs
python examples/civitai/browser_client.py logs -f
```

## Generated Markdown Template

The extractor generates markdown documentation with this structure:

```markdown
---
tags:
  - checkpoint
aliases:
  - DisplayName
version: v1.0
published: YYYY-MM-DD
creator: CreatorName
ecosystem: sdxl
basemodel: sdxl1.0
type: checkpoint
AIR: urn:air:sdxl:checkpoint:civitai:277058@1920523
image: Visual/Checkpoints/images/277058@1920523.jpg
---

# Model Name #Basemodel

## [version][version]

### 🔧 Recommended Settings
- VAE, Resolution, CFG Scale, etc.

### 📝 Notes
- Model-specific notes

### 📥 Download
- civitdl command
- wget command
```

## Output Directory Structure

```
outputs/civitai/
├── model_<modelId>_<versionId>.md    # Generated markdown
├── full_page.html                     # Full page HTML (from examine script)
└── accordion_*.html                   # Accordion sections (from examine script)
```

## Tips

1. **Login First**: Make sure you're logged into Civitai before running the extraction scripts

2. **Inspect HTML**: Use the `examine_civitai.py` script first to understand the page structure

3. **Manual Editing**: The generated markdown is a starting point - you'll likely need to manually fill in some fields

4. **Browser Visibility**: The server runs in non-headless mode so you can see what's happening

## Troubleshooting

### "Could not connect to browser server"
- Make sure the browser server is running
- Check that it's listening on port 9999
- Try: `python examples/civitai/browser_client.py ping`

### "Navigation failed"
- Check that you're logged into Civitai
- Verify the URL is correct
- Try manually navigating in the browser first

### Missing Data
- Some fields may not be extractable from all model pages
- Use `examine_civitai.py` to see what data is available
- Manually inspect the saved HTML files in `outputs/civitai/`

## Architecture

- **browser_server.py**: Wrapper around main server implementation, starts at civitai.com
- **browser_client.py**: Wrapper around main client implementation
- **examine_civitai.py**: Debug tool to inspect page structure
- **extract_civitai_model.py**: Main extraction logic and markdown generation
