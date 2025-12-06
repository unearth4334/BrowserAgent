# Patreon Collection Link Extractor

## Overview

This feature allows you to extract all post links from a Patreon collection. The agent will:
1. Open Patreon in your browser
2. Pause and wait for you to manually authenticate
3. Navigate to the specified collection page
4. Extract all links matching the pattern for collection posts

## Usage

```bash
browser-agent patreon-collection <collection_id> --browser-exe /usr/bin/brave-browser
```

### Example

For collection ID `1611241`:

```bash
browser-agent patreon-collection 1611241 --browser-exe /usr/bin/brave-browser
```

### Workflow

1. **Browser opens**: Brave will launch and navigate to `https://www.patreon.com/`
2. **Authentication pause**: You'll see a prompt: `Please log in to Patreon, then press Enter to continue...`
   - Log in to your Patreon account manually in the browser
   - Once logged in, return to the terminal and press Enter
3. **Collection navigation**: The agent navigates to `https://www.patreon.com/collection/1611241`
4. **Link extraction**: All links matching this pattern are extracted:
   - `<a href="https://www.patreon.com/posts/<post_id>?collection=<collection_id>" class="cm-XHOpxu">`
5. **Results**: The extracted links are displayed in the terminal

## Environment Variables

You can set default browser settings:

```bash
export BROWSER_AGENT_BROWSER_EXE=/usr/bin/brave-browser
export BROWSER_AGENT_HEADLESS=0

# Then run without flags:
browser-agent patreon-collection 1611241
```

## Technical Details

### New Components Added

1. **Actions** (`browser/actions.py`):
   - `WaitForUser`: Pauses execution and waits for user input
   - `ExtractLinks`: Extracts links from page using CSS selector

2. **Task Spec** (`agent/task_spec.py`):
   - `PatreonCollectionTaskSpec`: Defines the Patreon workflow

3. **Policy** (`agent/policy_patreon.py`):
   - `PatreonCollectionPolicy`: Decision logic for the Patreon workflow

4. **Browser Controller** (`browser/playwright_driver.py`):
   - Added handling for `WaitForUser` and `ExtractLinks` actions
   - Added `get_extracted_links()` method to retrieve results

5. **CLI** (`cli.py`):
   - New `patreon-collection` command

### CSS Selector Used

The link extraction uses this CSS selector:
```css
a.cm-XHOpxu[href*="/posts/"][href*="collection={collection_id}"]
```

This matches:
- Anchor tags with class `cm-XHOpxu`
- That contain `/posts/` in the href
- That contain the collection ID parameter

## Troubleshooting

- **Links not found**: The page structure may have changed. Check the browser to see if the links have different CSS classes.
- **Authentication issues**: Make sure you're fully logged in before pressing Enter at the pause.
- **Wrong collection ID**: Verify the collection ID in the Patreon URL.
