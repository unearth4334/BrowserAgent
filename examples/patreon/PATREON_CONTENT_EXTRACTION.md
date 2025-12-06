# Patreon Content Extraction Guide

This guide explains how to extract individual post content from Patreon collections using the Browser Agent.

## Overview

The content extraction workflow consists of two steps:

1. **Extract collection links** - Get all post URLs from a collection
2. **Extract post content** - Visit each post and extract the description HTML

There are two modes of operation:
- **Standalone mode** - Opens a new browser for each operation
- **Client-server mode** - Uses a persistent browser instance (recommended for multiple extractions)

## Prerequisites

- Browser Agent installed with dev dependencies
- Playwright browsers installed (`playwright install chromium`)
- Valid Patreon account with access to the collection

## Step 1: Extract Collection Links

First, extract all post links from a collection:

```bash
source .venv/bin/activate
python scripts/extract_patreon_collection.py <collection_id> [browser_exe]
```

**Example:**
```bash
python scripts/extract_patreon_collection.py 1611241 /usr/bin/brave-browser
```

This will:
1. Open the browser and navigate to Patreon
2. Prompt you to log in
3. Navigate to the collection page
4. Load all collection items (clicking "Load more" as needed)
5. Extract all post links
6. Save results to `outputs/patreon_collection_<collection_id>.json`

**Output format:**
```json
{
  "collection_id": "1611241",
  "url": "https://www.patreon.com/collection/1611241?view=expanded",
  "count": 22,
  "links": [
    "https://www.patreon.com/posts/144726506?collection=1611241",
    ...
  ]
}
```

## Step 2: Extract Post Content

Extract the description HTML from individual posts:

### Option A: Client-Server Mode (Recommended)

This mode uses a persistent browser instance, so you only need to authenticate once for multiple extractions.

**1. Start the browser server:**
```bash
python scripts/browser_server.py /usr/bin/brave-browser
```

The server will:
- Open a browser window
- Navigate to Patreon
- Wait for you to log in
- Start listening for commands on port 9999

**2. Extract content (in a separate terminal):**
```bash
source .venv/bin/activate
python scripts/extract_patreon_content_client.py <collection_id> [post_index_or_url]
```

**Examples:**

Extract from the first post:
```bash
python scripts/extract_patreon_content_client.py 1611241
```

Extract from a specific post index:
```bash
python scripts/extract_patreon_content_client.py 1611241 5
```

Extract from a specific URL:
```bash
python scripts/extract_patreon_content_client.py 1611241 https://www.patreon.com/posts/144726506
```

**Advantages:**
- Authenticate only once
- Fast extraction (no browser startup delay)
- Extract multiple posts in succession
- Browser stays open for inspection

### Option B: Standalone Mode

Opens a new browser for each extraction operation.

```bash
python scripts/extract_patreon_content.py <collection_id> [browser_exe] [post_index_or_url]
```

**Parameters:**
- `collection_id`: The collection ID (required)
- `browser_exe`: Path to browser executable (default: `/usr/bin/brave-browser`)
- `post_index_or_url`: Post index (0-based) or full URL (default: `0`)

**Examples:**

```bash
# Extract from first post
python scripts/extract_patreon_content.py 1611241

# Extract from specific post
python scripts/extract_patreon_content.py 1611241 /usr/bin/brave-browser 5
```

Extract from the first post:
```bash
python scripts/extract_patreon_content.py 1611241
```

Extract from a specific post index:
```bash
python scripts/extract_patreon_content.py 1611241 /usr/bin/brave-browser 5
```

Extract from a specific URL:
```bash
python scripts/extract_patreon_content.py 1611241 /usr/bin/brave-browser https://www.patreon.com/posts/144726506
```

### Output Structure

Content is saved to `outputs/POST_<post_id>_<post_name>/`:

```
outputs/
├── POST_144726506_Anya Taylor-Joy [ SDXL ]/
│   ├── 144726506-desc.html    # Description HTML
│   └── 144726506-meta.json    # Metadata
└── POST_144669916_Ana De Armas [Pony SDXL]/
    ├── 144669916-desc.html
    └── 144669916-meta.json
```

**HTML file (`<post_id>-desc.html`):**
Contains the raw HTML of the post description, including:
- Paragraphs with formatting
- Lists (ordered and unordered)
- Links
- Blockquotes
- All inline styling

