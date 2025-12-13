# BrowserAgent Cloud Deployment Guide

**Application Note for WebUI Integration**  
*Last Updated: December 12, 2025*

## Overview

This guide provides step-by-step instructions for deploying BrowserAgent to a cloud instance (e.g., vast.ai, AWS, Azure) from your local WebUI. BrowserAgent enables headless browser automation for ComfyUI workflow queuing and other browser-based tasks in containerized cloud environments.

## Prerequisites

### Cloud Instance Requirements
- **OS**: Ubuntu 22.04 or later (Linux-based)
- **Python**: 3.11+ (tested on 3.10.12)
- **Memory**: Minimum 4GB RAM
- **Storage**: Minimum 2GB free space
- **Network**: SSH access with key-based authentication
- **ComfyUI**: Running on localhost (if using workflow queuing features)

### Local Requirements
- SSH client configured with access to cloud instance
- Git credentials or SSH key for GitHub access

## Deployment Steps

### 1. Connect to Cloud Instance

```bash
# Replace with your cloud instance details
ssh -p <PORT> <USER>@<HOST>

# Example for vast.ai:
ssh -p 19361 root@172.219.157.164
```

### 2. Clone or Update BrowserAgent Repository

```bash
# Navigate to desired installation directory
cd /root  # or your preferred location

# Clone the repository (first-time setup)
if [ ! -d "BrowserAgent" ]; then
    git clone https://github.com/unearth4334/BrowserAgent.git
    cd BrowserAgent
    git checkout main
else
    # Update existing installation
    cd BrowserAgent
    git fetch origin
    git checkout main
    git pull origin main
fi
```

**Note**: This command checks if BrowserAgent already exists. If it does, it updates to the latest version from the main branch. If not, it clones a fresh copy.

### 3. Install System Dependencies

BrowserAgent uses Playwright which requires several system libraries for Chromium:

```bash
# Update package list
apt-get update

# Install required system libraries (will show "already installed" if present)
apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2
```

**Note**: On some systems, you may need `apt-get install --fix-missing` if any packages fail.

### 4. Install Python Dependencies

```bash
# Install/upgrade BrowserAgent package (safe to re-run)
pip install --upgrade .

# Alternative: If pip install fails, dependencies can be installed separately
pip install --upgrade playwright>=1.47.0 typer>=0.12.0 rich>=13.0.0

# Install development dependencies (optional, for testing)
pip install --upgrade pytest>=8.0.0 pytest-cov>=5.0.0
```

**Note**: Using `--upgrade` ensures you get the latest versions. If packages are already installed and up-to-date, pip will show "Requirement already satisfied".

### 5. Install Playwright Browser

```bash
# Install Chromium browser for Playwright (safe to re-run)
python3 -m playwright install chromium

# This downloads ~300MB and installs to ~/.cache/ms-playwright/
```

**Note**: If Chromium is already installed, this command will show "chromium vXXX is already installed" and complete immediately.

**Troubleshooting**: If `playwright` command is not found, use `python3 -m playwright` instead.

### 6. Verify Installation

Run the comprehensive verification steps below to ensure all components are working.

## Installation Verification

### Method 1: Run Unit Tests (Recommended)

```bash
cd /root/BrowserAgent  # or your installation path

# Run all unit tests (235 tests, ~0.6 seconds)
PYTHONPATH=/root/BrowserAgent/src:$PYTHONPATH python3 -m pytest tests/ --ignore=tests/integration/ -v

# Expected output:
# ============================= 235 passed in 0.59s ==============================
```

**Success Criteria**: All 235 tests should pass. No errors should appear.

### Method 2: Quick Smoke Test

```bash
# Test 1: Verify Python can import the module
PYTHONPATH=/root/BrowserAgent/src:$PYTHONPATH python3 -c "from browser_agent.agent.core import Agent; print('✓ Import successful')"

# Test 2: Verify Playwright is installed
python3 -m playwright --version
# Expected: Version 1.57.0 or higher

# Test 3: Check Chromium browser
find ~/.cache/ms-playwright -name chrome -type f | head -1
# Expected: Should list the Chromium executable path
```

### Method 3: Test Browser Server

