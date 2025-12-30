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

# Remote connection details
REMOTE_HOST = "198.53.64.194"
REMOTE_PORT = "40671"
REMOTE_USER = "root"

# Default file path on remote
DEFAULT_REMOTE_PATH = "/workspace/ComfyUI/user/default/workflows/webui_test_output.json"

def download_workflow(remote_path: str, local_path: str, description: str = None, verbose: bool = True):
    """
    Download a workflow JSON file from the remote instance.
    
    Args:
        remote_path: Path to the file on the remote instance
        local_path: Where to save the file locally
        description: Description for the workflow catalog entry
        verbose: Print progress messages
    """
    if verbose:
        print(f"Downloading workflow from remote instance...")
        print(f"  Remote: {remote_path}")
        print(f"  Local:  {local_path}")
    
    # Build scp command
    scp_source = f"{REMOTE_USER}@{REMOTE_HOST}:{remote_path}"
    
    cmd = [
        "scp",
        "-P", REMOTE_PORT,  # Port flag for scp
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
  
  # Download a different workflow
  {sys.argv[0]} -r /workspace/ComfyUI/user/default/workflows/folder/workflow.json
  
Note: A hash will be automatically appended to the filename (e.g., workflow_a1b2c3d4e5f6.json)
  
Connection details:
  Host: {REMOTE_HOST}
  Port: {REMOTE_PORT}
  User: {REMOTE_USER}
        """
    )
    
    parser.add_argument(
        "-r", "--remote-path",
        default=DEFAULT_REMOTE_PATH,
        help=f"Path to workflow file on remote instance (default: {DEFAULT_REMOTE_PATH})"
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
    
    # Download the file
    final_path = download_workflow(
        remote_path=args.remote_path,
        local_path=args.output,
        description=args.description,
        verbose=not args.quiet
    )
    
    sys.exit(0 if final_path else 1)

if __name__ == "__main__":
    main()