**Metadata file (`<post_id>-meta.json`):**
```json
{
  "post_id": "144726506",
  "post_url": "https://www.patreon.com/posts/144726506?collection=1611241",
  "collection_id": "1611241",
  "post_name": "Anya Taylor-Joy [ SDXL ]",
  "title": "Anya Taylor-Joy [ SDXL ] | Patreon",
  "html_length": 3400
}
```

## How It Works

### New Action Type: `ExtractHTML`

Added a new action to the browser controller:

```python
from browser_agent.browser.actions import ExtractHTML

# Extract HTML from a selector
controller.perform(ExtractHTML('div[class*="cm-LIiDtl"]'))
html_content = controller.get_extracted_html()
```

### Selector Strategy

The script tries multiple CSS selectors to find the description content:

1. `div[class*="cm-LIiDtl"]` - Main content div (Patreon's class naming)
2. `div[data-tag="post-content"]` - Alternative attribute
3. `article div[class*="cm-"]` - Article content div

This ensures compatibility even if Patreon changes their class names.

### Workflow

1. **Authenticate**: Opens browser and prompts for login
2. **Get collection name**: Visits collection page to extract the collection title
3. **Navigate to post**: Visits the specified post URL
4. **Wait for content**: Waits for content div to load
5. **Extract HTML**: Uses `ExtractHTML` action to get description HTML
6. **Save files**: Saves HTML and metadata to organized directory structure

## Tips

- **Manual authentication**: The script keeps the browser open between steps, allowing you to handle any authentication challenges
- **Inspect before closing**: The browser stays open after extraction so you can verify the content was captured correctly
- **Collection names**: The script sanitizes collection names to create valid directory names
- **Error handling**: If content extraction fails, the script provides diagnostic information

## Batch Processing

To extract content from all posts in a collection:

### Using Client-Server Mode (Recommended)

**1. Start the browser server:**
```bash
python scripts/browser_server.py /usr/bin/brave-browser
```

**2. Run batch extraction script:**
```bash
#!/bin/bash
COLLECTION_ID="1611241"

# Load collection data
COUNT=$(cat outputs/patreon_collection_${COLLECTION_ID}.json | jq '.count')

echo "Extracting $COUNT posts from collection $COLLECTION_ID..."

# Extract each post
for i in $(seq 0 $((COUNT - 1))); do
  echo ""
  echo "=== Processing post $((i + 1))/$COUNT ==="
  python scripts/extract_patreon_content_client.py $COLLECTION_ID $i
  sleep 1  # Brief pause between requests
done

echo ""
echo "✓ Extraction complete!"
```

**3. Stop the server when done** (Ctrl+C in the server terminal)

### Using Standalone Mode

```bash
#!/bin/bash
COLLECTION_ID="1611241"
BROWSER="/usr/bin/brave-browser"

# Load collection data
COUNT=$(cat outputs/patreon_collection_${COLLECTION_ID}.json | jq '.count')

echo "Extracting $COUNT posts..."

# Extract each post
for i in $(seq 0 $((COUNT - 1))); do
  echo "Processing post $i..."
  python scripts/extract_patreon_content.py $COLLECTION_ID $BROWSER $i
done

echo "Done!"
```

**Note:** Standalone mode requires re-authentication for each post, which is impractical for batch processing.

## Troubleshooting

**Problem**: "Collection data not found" error

**Solution**: Run `extract_patreon_collection.py` first to get the post links

---

**Problem**: No HTML content extracted

**Solution**: 
- Check if you're logged in to Patreon
- Verify you have access to the collection
- Inspect the page HTML to find the correct selector
- The script will keep the browser open for manual inspection

---

**Problem**: Invalid post index error

**Solution**: Check the valid range in the error message (0 to count-1)

## API Reference

### ExtractHTML Action

```python
@dataclass
class ExtractHTML:
    """Extract HTML content matching a selector from the current page."""
    selector: str  # CSS selector to match elements
```

### Controller Methods

```python
# Extract HTML using an action
controller.perform(ExtractHTML('div.content'))

# Get the extracted HTML
html: str = controller.get_extracted_html()
```

## Future Enhancements

Potential improvements:
- Batch extraction mode (extract all posts automatically)
- Progress tracking and resume capability
- Extract additional post metadata (images, attachments, comments)
- Support for other content types (images, videos)
- Export to different formats (Markdown, PDF)
