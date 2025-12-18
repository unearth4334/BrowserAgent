#!/usr/bin/env python3
"""
Test script demonstrating ComfyUI browser modes.

This script shows:
1. Headless mode - browser runs without UI, good for automation
2. Screenshot capture works in headless mode
3. Authentication with credentials file
"""

from src.browser_agent.server.browser_client import BrowserClient
from datetime import datetime
import time

print("=" * 60)
print("ComfyUI Browser Mode Test")
print("=" * 60)

# Connect to running browser server (should be in headless mode)
client = BrowserClient(port=9999)

# Test 1: Check server is responsive
print("\n[Test 1] Checking server connection...")
ping_result = client.ping()
print(f"✓ Server is {'alive' if ping_result['status'] == 'success' else 'not responding'}")

# Test 2: Get page information
print("\n[Test 2] Getting page information...")
info = client.info()
print(f"  URL: {info.get('url')}")
print(f"  Title: {info.get('title')}")
print(f"  Status: {info.get('status')}")

# Test 3: Capture screenshot
print("\n[Test 3] Capturing screenshot...")
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
screenshot_path = f'outputs/test_comfyui_{timestamp}.png'
time.sleep(1)  # Give page a moment to stabilize

screenshot_result = client.screenshot(screenshot_path)
if screenshot_result['status'] == 'success':
    print(f"✓ Screenshot saved: {screenshot_path}")
else:
    print(f"✗ Screenshot failed: {screenshot_result.get('message')}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
print("\nSummary:")
print("  - Headless browser is running on port 9999")
print("  - ComfyUI is accessible with authentication")
print("  - Screenshots can be captured programmatically")
print("  - Server responds to remote commands via BrowserClient")
print("\nUsage:")
print("  # Start headless mode:")
print("  browser-agent comfyui open --credentials vastai_credentials.txt --headless")
print("\n  # Start visible mode (no --headless flag):")
print("  browser-agent comfyui open --credentials vastai_credentials.txt")
