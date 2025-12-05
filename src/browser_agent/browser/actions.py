from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass
class Navigate:
    url: str


@dataclass
class Click:
    selector: str


@dataclass
class Type:
    selector: str
    text: str
    press_enter: bool = False


@dataclass
class WaitForSelector:
    selector: str
    timeout_ms: int = 5000


@dataclass
class WaitForUser:
    """Pause execution and wait for user to press Enter to continue."""
    message: str = "Press Enter to continue..."


@dataclass
class ExtractLinks:
    """Extract links matching a pattern from the current page."""
    pattern: str  # CSS selector or pattern to match


@dataclass
class ExtractHTML:
    """Extract HTML content matching a selector from the current page."""
    selector: str  # CSS selector to match elements


Action = Union[Navigate, Click, Type, WaitForSelector, WaitForUser, ExtractLinks, ExtractHTML]
