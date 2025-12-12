#!/usr/bin/env python3
"""
Vast.ai Browser Server - Maintains a persistent authenticated browser instance.

This server keeps a browser open with vast.ai authentication and listens for commands.
"""
from browser_agent.server.browser_server import BrowserServer
from pathlib import Path
import sys


def load_credentials(credentials_file: Path) -> tuple[str, str, str]:
    """Load credentials and URL from the credentials file.
    
    Returns:
        tuple[str, str, str]: username, password, url
    """
    if not credentials_file.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {credentials_file}\n"
            "Please create it with format:\n"
            "  Line 1: username:password\n"
            "  Line 2: url"
        )
    
    content = credentials_file.read_text().strip()
    username = None
    password = None
    url = None
    
    # Parse the file looking for credentials and URL
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            if ":" in line and username is None:
                # First line with colon is username:password
                username, password = line.split(":", 1)
                username = username.strip()
                password = password.strip()
            elif line.startswith("http"):
                # Line starting with http is the URL
                url = line.strip()
    
    parser.add_argument(
        "--url",
        default=None,
        help="Vast.ai URL (overrides URL from credentials file)",
    )       "  Line 1: username:password\n"
            "  Line 2: url"
        )
    
    if not url:
        raise ValueError(
            f"URL not found in {credentials_file}\n"
            "Expected format:\n"
            "  Line 1: username:password\n"
            "  Line 2: url"
        )
    
    return username, password, url


def main():
    import argparse
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    
    parser = argparse.ArgumentParser(
        description="Start browser server for vast.ai with authentication"
    )
    parser.add_argument(
        "--url",
        default="https://disks-gba-says-facts.trycloudflare.com/",
        help="Vast.ai URL (default: %(default)s)",
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
    
    # Load credentials and URL
    try:
        username, password, url = load_credentials(args.credentials_file)
        print(f"✅ Loaded credentials for user: {username}")
        print(f"✅ Loaded URL: {url}")
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    # Build URL with credentials for HTTP basic auth
    if "://" in target_url:
        scheme, rest = target_url.split("://", 1)
        auth_url = f"{scheme}://{username}:{password}@{rest}"
    else:
        auth_url = f"https://{username}:{password}@{target_url}"
    
    print(f"\n🚀 Starting browser server on port {args.port}")
    print(f"   Target URL: {target_url}")
        auth_url = f"https://{username}:{password}@{args.url}"
    
    print(f"\n🚀 Starting browser server on port {args.port}")
    print(f"   Target URL: {args.url}")
    print(f"   Browser: {args.browser_exe}")
    print()
    
    # Create and start server (without wait_for_auth since HTTP basic auth is automatic)
    server = BrowserServer(browser_exe=args.browser_exe, port=args.port)
    server.start(initial_url=auth_url, wait_for_auth=False)


if __name__ == "__main__":
    sys.exit(main())
