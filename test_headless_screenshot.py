#!/usr/bin/env python3
"""Take a screenshot from the running browser server."""

from src.browser_agent.server.browser_client import BrowserClient
import time

# Connect to browser server
client = BrowserClient(port=9999)

# Wait a moment for page to fully load
print("Waiting for page to load...")
time.sleep(2)

# Take screenshot
screenshot_path = "outputs/comfyui_headless_screenshot.png"
print(f"Capturing screenshot to {screenshot_path}...")
result = client.screenshot(screenshot_path)

print(f"Result: {result}")

# Get page info for confirmation
info = client.info()
print(f"\nPage info:")
print(f"  URL: {info.get('url')}")
print(f"  Title: {info.get('title')}")
