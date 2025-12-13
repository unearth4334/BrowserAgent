# WebUI Quick Start Guide

**Concise integration guide for queuing ComfyUI workflows from your WebUI**

## Prerequisites

```bash
pip install paramiko
```

## Cloud Instance Configuration

```python
# Configuration for your cloud instance
CLOUD_CONFIG = {
    'hostname': '172.219.157.164',      # Your cloud IP
    'port': 19361,                       # SSH port
    'username': 'root',
    'key_filename': '~/.ssh/id_rsa',    # SSH key path (or None)
    'browser_agent_path': '/root/BrowserAgent',
    'comfyui_url': 'http://localhost:18188'
}
```

## Implementation

### Complete Function

```python
import paramiko
import time
import re

def queue_workflow(workflow_json_path, cloud_config):
    """
    Queue a ComfyUI workflow on remote cloud instance.
    
    Args:
        workflow_json_path: Path to local workflow JSON file
        cloud_config: Dict with connection details
        
    Returns:
        str: Prompt ID if successful, None if failed
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # 1. Connect via SSH
        ssh.connect(
            hostname=cloud_config['hostname'],
            port=cloud_config['port'],
            username=cloud_config['username'],
            key_filename=cloud_config.get('key_filename'),
            timeout=10
        )
        
        # 2. Upload workflow file
        sftp = ssh.open_sftp()
        remote_path = f"/tmp/workflow_{int(time.time())}.json"
        sftp.put(workflow_json_path, remote_path)
        sftp.close()
        
        # 3. Check if browser server is running
        stdin, stdout, stderr = ssh.exec_command(
            "ps aux | grep 'browser_agent.server.browser_server' | grep -v grep"
        )
        is_running = "browser_server" in stdout.read().decode()
        
        # 4. Start browser server if not running
        if not is_running:
            start_cmd = (
                f"cd {cloud_config['browser_agent_path']} && "
                f"PYTHONPATH={cloud_config['browser_agent_path']}/src:$PYTHONPATH "
                f"nohup python3 -m browser_agent.server.browser_server "
                f"--port 8765 --headless > /tmp/browser_server.log 2>&1 &"
            )
            ssh.exec_command(start_cmd)
            time.sleep(3)  # Wait for server to start
        
        # 5. Queue workflow using UI-click method
        queue_cmd = (
            f"cd {cloud_config['browser_agent_path']}/examples/comfyui && "
            f"PYTHONPATH={cloud_config['browser_agent_path']}/src:$PYTHONPATH "
            f"python3 queue_workflow_ui_click.py "
            f"--workflow-path {remote_path} "
            f"--comfyui-url {cloud_config['comfyui_url']}"
        )
        
        stdin, stdout, stderr = ssh.exec_command(queue_cmd, timeout=60)
        output = stdout.read().decode()
        
        # 6. Extract prompt ID
        match = re.search(r'Prompt ID: ([a-f0-9-]+)', output)
        if match:
            return match.group(1)
        else:
            print(f"Error: {stderr.read().decode()}")
            return None
            
    finally:
        ssh.close()


# Usage in your WebUI
def on_generate_button_clicked(workflow_data):
    """Example: Handle generate button click in WebUI."""
    
    # Generate workflow JSON file
    workflow_path = save_workflow_json(workflow_data)
    
    # Queue on cloud
    prompt_id = queue_workflow(workflow_path, CLOUD_CONFIG)
    
    if prompt_id:
        print(f"✓ Queued! Prompt ID: {prompt_id}")
        # Store prompt_id for tracking
    else:
        print("✗ Failed to queue workflow")
```

## Workflow Steps

The function performs these operations in sequence:

1. **SSH Connect** - Establish secure connection to cloud instance
2. **Upload File** - Copy workflow JSON to `/tmp/` on remote instance via SFTP
3. **Check Server** - Verify if browser server is running (`ps aux | grep browser_server`)
4. **Start Server** - If not running, start browser server in background (takes ~3 seconds)
5. **Queue Workflow** - Execute `queue_workflow_ui_click.py` with workflow path
6. **Return ID** - Extract and return prompt ID for status tracking

## Optional: Status Checking

```python
def check_status(prompt_id, cloud_config):
    """Check if workflow is running, pending, or completed."""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(
            hostname=cloud_config['hostname'],
            port=cloud_config['port'],
            username=cloud_config['username'],
            key_filename=cloud_config.get('key_filename'),
            timeout=10
        )
        
        # Check queue status
        cmd = f"curl -s {cloud_config['comfyui_url']}/queue"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode()
        
        if prompt_id in output:
            return "running" if "queue_running" in output else "pending"
        else:
            return "completed"  # or check history for details
            
    finally:
        ssh.close()
```

## Timing

- SSH connection: ~1-2 seconds
- File upload: <1 second for typical workflow (~100KB)
- Server startup: ~3 seconds (only if not already running)
- Queue execution: ~5-7 seconds
- **Total first run**: ~12 seconds
- **Total subsequent**: ~9 seconds (server already running)

## Error Handling

```python
try:
    prompt_id = queue_workflow(workflow_path, CLOUD_CONFIG)
    if prompt_id:
        # Success
        update_ui_status(f"Queued: {prompt_id}")
    else:
        # Failed (see stderr in function)
        update_ui_status("Queue failed - check logs")
except Exception as e:
    # Connection/SSH error
    update_ui_status(f"Error: {e}")
```

## Troubleshooting

**Connection timeout**: Increase `timeout=30` in `ssh.connect()`

**Server fails to start**: Check logs on cloud instance
```bash
ssh -p 19361 root@172.219.157.164 "cat /tmp/browser_server.log"
```

**Queue fails**: Verify workflow file is valid JSON and ComfyUI is running
```bash
ssh -p 19361 root@172.219.157.164 "curl -s http://localhost:18188 | head -10"
```

## Why UI-Click Method?

The `queue_workflow_ui_click.py` script clicks the "Queue Prompt" button in the browser UI instead of using the HTTP API. This ensures:

- **Full compatibility** with custom nodes that require UI metadata (e.g., WidgetToString)
- **Complete metadata preservation** - all workflow data is passed correctly
- **No TypeError issues** - works with all ComfyUI custom node types

For workflows without UI-dependent nodes, you can use `queue_workflow_simple.py` for slightly faster execution (~3 seconds faster).

---

**That's it!** Copy the `queue_workflow()` function into your WebUI and call it when the user generates a workflow.
