#!/usr/bin/env python3
"""Check what's actually on the page and try different selectors."""

from browser_agent.server import BrowserClient
import json

def inspect_page():
    """Inspect the current page to understand the structure."""
    client = BrowserClient(port=9999)
    
    print("Checking page structure...\n")
    
    # Check various selectors
    checks = [
        ("Post card divs", "document.querySelectorAll('div[data-tag=\"post-card\"]').length"),
        ("Post links", "document.querySelectorAll('a[href*=\"/posts/\"]').length"),
        ("All links count", "document.querySelectorAll('a').length"),
        ("Body scroll height", "document.body.scrollHeight"),
        ("Window inner height", "window.innerHeight"),
        ("Has 'Sign in' text", "document.body.innerText.includes('Sign in') || document.body.innerText.includes('Log in')"),
        ("Page loaded state", "document.readyState"),
    ]
    
    for name, js_code in checks:
        result = client.eval_js(js_code)
        if result.get("status") == "success":
            print(f"{name}: {result.get('result')}")
        else:
            print(f"{name}: ERROR - {result.get('message')}")
    
    # Check if we need to authenticate
    print("\n\nChecking for authentication requirement...")
    auth_check = client.eval_js("""
        ({
            hasSignInButton: !!document.querySelector('button:has-text("Sign in")') || 
                            !!document.querySelector('a[href*="login"]'),
            bodyText: document.body.innerText.substring(0, 500)
        })
    """)
    
    if auth_check.get("status") == "success":
        data = auth_check.get("result", {})
        print(f"Has sign-in button: {data.get('hasSignInButton')}")
        print(f"\nFirst 500 chars of page text:\n{data.get('bodyText')}")

if __name__ == "__main__":
    inspect_page()
