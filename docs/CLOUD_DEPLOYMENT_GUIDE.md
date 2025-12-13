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

# Run the UI-click workflow queue script (requires a workflow file)
PYTHONPATH=/root/BrowserAgent/src:$PYTHONPATH python3 queue_workflow_ui_click.py \
    --workflow-path /path/to/workflow.json \
    --comfyui-url http://localhost:18188

# Expected output:
# Starting browser server...
# Loading workflow...
# Converting to API format...
# Queuing workflow...
# ✓ Workflow queued successfully! Prompt ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

**Note**: The `queue_workflow_ui_click.py` script uses UI-native queuing (clicks Queue button) for full compatibility with custom nodes that require UI metadata.

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

### Complete WebUI Workflow Queue Implementation

This section provides a production-ready implementation for queuing ComfyUI workflows from your WebUI.

#### Prerequisites

```python
# Required Python packages in your WebUI environment
pip install paramiko
```

#### Full Implementation

```python
import paramiko
import re
import time
from pathlib import Path

class ComfyUIWorkflowQueue:
    """
    Manages ComfyUI workflow queuing via BrowserAgent on a remote cloud instance.
    
    Features:
    - SSH connection management
    - Browser server lifecycle management
    - Workflow file transfer
    - Automatic server startup and health checks
    - Prompt ID extraction and status tracking
    """
    
    def __init__(self, hostname, port, username, key_filename=None, 
                 browser_agent_path="/root/BrowserAgent",
                 comfyui_url="http://localhost:18188"):
        """
        Initialize connection to cloud instance.
        
        Args:
            hostname: Cloud instance IP/hostname
            port: SSH port (e.g., 19361 for vast.ai)
            username: SSH username (typically 'root')
            key_filename: Path to SSH private key (optional)
            browser_agent_path: Path to BrowserAgent on remote instance
            comfyui_url: ComfyUI URL on remote instance
        """
        self.hostname = hostname
        self.port = port
        self.username = username
        self.key_filename = key_filename
        self.browser_agent_path = browser_agent_path
        self.comfyui_url = comfyui_url
        self.ssh = None
        self.sftp = None
    
    def connect(self):
        """Establish SSH connection to cloud instance."""
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if self.key_filename:
            self.ssh.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                key_filename=self.key_filename,
                timeout=10
            )
        else:
            self.ssh.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                timeout=10
            )
        
        self.sftp = self.ssh.open_sftp()
        print(f"✓ Connected to {self.hostname}:{self.port}")
    
    def disconnect(self):
        """Close SSH and SFTP connections."""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
        print("✓ Disconnected from cloud instance")
    
    def run_command(self, command, timeout=30):
        """
        Execute command on remote instance.
        
        Returns:
            tuple: (stdout, stderr, exit_code)
        """
        stdin, stdout, stderr = self.ssh.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        return (
            stdout.read().decode('utf-8'),
            stderr.read().decode('utf-8'),
            exit_code
        )
    
    def is_browser_server_running(self):
        """
        Check if browser server is running on remote instance.
        
        Returns:
            bool: True if server is running
        """
        stdout, stderr, _ = self.run_command(
            "ps aux | grep 'browser_agent.server.browser_server' | grep -v grep"
        )
        return "browser_server" in stdout
    
    def start_browser_server(self, port=8765):
        """
        Start browser server on remote instance.
        
        Args:
            port: Port for browser server (default: 8765)
            
        Returns:
            bool: True if server started successfully
        """
        if self.is_browser_server_running():
            print("✓ Browser server already running")
            return True
        
        print("⏳ Starting browser server...")
        
        # Start server in background
        start_command = (
            f"cd {self.browser_agent_path} && "
            f"PYTHONPATH={self.browser_agent_path}/src:$PYTHONPATH "
            f"nohup python3 -m browser_agent.server.browser_server "
            f"--port {port} --headless "
            f"> /tmp/browser_server_{port}.log 2>&1 &"
        )
        
        stdout, stderr, exit_code = self.run_command(start_command)
        
        # Wait for server to initialize
        time.sleep(3)
        
        # Verify server is running
        if self.is_browser_server_running():
            print(f"✓ Browser server started on port {port}")
            return True
        else:
            print(f"✗ Failed to start browser server")
            print(f"Error: {stderr}")
            return False
    
    def stop_browser_server(self):
        """Stop browser server on remote instance."""
        if not self.is_browser_server_running():
            print("✓ Browser server not running")
            return
        
        print("⏳ Stopping browser server...")
        self.run_command("pkill -f browser_agent.server.browser_server")
        time.sleep(1)
        
        if not self.is_browser_server_running():
            print("✓ Browser server stopped")
        else:
            print("⚠ Browser server may still be running")
    
    def upload_workflow(self, local_workflow_path, remote_path="/tmp/workflow.json"):
        """
        Upload workflow JSON file to remote instance.
        
        Args:
            local_workflow_path: Path to local workflow JSON file
            remote_path: Destination path on remote instance
            
        Returns:
            bool: True if upload successful
        """
        try:
            self.sftp.put(local_workflow_path, remote_path)
            print(f"✓ Uploaded workflow to {remote_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to upload workflow: {e}")
            return False
    
    def queue_workflow(self, workflow_path_on_remote, use_ui_method=True):
        """
        Queue workflow for execution in ComfyUI.
        
        Args:
            workflow_path_on_remote: Path to workflow JSON on remote instance
            use_ui_method: Use UI-click method (True) or HTTP API method (False)
                          UI method recommended for compatibility with all custom nodes
        
        Returns:
            str or None: Prompt ID if successful, None if failed
        """
        # Ensure browser server is running
        if not self.is_browser_server_running():
            if not self.start_browser_server():
                return None
        
        # Choose queuing script
        script_name = "queue_workflow_ui_click.py" if use_ui_method else "queue_workflow_simple.py"
        
        print(f"⏳ Queuing workflow using {'UI-click' if use_ui_method else 'HTTP API'} method...")
        
        # Execute queue command
        queue_command = (
            f"cd {self.browser_agent_path}/examples/comfyui && "
            f"PYTHONPATH={self.browser_agent_path}/src:$PYTHONPATH "
            f"python3 {script_name} "
            f"--workflow-path {workflow_path_on_remote} "
            f"--comfyui-url {self.comfyui_url}"
        )
        
        stdout, stderr, exit_code = self.run_command(queue_command, timeout=60)
        
        if exit_code != 0:
            print(f"✗ Queue command failed with exit code {exit_code}")
            print(f"Error: {stderr}")
            return None
        
        # Extract prompt ID from output
        match = re.search(r'Prompt ID: ([a-f0-9-]+)', stdout)
        if match:
            prompt_id = match.group(1)
            print(f"✓ Workflow queued successfully!")
            print(f"  Prompt ID: {prompt_id}")
            return prompt_id
        else:
            print("⚠ Workflow may be queued but prompt ID not found in output")
            print(f"Output: {stdout}")
            return None
    
    def check_workflow_status(self, prompt_id):
        """
        Check execution status of a queued workflow.
        
        Args:
            prompt_id: Prompt ID returned from queue_workflow()
            
        Returns:
            dict: Status information with keys 'state', 'message'
                 state: 'pending', 'running', 'completed', 'failed', 'unknown'
        """
        # Check queue status
        check_command = f"curl -s {self.comfyui_url}/queue"
        stdout, stderr, _ = self.run_command(check_command)
        
        try:
            import json
            queue_data = json.loads(stdout)
            
            # Check if in running queue
            running = queue_data.get('queue_running', [])
            for item in running:
                if prompt_id in str(item):
                    return {'state': 'running', 'message': 'Workflow is currently executing'}
            
            # Check if in pending queue
            pending = queue_data.get('queue_pending', [])
            for item in pending:
                if prompt_id in str(item):
                    return {'state': 'pending', 'message': 'Workflow is waiting in queue'}
            
            # Check history for completion/failure
            history_command = f"curl -s {self.comfyui_url}/history/{prompt_id}"
            stdout, stderr, _ = self.run_command(history_command)
            history_data = json.loads(stdout)
            
            if prompt_id in history_data:
                prompt_history = history_data[prompt_id]
                status = prompt_history.get('status', {})
                
                if status.get('completed'):
                    return {'state': 'completed', 'message': 'Workflow completed successfully'}
                elif 'messages' in prompt_history and prompt_history['messages']:
                    # Check for errors in messages
                    return {'state': 'failed', 'message': f"Workflow failed: {prompt_history['messages']}"}
                else:
                    return {'state': 'completed', 'message': 'Workflow finished'}
            
            return {'state': 'unknown', 'message': 'Workflow not found in queue or history'}
            
        except Exception as e:
            return {'state': 'unknown', 'message': f'Error checking status: {e}'}


# Example Usage in WebUI
def queue_comfyui_workflow_example():
    """
    Example function showing how to use ComfyUIWorkflowQueue in your WebUI.
    """
    
    # Initialize queue manager with your cloud instance details
    queue_manager = ComfyUIWorkflowQueue(
        hostname="172.219.157.164",  # Your cloud instance IP
        port=19361,                   # SSH port
        username="root",              # SSH username
        key_filename="~/.ssh/id_rsa", # Path to SSH key (optional)
        browser_agent_path="/root/BrowserAgent",
        comfyui_url="http://localhost:18188"
    )
    
    try:
        # Connect to cloud instance
        queue_manager.connect()
        
        # Upload workflow file generated by your WebUI
        local_workflow_file = "/path/to/generated/workflow.json"
        remote_workflow_path = "/tmp/my_workflow.json"
        
        if not queue_manager.upload_workflow(local_workflow_file, remote_workflow_path):
            print("Failed to upload workflow")
            return None
        
        # Queue the workflow
        # Use use_ui_method=True for full compatibility (recommended)
        # Use use_ui_method=False for slightly faster execution if workflow doesn't use UI-dependent nodes
        prompt_id = queue_manager.queue_workflow(
            workflow_path_on_remote=remote_workflow_path,
            use_ui_method=True  # Recommended for maximum compatibility
        )
        
        if not prompt_id:
            print("Failed to queue workflow")
            return None
        
        # Optional: Check status
        status = queue_manager.check_workflow_status(prompt_id)
        print(f"Status: {status['state']} - {status['message']}")
        
        return prompt_id
        
    finally:
        # Always disconnect
        queue_manager.disconnect()


# Simplified single-function interface for WebUI integration
def queue_workflow_from_webui(hostname, port, username, key_filename,
                                local_workflow_path, comfyui_url="http://localhost:18188"):
    """
    Simplified function to queue a workflow from WebUI.
    
    Args:
        hostname: Cloud instance IP/hostname
        port: SSH port
        username: SSH username
        key_filename: Path to SSH private key
        local_workflow_path: Path to workflow JSON file on local machine
        comfyui_url: ComfyUI URL on remote instance
    
    Returns:
        str or None: Prompt ID if successful, None if failed
    """
    queue_manager = ComfyUIWorkflowQueue(
        hostname=hostname,
        port=port,
        username=username,
        key_filename=key_filename,
        comfyui_url=comfyui_url
    )
    
    try:
        queue_manager.connect()
        
        # Upload workflow
        remote_path = f"/tmp/workflow_{int(time.time())}.json"
        if not queue_manager.upload_workflow(local_workflow_path, remote_path):
            return None
        
        # Queue with UI method for maximum compatibility
        prompt_id = queue_manager.queue_workflow(remote_path, use_ui_method=True)
        
        return prompt_id
        
    finally:
        queue_manager.disconnect()
```

