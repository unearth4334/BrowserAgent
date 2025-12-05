# Interactive Browser Session Guide

## Starting an Interactive Session

Start a persistent browser session with Brave:

```bash
browser-agent interactive --browser-exe /usr/bin/brave-browser
```

Or start directly at a URL:

```bash
browser-agent interactive https://www.patreon.com --browser-exe /usr/bin/brave-browser
```

Or with environment variables:

```bash
export BROWSER_AGENT_BROWSER_EXE=/usr/bin/brave-browser
browser-agent interactive https://www.patreon.com
```

## Available Commands

Once in the interactive session, you can use these commands:

### Navigation & Basic Actions
- `goto <url>` - Navigate to any URL
- `info` - Show current page info (URL, title, buttons, inputs count)
- `html` - Show page HTML (first 1000 characters)

### Authentication Workflow Example
```
[browser] > goto https://www.patreon.com
# Manually log in to Patreon in the browser window
# Authentication persists throughout the session!

[browser] > goto https://www.patreon.com/collection/1611241?view=expanded
[browser] > wait a[href*="/posts/"] 10000
[browser] > extract a[href*="/posts/"][href*="collection=1611241"]
[browser] > links
[browser] > save patreon_links.json
```

### Link Extraction
- `extract <css-selector>` - Extract all links matching the selector
  - Example: `extract a[href*="/posts/"]`
  - Example: `extract a.cm-XHOpxu`
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

## Patreon Collection Extraction Example

Complete workflow for extracting Patreon collection links:

```bash
# Start interactive session
browser-agent interactive https://www.patreon.com --browser-exe /usr/bin/brave-browser

# In the interactive session:
[browser] > info
# (Manually authenticate in the browser window)

[browser] > goto https://www.patreon.com/collection/1611241?view=expanded
[browser] > wait a[href*="/posts/"] 10000
[browser] > extract a[href*="/posts/"][href*="collection=1611241"]
[browser] > links
[browser] > save collection_1611241.json
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
   [browser] > eval document.querySelectorAll('a[href*="/posts/"]').length
   ```

3. **Try different selectors if extraction fails:**
   ```
   [browser] > extract a[href*="/posts/"]
   [browser] > extract a.post-link
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
  "url": "https://www.patreon.com/collection/1611241?view=expanded",
  "count": 42,
  "links": [
    "https://www.patreon.com/posts/12345?collection=1611241",
    "https://www.patreon.com/posts/67890?collection=1611241",
    ...
  ]
}
```