```bash
# Start browser server in background (uses PYTHONPATH)
cd /root/BrowserAgent
PYTHONPATH=/root/BrowserAgent/src:$PYTHONPATH python3 -m browser_agent.server.browser_server \
    --port 8765 \
    --headless \
    --initial-url "https://example.com" &

# Wait for server to start
sleep 3

# Test connection with browser client
PYTHONPATH=/root/BrowserAgent/src:$PYTHONPATH python3 -m browser_agent.server.browser_client \
    --host localhost \
    --port 8765 \
    ping

# Expected output: {"status": "success", "message": "pong"}

# Stop the server
pkill -f browser_server
```

## ComfyUI Integration Verification

If you're using BrowserAgent for ComfyUI workflow queuing:

### 1. Verify ComfyUI is Running

```bash
# Check if ComfyUI is accessible
curl -s http://localhost:18188 | head -20

# Expected: HTML content from ComfyUI interface
```

### 2. Test Workflow Queuing (Example)

```bash
# Navigate to BrowserAgent examples directory
cd /root/BrowserAgent/examples/comfyui

# Run the simple workflow queue script (requires a workflow file)
PYTHONPATH=/root/BrowserAgent/src:$PYTHONPATH python3 queue_workflow_simple.py \
    --workflow-path /path/to/workflow.json \
    --comfyui-url http://localhost:18188

# Expected output:
# Starting browser server...
# Loading workflow...
# Converting to API format...
# Queuing workflow...
# ✓ Workflow queued successfully! Prompt ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

**Note**: The `queue_workflow_simple.py` script includes critical 0.5-second timing delays at 6 points for reliable execution.

## Common Issues and Solutions

### Issue 0: Repository already exists (git clone fails)

**Cause**: BrowserAgent directory already exists from a previous installation.

**Solution**:
```bash
# Update existing installation instead of cloning
cd /root/BrowserAgent
git fetch origin
git checkout main
git pull origin main

# Then proceed with dependency installation steps
```

### Issue 1: ModuleNotFoundError: No module named 'browser_agent'

**Cause**: Package not installed or not in Python path.

**Solution**:
```bash
# Use PYTHONPATH to reference source directly
export PYTHONPATH=/root/BrowserAgent/src:$PYTHONPATH

# Or add to ~/.bashrc for persistence:
echo 'export PYTHONPATH=/root/BrowserAgent/src:$PYTHONPATH' >> ~/.bashrc
source ~/.bashrc
```

### Issue 2: Playwright browser not found (exit code 127)

**Cause**: Missing system libraries or Chromium not installed.

**Solution**:
```bash
# Reinstall system dependencies
apt-get install -y libnss3 libnspr4 libatk1.0-0

# Reinstall Chromium
python3 -m playwright install chromium
```

### Issue 3: "Package installs as UNKNOWN-0.0.0"

**Cause**: Build backend doesn't support editable installs.

**Solution**: This is expected behavior. Use `PYTHONPATH` method (see Issue 1) instead of relying on pip installation.

### Issue 4: Socket buffer limit exceeded (JavaScript injection)

**Cause**: Attempting to inject >130KB of JavaScript code.

**Solution**: Use localStorage chunking (50KB chunks) as demonstrated in `examples/comfyui/queue_hybrid.py`.

### Issue 5: ComfyUI workflow fails to queue

**Cause**: Missing timing delays between browser actions.

**Solution**: Add 0.5-second delays at critical synchronization points:
- After page navigation
- After file read operations
- After localStorage storage
- After workflow load (2s + 0.5s)
- After API export
- After queue request

See `examples/comfyui/queue_workflow_simple.py` for reference implementation.

## WebUI Integration Pattern

### Recommended Architecture

```
WebUI (Local) ──SSH──> Cloud Instance (BrowserAgent)
                              │
                              ├─> Browser Server (port 8765)
                              │   └─> Playwright/Chromium
                              │
                              └─> ComfyUI (port 18188)
