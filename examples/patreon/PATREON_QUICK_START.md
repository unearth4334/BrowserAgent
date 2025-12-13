# Quick Reference: Patreon Collection Extraction

## Quick Start (Interactive Mode - RECOMMENDED)

This method lets you authenticate once and maintain the session:

```bash
# Start interactive session at Patreon
browser-agent interactive https://www.patreon.com --browser-exe /usr/bin/brave-browser

# Then run these commands:
# 1. Log in manually in the browser (one time!)
# 2. Navigate to your collection:
goto https://www.patreon.com/collection/1611241?view=expanded

# 3. Wait for content to load:
wait a[href*="/posts/"] 10000

# 4. Extract links:
extract a[href*="/posts/"][href*="collection=1611241"]

# 5. View the links:
links

# 6. Save to file:
save patreon_collection_1611241.json

# Done! The browser stays open for more commands.
# Type 'quit' when finished.
```

## One-Shot Mode (Requires Authentication Each Time)

If you prefer automated mode, use the patreon-collection command:

```bash
browser-agent patreon-collection 1611241 --browser-exe /usr/bin/brave-browser
```

⚠️ **Note:** This closes the browser after completion, so you need to re-authenticate each run.

## Environment Variables (Optional)

Set these to avoid typing flags every time:

```bash
export BROWSER_AGENT_BROWSER_EXE=/usr/bin/brave-browser
export BROWSER_AGENT_HEADLESS=0

# Then simply:
browser-agent interactive https://www.patreon.com
```

## Troubleshooting

### No links found?

Try broader selectors in interactive mode:

```
[browser] > extract a[href*="/posts/"]  # All post links
[browser] > eval document.querySelectorAll('a[href*="/posts/"]').length  # Count them
[browser] > html  # Inspect page structure
```

### Content not loading?

Wait longer or for different selectors:

```
[browser] > wait div.content 15000  # Wait 15 seconds
[browser] > wait a 20000  # Wait for any links
```

### Want to inspect page?

```
[browser] > buttons  # See all buttons
[browser] > inputs   # See all input fields
[browser] > eval document.body.innerHTML.length  # Check if page loaded
```

## Example Session Output

```
$ browser-agent interactive https://www.patreon.com --browser-exe /usr/bin/brave-browser
🌐 Interactive Browser Session Started
Type 'help' for available commands, 'quit' to exit

┌─────────────────┐
│ URL   │ https://www.patreon.com/ │
│ Title │ Patreon                  │
│ Buttons │ 15                     │
│ Inputs  │ 0                      │
└─────────────────┘

[browser] > goto https://www.patreon.com/collection/1611241?view=expanded
┌─────────────────┐
│ URL   │ https://www.patreon.com/collection/1611241?view=expanded │
│ Title │ Collection                                               │
│ Buttons │ 42                                                     │
│ Inputs  │ 3                                                      │
└─────────────────┘

[browser] > wait a[href*="/posts/"]
Element appeared: a[href*="/posts/"]

[browser] > extract a[href*="/posts/"][href*="collection=1611241"]
Extracted 38 links
  1. https://www.patreon.com/posts/12345?collection=1611241
  2. https://www.patreon.com/posts/67890?collection=1611241
  ...

[browser] > save collection.json
Saved 38 links to collection.json

[browser] > quit
Browser session ended
```
