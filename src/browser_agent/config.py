from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass
class Settings:
    """Global configuration for the browser agent."""

    browser_executable_path: str | None = None
    headless: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        exe = os.getenv("BROWSER_AGENT_BROWSER_EXE") or None
        headless_raw = os.getenv("BROWSER_AGENT_HEADLESS", "1")

        return cls(
            browser_executable_path=exe,
            headless=headless_raw.lower() not in ("0", "false", "no"),
        )