```

### WebUI Implementation Steps

1. **SSH Connection Management**
   ```python
   import paramiko
   
   ssh = paramiko.SSHClient()
   ssh.set_missing_host_key_policy(paramiko.AutoKeyPolicy())
   ssh.connect(hostname, port, username, key_filename='~/.ssh/id_rsa')
   ```

2. **Remote Command Execution**
   ```python
   def run_remote_command(ssh, command):
       stdin, stdout, stderr = ssh.exec_command(command)
       return stdout.read().decode(), stderr.read().decode()
   ```

3. **Deployment Automation**
   ```python
   # Check if repository exists, clone or update accordingly
   check_cmd = "[ -d /root/BrowserAgent ] && echo 'EXISTS' || echo 'NEW'"
   output, _ = run_remote_command(ssh, check_cmd)
   
   if 'EXISTS' in output:
       # Update existing installation
       run_remote_command(ssh, 
           "cd /root/BrowserAgent && git fetch origin && git checkout main && git pull origin main")
   else:
       # Clone new installation
       run_remote_command(ssh, 
           "git clone https://github.com/unearth4334/BrowserAgent.git /root/BrowserAgent && "
           "cd /root/BrowserAgent && git checkout main")
   
   # Install/upgrade dependencies (safe to re-run)
   run_remote_command(ssh, "cd /root/BrowserAgent && pip install --upgrade .")
   run_remote_command(ssh, "python3 -m playwright install chromium")
   
   # Verify installation
   output, error = run_remote_command(ssh, 
       "cd /root/BrowserAgent && PYTHONPATH=/root/BrowserAgent/src:$PYTHONPATH python3 -m pytest tests/ --ignore=tests/integration/ -q")
   
   if "235 passed" in output:
       print("✓ Installation verified successfully")
   ```

4. **Browser Server Management**
   ```python
   # Start server
   ssh.exec_command(
       "cd /root/BrowserAgent && "
       "PYTHONPATH=/root/BrowserAgent/src:$PYTHONPATH "
       "nohup python3 -m browser_agent.server.browser_server "
       "--port 8765 --headless > browser_server.log 2>&1 &"
   )
   
   # Check server status
   output, _ = run_remote_command(ssh, "ps aux | grep browser_server | grep -v grep")
   server_running = "browser_server" in output
   ```

5. **Workflow Queue Operations**
   ```python
   # Upload workflow file
   sftp = ssh.open_sftp()
   sftp.put('local_workflow.json', '/tmp/workflow.json')
   sftp.close()
   
   # Queue workflow
   queue_command = (
       "cd /root/BrowserAgent/examples/comfyui && "
       "PYTHONPATH=/root/BrowserAgent/src:$PYTHONPATH "
       "python3 queue_workflow_simple.py "
       "--workflow-path /tmp/workflow.json "
       "--comfyui-url http://localhost:18188"
   )
   output, error = run_remote_command(ssh, queue_command)
   
   # Parse prompt ID from output
   import re
   match = re.search(r'Prompt ID: ([a-f0-9-]+)', output)
   if match:
       prompt_id = match.group(1)
       print(f"Queued workflow: {prompt_id}")
   ```

## Performance Considerations

- **Startup Time**: Browser server takes ~3 seconds to initialize
- **Workflow Queue Time**: ~5-7 seconds per workflow (including all delays)
- **Memory Usage**: ~500MB for Chromium + ~100MB for Python
- **Network**: Minimal bandwidth (<1MB per workflow operation)

## Security Recommendations

1. **Use SSH Key Authentication**: Never store passwords in WebUI
2. **Restrict SSH Access**: Use firewall rules to limit SSH access
3. **Run as Non-Root**: Create dedicated user for BrowserAgent (optional)
4. **Monitor Logs**: Check browser_server.log regularly for issues
5. **Update Dependencies**: Keep Playwright and system libraries updated

## Directory Structure

After successful deployment:

```
/root/BrowserAgent/
├── src/
│   └── browser_agent/
│       ├── agent/           # Agent core logic
│       ├── browser/         # Playwright driver
│       └── server/          # Browser server/client
├── examples/
│   └── comfyui/
│       ├── queue_hybrid.py
│       ├── queue_workflow_simple.py
│       └── queue_with_screenshots.py
├── tests/                   # Unit tests (235 tests)
├── docs/                    # Documentation
└── pyproject.toml           # Package configuration
```

## Support and Troubleshooting

For issues not covered in this guide:

1. Check logs: `/root/BrowserAgent/browser_server.log`
2. Run verbose tests: `pytest tests/ -vv --tb=long`
3. Review examples: See `examples/comfyui/` for working implementations
4. Check GitHub issues: https://github.com/unearth4334/BrowserAgent/issues

## Version History

- **v0.1.0** (December 2025): Initial cloud deployment support
  - Screenshot capability added
  - ComfyUI workflow queuing with hybrid approach
  - Timing delays for reliable execution
  - Comprehensive unit test coverage (235 tests)

---

**End of Application Note**
