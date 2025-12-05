from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ButtonInfo:
    selector: str
    text: str


@dataclass
class InputInfo:
    selector: str
    name: Optional[str]
    value: Optional[str]


@dataclass
class PageObservation:
    url: str
    title: str
    buttons: List[ButtonInfo]
    inputs: List[InputInfo]
    raw_html: Optional[str] = None
