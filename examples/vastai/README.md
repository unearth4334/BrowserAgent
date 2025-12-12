# Vast.ai Browser Automation

This module provides browser automation utilities for interacting with vast.ai instances using HTTP basic authentication.

## Overview

The vast.ai module demonstrates how to:
- Authenticate with vast.ai instances using HTTP basic auth
- Navigate to authenticated pages
- Extract information from vast.ai dashboards (future enhancement)

## Setup

### 1. Install Dependencies

Ensure you have the browser-agent package installed with Playwright:

```bash
# Install in editable mode
pip install -e .[dev]

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Credentials

Create or edit the `vastai_credentials.txt` file in the project root:

```bash
# Format: username:password
myusername:mypassword
```

**Important**: This file is already added to `.gitignore` to prevent accidental credential commits.

## Usage

### Basic Authentication

Authenticate with a vast.ai instance:

```bash
# Using default URL (from script)
python examples/vastai/vastai_auth.py

# With custom URL
python examples/vastai/vastai_auth.py --url https://your-vastai-instance.com/

# In headless mode
python examples/vastai/vastai_auth.py --headless
```

### Custom Credentials File

Specify a different credentials file:

```bash
python examples/vastai/vastai_auth.py --credentials-file /path/to/creds.txt
```

## Architecture

The module follows the browser-agent layered architecture:

- **`task_spec_vastai.py`**: Defines the `VastAiAuthTaskSpec` task specification
  - Embeds credentials in URL for HTTP basic auth
  - Checks for successful authentication via page elements
  
- **`policy_vastai.py`**: Implements the `VastAiAuthPolicy` decision logic
  - Navigates to URL with embedded credentials
  - Waits for page to load
  - Marks task as complete

- **`vastai_auth.py`**: Standalone script demonstrating usage
  - Loads credentials from file
  - Configures browser settings
  - Runs the agent with task and policy

## How HTTP Basic Auth Works

The script handles HTTP basic auth by embedding credentials in the URL:

```
https://username:password@domain.com/path
```

When the browser encounters an HTTP basic auth challenge, it automatically sends these credentials. This approach:
- ✅ Works with Playwright and most browsers
- ✅ Handles the "This site is asking you to sign in" popup automatically
- ✅ No need for manual popup interaction

## Future Enhancements

Potential additions to this module:

1. **Instance Management**
   - List running instances
   - Start/stop instances
   - Extract instance details

2. **GPU Monitoring**
   - Extract GPU utilization
   - Monitor training progress
   - Export metrics

3. **File Operations**
   - Upload files to instances
   - Download training outputs
   - Sync directories

## Security Notes

- Never commit `vastai_credentials.txt` to version control
- Consider using environment variables for CI/CD: `VASTAI_USERNAME` and `VASTAI_PASSWORD`
- The credentials are sent over HTTPS (encrypted in transit)
- Playwright stores credentials in memory during execution

## Troubleshooting

### Authentication Fails

1. Verify credentials in `vastai_credentials.txt` are correct
2. Check the URL is accessible (try in regular browser)
3. Run with `--headless` flag disabled to see browser actions
4. Check logs for error messages

### "Credentials file not found"

Ensure `vastai_credentials.txt` exists in the project root:

```bash
cd /home/sdamk/dev/BrowserAgent
ls -la vastai_credentials.txt
```

### Browser Doesn't Open

Ensure Playwright browsers are installed:

```bash
playwright install chromium
```

## Example Output

```
Loaded credentials for user: myusername

🚀 Starting authentication with https://disks-gba-says-facts.trycloudflare.com/
   Headless mode: False

✅ Successfully authenticated!
   Final URL: https://disks-gba-says-facts.trycloudflare.com/dashboard
   Page title: Vast.ai Dashboard

Browser will remain open. Press Enter to close...
```
