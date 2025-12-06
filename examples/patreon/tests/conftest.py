"""Pytest configuration for Patreon example tests."""
import sys
from pathlib import Path

# Add examples/patreon to path so tests can import from there
sys.path.insert(0, str(Path(__file__).parent.parent))
