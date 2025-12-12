#!/usr/bin/env python3
"""
Vast.ai Browser Server - Maintains a persistent authenticated browser instance.

This server keeps a browser open with vast.ai authentication and listens for commands.
"""
from browser_agent.server.browser_server import BrowserServer
from pathlib import Path
import sys


def load_credentials(credentials_file: Path) -> tuple[str, str]:
    """Load credentials from the credentials file."""
    if not credentials_file.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {credentials_file}\n"
            "Please create it with format: username:password"
        )
    
    content = credentials_file.read_text().strip()
    # Skip comments and empty lines
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            if ":" in line:
                username, password = line.split(":", 1)
                return username.strip(), password.strip()
    
    raise ValueError(
        f"Invalid credentials format in {credentials_file}\n"
        "Expected format: username:password"
    )


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
    
    # Load credentials
    try:
        username, password = load_credentials(args.credentials_file)
        print(f"✅ Loaded credentials for user: {username}")
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    
    # Build URL with credentials for HTTP basic auth
    if "://" in args.url:
        scheme, rest = args.url.split("://", 1)
        auth_url = f"{scheme}://{username}:{password}@{rest}"
    else:
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
