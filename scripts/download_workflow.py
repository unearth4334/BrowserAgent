#!/usr/bin/env python3
"""
Download workflow JSON file from remote cloud instance.
"""
import subprocess
import sys
from pathlib import Path
import argparse
import hashlib
import base64
from datetime import datetime
import re

# Remote connection details
REMOTE_HOST = "198.53.64.194"
REMOTE_PORT = "40548"
REMOTE_USER = "root"

# Remote workflows directory
REMOTE_WORKFLOWS_DIR = "/workspace/ComfyUI/user/default/workflows/"

# Default file path on remote
DEFAULT_REMOTE_PATH = "test_float_fix.json"

def parse_ssh_connection(ssh_string: str) -> tuple[str, str, str]:
    """
    Parse SSH connection string to extract host, port, and user.
    
    Args:
        ssh_string: SSH connection string like "ssh -p 40715 root@198.53.64.194 -L 8080:localhost:8080"
    
    Returns:
        Tuple of (host, port, user)
    """
    # Strip 'ssh' prefix if present
    ssh_string = re.sub(r'^ssh\s+', '', ssh_string)
    
    # Extract port using -p flag
    port_match = re.search(r'-p\s+(\d+)', ssh_string)
    port = port_match.group(1) if port_match else REMOTE_PORT
    
    # Extract user@host pattern
    user_host_match = re.search(r'([\w-]+)@([\w\.-]+)', ssh_string)
    if user_host_match:
        user = user_host_match.group(1)
        host = user_host_match.group(2)
    else:
        # Try to find just a hostname/IP
        host_match = re.search(r'([\d\.]+|[\w\.-]+)', ssh_string)
        host = host_match.group(1) if host_match else REMOTE_HOST
        user = REMOTE_USER
    
    return host, port, user

def download_workflow(remote_path: str, local_path: str, remote_host: str, remote_port: str, 
                      remote_user: str = "root", description: str = None, verbose: bool = True):
    """
    Download a workflow JSON file from the remote instance.
    
    Args:
        remote_path: Path to the file on the remote instance (relative or absolute)
        local_path: Where to save the file locally
        remote_host: Remote host address
        remote_port: Remote SSH port
        remote_user: Remote SSH user (default: root)
        description: Description for the workflow catalog entry
        verbose: Print progress messages
    """
    # If remote_path doesn't start with /, prepend workflows directory
    if not remote_path.startswith('/'):
        remote_path = REMOTE_WORKFLOWS_DIR + remote_path
    
    if verbose:
        print(f"Downloading workflow from remote instance...")
        print(f"  Remote: {remote_path}")
        print(f"  Local:  {local_path}")
    
    # Build scp command
    scp_source = f"{remote_user}@{remote_host}:{remote_path}"
    
    cmd = [
        "scp",
        "-P", remote_port,  # Port flag for scp
        scp_source,
        local_path
    ]
    
    if verbose:
        print(f"\nRunning: {' '.join(cmd)}")
        print()
    
    try:
        # Run scp command
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,  # Show progress in terminal
            text=True
        )
        
        if verbose:
            print(f"\n✓ Successfully downloaded to: {local_path}")
        
        # Verify file exists and show size
        local_file = Path(local_path)
        if local_file.exists():
            size_kb = local_file.stat().st_size / 1024
            if verbose:
                print(f"✓ File size: {size_kb:.2f} KB")
            
            # Calculate hash and rename file with hash suffix
            with open(local_file, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()[:8]
            
            # Create new filename with hash
            stem = local_file.stem
            suffix = local_file.suffix
            new_name = f"{stem}_{file_hash}{suffix}"
            new_path = local_file.parent / new_name
            
            # Rename file
            local_file.rename(new_path)
            
            if verbose:
                print(f"✓ Renamed with hash: {new_path.name}")
            
            # Update catalog if in outputs/workflows directory
            if "outputs/workflows" in str(new_path.parent):
                update_catalog(new_path, file_hash, description)
            
            return str(new_path)
    
    except subprocess.CalledProcessError as e:
        if verbose:
            print(f"✗ Error downloading file: {e}", file=sys.stderr)
        return None
    
    return local_path


def update_catalog(workflow_path: Path, file_hash: str, description: str = None):
    """Update the workflows catalog README with the new download."""
    catalog_path = workflow_path.parent / "README.md"
    
    if not catalog_path.exists():
        # Catalog doesn't exist, skip update
        return
    
    # Read current catalog
    content = catalog_path.read_text()
    
    # Get current date
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Always append new entry (don't update existing)
    desc = description if description else ""
    new_row = f"| {workflow_path.name} | {file_hash} | {desc} | {date_str} |"
    
    # Append to end of file
    if content.strip():
        content = content.rstrip() + '\n' + new_row + '\n'
    else:
        content = new_row + '\n'
    
    # Write updated catalog
    catalog_path.write_text(content)


def main():
    parser = argparse.ArgumentParser(
        description="Download workflow JSON file from remote ComfyUI instance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Download default workflow to current directory (hash appended automatically)
  {sys.argv[0]}
  
  # Download to specific location
  {sys.argv[0]} -o my_workflow.json
  
  # Download a different workflow (relative to workflows dir)
  {sys.argv[0]} -r my_workflow.json
  
  # Download from subdirectory
  {sys.argv[0]} -r folder/workflow.json
  
  # Use custom host and port
  {sys.argv[0]} --host 192.168.1.100 --port 22
  
  # Use SSH connection string
  {sys.argv[0]} --ssh "ssh -p 40715 root@198.53.64.194" -r workflow.json
  
Note: A hash will be automatically appended to the filename (e.g., workflow_a1b2c3d4e5f6.json)
  
Default connection details:
  Host: {REMOTE_HOST}
  Port: {REMOTE_PORT}
  User: {REMOTE_USER}
        """
    )
    
    parser.add_argument(
        "--host",
        default=REMOTE_HOST,
        help=f"Remote host address (default: {REMOTE_HOST})"
    )
    
    parser.add_argument(
        "--port",
        default=REMOTE_PORT,
        help=f"Remote SSH port (default: {REMOTE_PORT})"
    )
    
    parser.add_argument(
        "--user",
        default=REMOTE_USER,
        help=f"Remote SSH user (default: {REMOTE_USER})"
    )
    
    parser.add_argument(
        "--ssh",
        default=None,
        help="SSH connection string (e.g., 'ssh -p 40715 root@198.53.64.194'). Overrides --host, --port, and --user"
    )
    
    parser.add_argument(
        "-r", "--remote-path",
        default=DEFAULT_REMOTE_PATH,
        help=f"Workflow filename or absolute path (default: {DEFAULT_REMOTE_PATH}). Relative paths use {REMOTE_WORKFLOWS_DIR}"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="outputs/workflows/WAN2.2_IMG_to_VIDEO_Base.json",
        help="Local output filename (hash will be appended automatically)"
    )
    
    parser.add_argument(
        "-d", "--description",
        default=None,
        help="Description for the workflow catalog entry"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )
    
    args = parser.parse_args()
    
    # Parse SSH connection string if provided
    if args.ssh:
        host, port, user = parse_ssh_connection(args.ssh)
    else:
        host = args.host
        port = args.port
        user = args.user
    
    # Download the file
    final_path = download_workflow(
        remote_path=args.remote_path,
        local_path=args.output,
        remote_host=host,
        remote_port=port,
        remote_user=user,
        description=args.description,
        verbose=not args.quiet
    )
    
    sys.exit(0 if final_path else 1)

if __name__ == "__main__":
    main()
