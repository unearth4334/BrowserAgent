# Quick Start: Patreon Content Extraction (Client-Server Mode)

This is the recommended workflow for extracting content from Patreon collections.

## One-Time Setup

```bash
# Install dependencies
pip install -e .[dev]
playwright install chromium

# Make scripts executable
chmod +x scripts/*.py
```

## Workflow

### 1. Start Browser Server (Terminal 1)

```bash
source .venv/bin/activate
python scripts/browser_server.py /usr/bin/brave-browser
```

**What happens:**
- Browser opens and navigates to Patreon
- You log in manually
- Server starts listening on port 9999
- Leave this terminal running!

### 2. Extract Collection Links (Terminal 2)

```bash
source .venv/bin/activate
python scripts/extract_patreon_client.py 1611241
```

**Output:** `outputs/patreon_collection_1611241.json`

### 3. Extract Post Content (Terminal 2)

**Single post:**
```bash
python scripts/extract_patreon_content_client.py 1611241 0
```

**Batch extraction:**
```bash
# Create batch script
cat > extract_all.sh << 'EOF'
#!/bin/bash
COLLECTION_ID="1611241"
COUNT=$(cat outputs/patreon_collection_${COLLECTION_ID}.json | jq '.count')

for i in $(seq 0 $((COUNT - 1))); do
  echo "=== Post $((i + 1))/$COUNT ==="
  python scripts/extract_patreon_content_client.py $COLLECTION_ID $i
  sleep 1
done
EOF

chmod +x extract_all.sh
./extract_all.sh
```

**Output:** `outputs/<collection_name>/<post_id>-desc.html`

### 4. Stop Server (Terminal 1)

Press `Ctrl+C` when done

## File Structure

```
outputs/
└── <collection_name>/           # e.g., "SDXL Models"
    ├── 144726506-desc.html      # Description HTML
    ├── 144726506-meta.json      # Metadata
    ├── 144669916-desc.html
    ├── 144669916-meta.json
    └── ...
```

## Quick Commands Reference

| Action | Command |
|--------|---------|
| Start server | `python scripts/browser_server.py /usr/bin/brave-browser` |
| Get collection links | `python scripts/extract_patreon_client.py <collection_id>` |
| Extract single post | `python scripts/extract_patreon_content_client.py <collection_id> <index>` |
| Extract by URL | `python scripts/extract_patreon_content_client.py <collection_id> <url>` |
| Check server | `python scripts/browser_client.py ping` |
| Get page info | `python scripts/browser_client.py info` |

## Advantages of Client-Server Mode

✅ **Authenticate once** - No repeated logins  
✅ **Fast extraction** - No browser startup delay  
✅ **Batch processing** - Extract multiple posts automatically  
✅ **Debug friendly** - Browser stays open for inspection  
✅ **Reliable** - Single persistent session  

## Troubleshooting

**"Could not connect to browser server"**
→ Start the server first in a separate terminal

**"Collection data not found"**
→ Run `extract_patreon_client.py` to get the links first

**"No HTML content extracted"**
→ Check that you're logged in and have access to the collection

**Server crashes or freezes**
→ Restart the server and re-authenticate

## Example Session

```bash
# Terminal 1: Start server
$ python scripts/browser_server.py /usr/bin/brave-browser
🌐 Browser Server Starting
Port: 9999
Browser: /usr/bin/brave-browser
✓ Browser started
Please authenticate in the browser...
Press Enter once you're logged in to start the server...
[You log in to Patreon in the browser]
[Press Enter]
✓ Server ready on port 9999
Waiting for commands...

# Terminal 2: Extract collection
$ python scripts/extract_patreon_client.py 1611241
Patreon Collection Extractor (Client Mode)
Collection ID: 1611241

Step 1: Connecting to browser server...
✓ Connected to browser server
Step 2: Navigating to collection 1611241...
✓ Navigated to collection
...
✓ Found 22 links
✓ Saved to patreon_collection_1611241.json

# Terminal 2: Extract first post
$ python scripts/extract_patreon_content_client.py 1611241 0
Patreon Content Extractor (Client Mode)
Collection ID: 1611241

Step 1: Connecting to browser server...
✓ Connected to browser server
Step 2: Loading collection data...
✓ Loaded 22 posts
Step 3: Getting collection name...
  Collection: SDXL Models
Step 4: Extracting post content...
→ Navigating to post...
  Title: Anya Taylor-Joy SDXL LoRA | Patreon
→ Waiting for content...
✓ Found content using selector: div[class*="cm-LIiDtl"]
  Length: 2543 characters
Step 5: Saving content...
✓ Saved HTML to outputs/SDXL_Models/144726506-desc.html
✓ Saved metadata to outputs/SDXL_Models/144726506-meta.json

✓ Extraction complete!
Output: outputs/SDXL_Models/144726506-desc.html
```

## Next Steps

- Process extracted HTML (convert to Markdown, extract metadata, etc.)
- Extract additional content (images, attachments, comments)
- Build a database of extracted content
- Create analysis tools for the collected data
