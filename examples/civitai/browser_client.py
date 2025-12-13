#!/usr/bin/env python3
"""
Civitai Browser Client - Simple wrapper around main implementation.
"""
import sys
from pathlib import Path

# Add parent directory to path to import from main implementation
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from browser_agent.server.browser_client import main

if __name__ == "__main__":
    main()
