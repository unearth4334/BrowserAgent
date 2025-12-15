# vast_api WebUI Automation Examples

Examples for automating the vast_api WebUI using BrowserAgent.

## Scripts

### `debug_create_tab.py`

Debug script that inspects the Create tab and workflow-tile element in the vast_api WebUI.

**Features:**
- Opens the vast_api WebUI in a visible browser
- Attempts to click the "🎨 Create" tab using multiple selectors
- Inspects the `workflow-tile` element
- Extracts page structure for debugging
- Keeps browser open for manual inspection

**Usage:**

```bash
# Default URL (http://10.0.78.66:5000/)
python3 examples/vast_api/debug_create_tab.py

# Custom URL
python3 examples/vast_api/debug_create_tab.py --url http://localhost:5000/

# Custom port
python3 examples/vast_api/debug_create_tab.py --port 8888
```

**What it does:**

1. **Starts browser server** - Opens browser in non-headless mode (port 9999 by default)
2. **Navigates to WebUI** - Loads your vast_api WebUI URL
3. **Finds Create tab** - Tries multiple selectors to locate and click the Create tab:
   - `button:has-text('🎨 Create')`
   - `button:has-text('Create')`
   - `[role='tab']:has-text('Create')`
   - `.nav-link:has-text('Create')`
   - `a:has-text('Create')`
4. **Inspects workflow-tile** - Checks if `.workflow-tile` element exists and extracts:
   - Element ID and classes
   - Number of children and their tags
   - Text content preview
   - HTML preview (first 500 characters)
5. **Page structure** - Extracts overall page structure (3 levels deep)
6. **Manual inspection** - Keeps browser open so you can inspect manually

**Output example:**

```
🔍 vast_api WebUI Create Tab Debugger
   WebUI: http://10.0.78.66:5000/
   Server Port: 9999

⏳ Starting browser server...
✅ Browser server ready

📍 Step 1: WebUI loaded at startup
   URL: http://10.0.78.66:5000/
   Title: vast_api WebUI
✅ Ready

📍 Step 2: Click '🎨 Create' tab...
   Trying selector: button:has-text('🎨 Create')
✅ Clicked Create tab using: button:has-text('🎨 Create')

📍 Step 3: Inspect workflow-tile element...
✅ Found workflow-tile element!

   ID: workflow-tile-1
   Classes: workflow-tile card
   Children: 3 elements
   Child tags: ['DIV', 'INPUT', 'BUTTON']

   Text content preview:
   Workflow Name
   workflow_example.json
   Queue Workflow

   HTML preview (first 500 chars):
   <div class="workflow-name">Workflow Name</div>
   <input type="file" class="workflow-input" accept=".json">
   <button class="queue-btn">Queue Workflow</button>

📍 Step 4: Extract full page structure...
✅ Page structure extracted
   (Use inspect() in interactive mode for detailed view)

🔍 Browser remains open for manual inspection
   Press Ctrl+C to exit
```

**If element not found:**

The script will:
- Show all clickable elements on the page
- Search for similar elements (`.workflow`, `.tile`, `[class*="workflow"]`, etc.)
- Keep browser open for manual debugging

**Troubleshooting:**

If the script can't find the Create tab or workflow-tile:
1. Check the console output for list of found elements
2. Use the open browser to manually inspect the page
3. Update the selectors in the script based on actual HTML structure
4. Look at the "similar elements" output for hints

## Requirements

```bash
# Ensure BrowserAgent is installed
pip install -e .

# Install Playwright browsers
playwright install chromium
```

## Next Steps

After debugging with this script:
1. Identify the correct selectors for your WebUI elements
2. Create a workflow queuing script based on findings
3. Integrate with your WebUI automation needs
