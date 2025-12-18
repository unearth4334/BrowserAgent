#!/usr/bin/env python3
"""
Download workflow JSON file from remote cloud instance.
"""
import subprocess
import sys
from pathlib import Path
import argparse

# Remote connection details
REMOTE_HOST = "198.53.64.194"
REMOTE_PORT = "40671"
REMOTE_USER = "root"

# Default file path on remote
DEFAULT_REMOTE_PATH = "/workspace/ComfyUI/user/default/workflows/UmeAiRT/WAN2.2_IMG_to_VIDEO_Base.json"

def download_workflow(remote_path: str, local_path: str, verbose: bool = True):
    """
    Download a workflow JSON file from the remote instance.
    
    Args:
        remote_path: Path to the file on the remote instance
        local_path: Where to save the file locally
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
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error downloading file: {e}", file=sys.stderr)
        return False
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Download cancelled by user", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Download workflow JSON file from remote ComfyUI instance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Download default workflow to current directory
  {sys.argv[0]}
  
  # Download to specific location
  {sys.argv[0]} -o my_workflow.json
  
  # Download a different workflow
  {sys.argv[0]} -r /workspace/ComfyUI/user/default/workflows/folder/workflow.json
  
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
        default="WAN2.2_IMG_to_VIDEO_Base.json",
        help="Local output filename (default: WAN2.2_IMG_to_VIDEO_Base.json)"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )
    
    args = parser.parse_args()
    
    # Download the file
    success = download_workflow(
        remote_path=args.remote_path,
        local_path=args.output,
        verbose=not args.quiet
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
