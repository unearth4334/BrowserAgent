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


@dataclass
class ExecuteJS:
    """Execute JavaScript code in the page context."""
    code: str


@dataclass
class UploadFile:
    """Upload a file to a file input element."""
    selector: str
    file_path: str


@dataclass
class SelectOption:
    """Select an option from a dropdown/select element."""
    selector: str
    value: str


@dataclass
class SetSlider:
    """Set a slider value."""
    selector: str
    value: float


@dataclass
class Screenshot:
    """Capture a screenshot of the current page or element."""
    path: str
    selector: str | None = None  # If provided, screenshot only this element
    full_page: bool = False  # If True, capture full scrollable page


@dataclass
class ClickAtCoordinates:
    """Click at specific x, y coordinates on the page."""
    x: int
    y: int
    button: str = "left"  # "left", "right", or "middle"


Action = Union[
    Navigate,
    Click,
    Type,
    WaitForSelector,
    WaitForUser,
    ExtractLinks,
    ExtractHTML,
    ExecuteJS,
    UploadFile,
    SelectOption,
    SetSlider,
    Screenshot,
    ClickAtCoordinates,
]
