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


Action = Union[Navigate, Click, Type, WaitForSelector]
