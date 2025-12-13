#!/usr/bin/env python3
"""
Test script for the VastAI API server.

This script tests all API endpoints to ensure they work correctly.
"""
import requests
import time
import sys
from pathlib import Path


def test_api(base_url: str = "http://localhost:8000"):
    """Test all API endpoints."""
    print(f"🧪 Testing VastAI API at {base_url}\n")
    
    # Test 1: Root endpoint
    print("1. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        response.raise_for_status()
        data = response.json()
        print(f"   ✅ Root endpoint: {data['name']}")
        print(f"      Available endpoints: {len(data['endpoints'])}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 2: Session status (should be inactive)
    print("\n2. Testing session status (should be inactive)...")
    try:
        response = requests.get(f"{base_url}/session/status")
        response.raise_for_status()
        data = response.json()
        if not data['active']:
            print(f"   ✅ Session inactive as expected")
        else:
            print(f"   ⚠️  Session already active on port {data.get('port')}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 3: Try to open workflow without session (should fail)
    print("\n3. Testing workflow open without session (should fail)...")
    try:
        response = requests.post(f"{base_url}/workflow/open", json={
            "workflow_path": "test.json"
        })
        if response.status_code == 400:
            print(f"   ✅ Correctly rejected: {response.json()['detail']}")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 4: Try to queue workflow without session (should fail)
    print("\n4. Testing workflow queue without session (should fail)...")
    try:
        response = requests.post(f"{base_url}/workflow/queue", json={
            "iterations": 1
        })
        if response.status_code == 400:
            print(f"   ✅ Correctly rejected: {response.json()['detail']}")
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    print("\n✅ All API endpoint tests passed!")
    print("\nTo test with actual credentials, use:")
    print("  curl -X POST http://localhost:8000/session/start \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{")
    print('      "credentials": {')
    print('        "username": "your_username",')
    print('        "password": "your_password",')
    print('        "url": "https://your-instance.trycloudflare.com"')
    print("      },")
    print('      "headless": true')
    print("    }'")
    
    return True


def test_with_credentials(base_url: str, username: str, password: str, url: str):
    """Test API with actual credentials (requires vast.ai instance)."""
    print(f"🧪 Testing VastAI API with credentials at {base_url}\n")
    
    # Start session
    print("1. Starting authenticated session...")
    try:
        response = requests.post(f"{base_url}/session/start", json={
            "credentials": {
                "username": username,
                "password": password,
                "url": url
            },
            "headless": True,
            "port": 9999
        })
        response.raise_for_status()
        data = response.json()
        if data['success']:
            print(f"   ✅ {data['message']}")
            print(f"      Details: {data['details']}")
        else:
            print(f"   ❌ Failed: {data['message']}")
            return False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Wait for server to fully start
    print("\n   Waiting for browser server to initialize...")
    time.sleep(3)
    
    # Check status
    print("\n2. Checking session status...")
    try:
        response = requests.get(f"{base_url}/session/status")
        response.raise_for_status()
        data = response.json()
        if data['active']:
            print(f"   ✅ Session active on port {data['port']}")
            print(f"      URL: {data.get('url', 'N/A')}")
        else:
            print(f"   ❌ Session not active")
            return False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Stop session
    print("\n3. Stopping session...")
    try:
        response = requests.post(f"{base_url}/session/stop")
        response.raise_for_status()
        data = response.json()
        if data['success']:
            print(f"   ✅ {data['message']}")
        else:
            print(f"   ⚠️  {data['message']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    print("\n✅ All tests with credentials passed!")
    return True


def load_credentials(credentials_file: Path) -> tuple[str, str, str]:
    """Load credentials from file."""
    if not credentials_file.exists():
        return None, None, None
    
    content = credentials_file.read_text().strip()
    non_comment_lines = []
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            non_comment_lines.append(line)
    
    username = password = url = None
    
    if len(non_comment_lines) >= 1 and ":" in non_comment_lines[0]:
        username, password = non_comment_lines[0].split(":", 1)
        username = username.strip()
        password = password.strip()
    
    if len(non_comment_lines) >= 2:
        url = non_comment_lines[1].strip()
    
    return username, password, url


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test VastAI API server endpoints"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="API server URL (default: %(default)s)",
    )
    parser.add_argument(
        "--with-credentials",
        action="store_true",
        help="Run tests with actual credentials from vastai_credentials.txt",
    )
    parser.add_argument(
        "--credentials-file",
        type=str,
        default="vastai_credentials.txt",
        help="Path to credentials file (default: %(default)s)",
    )
    
    args = parser.parse_args()
    
    # Basic API tests
    success = test_api(args.url)
    if not success:
        return 1
    
    # Test with credentials if requested
    if args.with_credentials:
        credentials_path = Path(__file__).parent.parent.parent / args.credentials_file
        username, password, url = load_credentials(credentials_path)
        
        if not all([username, password, url]):
            print(f"\n⚠️  Could not load credentials from {credentials_path}")
            print("   Skipping credential tests")
        else:
            print(f"\n{'='*60}\n")
            success = test_with_credentials(args.url, username, password, url)
            if not success:
                return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
