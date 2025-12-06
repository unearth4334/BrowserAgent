# Interactive Browser Session Guide

## Starting an Interactive Session

Start a persistent browser session with Brave:

```bash
browser-agent interactive --browser-exe /usr/bin/brave-browser
```

Or start directly at a URL:

```bash
browser-agent interactive https://example.com --browser-exe /usr/bin/brave-browser
```

Or with environment variables:

```bash
export BROWSER_AGENT_BROWSER_EXE=/usr/bin/brave-browser
browser-agent interactive https://example.com
```

## Available Commands

Once in the interactive session, you can use these commands:

### Navigation & Basic Actions
- `goto <url>` - Navigate to any URL
- `info` - Show current page info (URL, title, buttons, inputs count)
- `html` - Show page HTML (first 1000 characters)

### Authentication Workflow Example
```
[browser] > goto https://example.com/login
# Manually log in in the browser window
# Authentication persists throughout the session!

[browser] > goto https://example.com/content
[browser] > wait a[href*="/items/"] 10000
[browser] > extract a[href*="/items/"]
[browser] > links
[browser] > save extracted_links.json
```

### Link Extraction
- `extract <css-selector>` - Extract all links matching the selector
  - Example: `extract a[href*="/posts/"]`
  - Example: `extract a.item-link`
- `links` - Display previously extracted links
- `save <filename.json>` - Save extracted links to JSON file

### Page Interaction
- `click <selector>` - Click an element
  - Example: `click button#submit`
- `type <selector> <text>` - Type text into input field
  - Example: `type input#search hello world`
- `wait <selector> [timeout_ms]` - Wait for element to appear
  - Example: `wait div.content`
  - Example: `wait button 5000` (5 second timeout)

### Page Inspection
- `buttons` - Show all buttons on the page (first 20)
- `inputs` - Show all input fields on the page (first 20)
- `eval <javascript>` - Execute JavaScript and see the result
  - Example: `eval document.title`
  - Example: `eval document.querySelectorAll('a').length`

### Help & Exit
- `help` - Show all commands
- `quit` or `exit` - Close browser and exit session

## Example: Extracting Links from a Page

Complete workflow for extracting links from a web page:

```bash
# Start interactive session
browser-agent interactive https://example.com --browser-exe /usr/bin/brave-browser

# In the interactive session:
[browser] > info
# (Manually authenticate in the browser window if needed)

[browser] > goto https://example.com/collection/1234
[browser] > wait a[href*="/items/"] 10000
[browser] > extract a[href*="/items/"]
[browser] > links
[browser] > save collection_1234.json
[browser] > quit
```

## Debugging Tips

1. **Check page structure:**
   ```
   [browser] > html
   [browser] > buttons
   [browser] > inputs
   ```

2. **Test CSS selectors with JavaScript:**
   ```
   [browser] > eval document.querySelectorAll('a[href*="/items/"]').length
   ```

3. **Try different selectors if extraction fails:**
   ```
   [browser] > extract a[href*="/items/"]
   [browser] > extract a.item-link
   [browser] > eval document.querySelector('a').outerHTML
   ```

4. **Wait for dynamic content:**
   ```
   [browser] > wait div.content 15000
   [browser] > extract a
   ```

## Benefits of Interactive Mode

- ✅ **Persistent authentication** - Log in once, use throughout session
- ✅ **Debug and iterate** - Test selectors and commands before scripting
- ✅ **Manual intervention** - Handle CAPTCHAs, 2FA, etc.
- ✅ **Save work** - Export data to JSON files
- ✅ **JavaScript inspection** - Run custom JS to understand page structure

## Saved JSON Format

When you use `save filename.json`, the file contains:

```json
{
  "url": "https://example.com/collection/1234",
  "count": 42,
  "links": [
    "https://example.com/items/12345",
    "https://example.com/items/67890",
    ...
  ]
}
```

## For Site-Specific Examples

See the `examples/` directory for specific use cases:
- `examples/patreon/` - Patreon collection extraction
