#!/usr/bin/env python3
"""
Vast.ai Browser Server - Maintains a persistent authenticated browser instance.

This server keeps a browser open with vast.ai authentication and listens for commands.
"""
from browser_agent.server.browser_server import BrowserServer
from pathlib import Path
import sys


def load_credentials(credentials_file: Path) -> tuple[str, str, str, str]:
    """Load credentials, URL, and workflow path from the credentials file.
    
    Returns:
        tuple[str, str, str, str]: username, password, url, workflow_path
    """
    if not credentials_file.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {credentials_file}\n"
            "Please create it with format:\n"
            "  Line 1: username:password\n"
            "  Line 2: url\n"
            "  Line 3: workflow_path"
        )
    
    content = credentials_file.read_text().strip()
    username = None
    password = None
    url = None
    workflow_path = None
    
    # Parse the file looking for credentials, URL, and workflow
    non_comment_lines = []
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            non_comment_lines.append(line)
    
    # First line with colon is username:password
    if len(non_comment_lines) >= 1 and ":" in non_comment_lines[0]:
        username, password = non_comment_lines[0].split(":", 1)
        username = username.strip()
        password = password.strip()
    
    # Second line is URL
    if len(non_comment_lines) >= 2:
        url = non_comment_lines[1].strip()
    
    # Third line is workflow path (optional)
    if len(non_comment_lines) >= 3:
        workflow_path = non_comment_lines[2].strip()
    
    if not username or not password:
        raise ValueError(
            f"Invalid credentials format in {credentials_file}\n"
            "Expected format:\n"
            "  Line 1: username:password\n"
            "  Line 2: url\n"
            "  Line 3: workflow_path (optional)"
        )
    
    if not url:
        raise ValueError(
            f"URL not found in {credentials_file}\n"
            "Expected format:\n"
            "  Line 1: username:password\n"
            "  Line 2: url\n"
            "  Line 3: workflow_path (optional)"
        )
    
    return username, password, url, workflow_path


def main():
    import argparse
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    
    parser = argparse.ArgumentParser(
        description="Start browser server for vast.ai with authentication"
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Vast.ai URL (overrides URL from credentials file)",
    )
    parser.add_argument(
        "--workflow",
        default=None,
        help="ComfyUI workflow path (overrides workflow from credentials file)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9999,
        help="Server port (default: %(default)s)",
    )
    parser.add_argument(
        "--browser-exe",
        default="/usr/bin/brave-browser",
        help="Browser executable path (default: %(default)s)",
    )
    parser.add_argument(
        "--credentials-file",
        type=Path,
        default=project_root / "vastai_credentials.txt",
        help="Path to credentials file (default: vastai_credentials.txt)",
    )
    
    args = parser.parse_args()
    
    # Load credentials, URL, and workflow
    try:
        username, password, url, workflow_path = load_credentials(args.credentials_file)
        print(f"✅ Loaded credentials for user: {username}")
        print(f"✅ Loaded URL: {url}")
        if workflow_path:
            print(f"✅ Loaded workflow: {workflow_path}")
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    
    # Use command-line arguments if provided, otherwise use from credentials file
    target_url = args.url if args.url else url
    target_workflow = args.workflow if args.workflow else workflow_path
    
    # Build URL with credentials for HTTP basic auth
    if "://" in target_url:
        scheme, rest = target_url.split("://", 1)
        auth_url = f"{scheme}://{username}:{password}@{rest}"
    else:
        auth_url = f"https://{username}:{password}@{target_url}"
    
    print(f"\n🚀 Starting browser server on port {args.port}")
    print(f"   Target URL: {target_url}")
    if target_workflow:
        print(f"   Workflow: {target_workflow}")
    print(f"   Browser: {args.browser_exe}")
    print()
    
    # Create and start server (without wait_for_auth since HTTP basic auth is automatic)
    server = BrowserServer(browser_exe=args.browser_exe, port=args.port)
    server.start(initial_url=auth_url, wait_for_auth=False)


if __name__ == "__main__":
    sys.exit(main())
