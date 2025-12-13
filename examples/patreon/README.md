# Patreon Content Extraction Examples

This directory contains example scripts demonstrating how to use the browser-agent utility
for extracting content from Patreon.

## Prerequisites

1. Install browser-agent:
   ```bash
   pip install -e .[dev]
   playwright install chromium
   ```

2. Have a Patreon account with access to the collections you want to extract.

## Scripts

### Browser Server/Client Architecture

- **`browser_server.py`** - Starts a persistent browser server that maintains authentication
- **`browser_client.py`** - Client library for communicating with the browser server

### Collection Extraction

- **`extract_patreon_collection.py`** - Extract collection links (standalone browser session)
- **`extract_patreon_client.py`** - Extract collection links using the browser server
- **`extract_collection_links.py`** - Alternative collection link extraction using JavaScript

### Content Extraction

- **`extract_patreon_content.py`** - Extract post content (standalone browser session)
- **`extract_patreon_content_client.py`** - Extract post content and attachments using browser server
- **`extract_all_posts.py`** - Batch extract all posts from a collection

### Utilities

- **`debug_page_structure.py`** - Debug script to inspect page structure

## Quick Start

### Method 1: Using Browser Server (Recommended for multiple extractions)

1. Start the browser server:
   ```bash
   python examples/patreon/browser_server.py /usr/bin/brave-browser
   ```

2. Log in to Patreon in the browser, then press Enter to start the server.

3. In another terminal, extract collection links:
   ```bash
   python examples/patreon/extract_patreon_client.py 1611241
   ```

4. Extract content from posts:
   ```bash
   python examples/patreon/extract_patreon_content_client.py 1611241
   ```

### Method 2: Standalone Scripts (For single extractions)

```bash
python examples/patreon/extract_patreon_collection.py 1611241 /usr/bin/brave-browser
```

## Output

Extracted content is saved to the `outputs/` directory:

- `outputs/patreon_collection_{id}.json` - Collection metadata and links
- `outputs/POST_{post_id}_{name}/` - Individual post content
  - `{post_id}-desc.html` - Post description HTML
  - `{post_id}-meta.json` - Post metadata
  - `{post_id}-attachments.json` - Attachment information
  - `attachments/` - Downloaded attachment files

## Custom Policy and Task Spec

This example also demonstrates how to create custom policies and task specs:

- **`policy_patreon.py`** - Custom policy for Patreon collection extraction
- **`task_spec_patreon.py`** - Task specification for Patreon tasks

These can be used with the browser-agent's Agent class for automated workflows.

## Testing

The `tests/` directory contains integration test scripts:

- **`test_extract_all_251893.py`** - Test extracting all posts from collection 251893
- **`test_extract_collection_251893.py`** - Test collection link extraction
- **`test_load_more_251893.py`** - Test pagination and load-more functionality
- **`test_inspect_page.py`** - Inspect page structure for debugging
- **`test_aggressive_scroll.py`** - Test aggressive scrolling for lazy-loaded content

These are practical test scripts that work with actual Patreon collections (requires authentication).