#### Integration into Your WebUI

**Step 1: Add the Queue Manager Class**

Copy the `ComfyUIWorkflowQueue` class into your WebUI codebase (e.g., `utils/comfyui_queue.py`).

**Step 2: Configure Connection Details**

```python
# In your WebUI configuration
CLOUD_INSTANCE = {
    'hostname': '172.219.157.164',
    'port': 19361,
    'username': 'root',
    'key_filename': '~/.ssh/id_rsa',  # Or None to use ssh-agent
    'browser_agent_path': '/root/BrowserAgent',
    'comfyui_url': 'http://localhost:18188'
}
```

**Step 3: Queue Workflow from WebUI**

```python
# In your WebUI workflow generation code
def on_generate_video_clicked(workflow_data):
    """Handler for 'Generate Video' button in WebUI."""
    
    # 1. Generate workflow JSON
    workflow_json_path = save_workflow_to_file(workflow_data)
    
    # 2. Queue on cloud instance
    queue_manager = ComfyUIWorkflowQueue(**CLOUD_INSTANCE)
    
    try:
        queue_manager.connect()
        
        # Upload and queue
        remote_path = "/tmp/webui_workflow.json"
        queue_manager.upload_workflow(workflow_json_path, remote_path)
        prompt_id = queue_manager.queue_workflow(remote_path, use_ui_method=True)
        
        if prompt_id:
            # Store prompt_id for status tracking
            save_prompt_id_to_database(prompt_id)
            show_success_message(f"Queued successfully! ID: {prompt_id}")
        else:
            show_error_message("Failed to queue workflow")
            
    except Exception as e:
        show_error_message(f"Error: {e}")
    finally:
        queue_manager.disconnect()
```

**Step 4: Monitor Workflow Status (Optional)**

```python
def check_workflow_progress(prompt_id):
    """Check progress of a previously queued workflow."""
    
    queue_manager = ComfyUIWorkflowQueue(**CLOUD_INSTANCE)
    
    try:
        queue_manager.connect()
        status = queue_manager.check_workflow_status(prompt_id)
        
        return status  # {'state': 'running', 'message': '...'}
        
    finally:
        queue_manager.disconnect()
```

### Key Features

1. **Automatic Server Management**: Checks if browser server is running, starts it if needed
2. **Robust Error Handling**: Comprehensive error checking and reporting
3. **Status Tracking**: Check workflow execution status anytime
4. **Method Selection**: Choose between UI-click (maximum compatibility) or HTTP API (faster)
5. **Connection Lifecycle**: Proper SSH connection management with cleanup

### Performance Notes

- **Initial startup**: ~3 seconds for browser server initialization
- **Workflow queue**: ~5-7 seconds per workflow (UI method)
- **Status check**: <1 second per check
- **SSH connection**: ~1-2 seconds to establish

### Troubleshooting WebUI Integration

**Issue: SSH connection timeout**
```python
# Increase timeout in connect()
self.ssh.connect(..., timeout=30)
```

**Issue: Browser server fails to start**
```python
# Check server logs on remote instance
queue_manager.run_command("cat /tmp/browser_server_8765.log")
```

**Issue: Workflow upload fails**
```python
# Verify SFTP connection
try:
    queue_manager.sftp.stat(remote_path)
    print("File uploaded successfully")
except:
    print("Upload failed")
```

### WebUI Implementation Steps (Legacy Reference)

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
