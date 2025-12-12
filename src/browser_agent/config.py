from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Literal


@dataclass
class Settings:
    """Global configuration for the browser agent."""

    browser_executable_path: str | None = None
    headless: bool = True
    browser_type: Literal["chromium", "firefox", "webkit"] = "chromium"
    launch_timeout: int = 15000  # milliseconds
    navigation_timeout: int = 30000  # milliseconds
    default_wait: Literal["load", "domcontentloaded", "networkidle"] = "load"
    extra_launch_args: list[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        exe = os.getenv("BROWSER_AGENT_BROWSER_EXE") or None
        headless_raw = os.getenv("BROWSER_AGENT_HEADLESS", "1")
        browser_type = os.getenv("BROWSER_AGENT_BROWSER_TYPE", "chromium")
        launch_timeout_raw = os.getenv("BROWSER_AGENT_LAUNCH_TIMEOUT", "15000")
        navigation_timeout_raw = os.getenv("BROWSER_AGENT_NAVIGATION_TIMEOUT", "30000")
        default_wait = os.getenv("BROWSER_AGENT_DEFAULT_WAIT", "load")

        # Parse extra launch args from environment (comma-separated)
        extra_args_raw = os.getenv("BROWSER_AGENT_EXTRA_ARGS", "")
        extra_args = [arg.strip() for arg in extra_args_raw.split(",") if arg.strip()]

        return cls(
            browser_executable_path=exe,
            headless=headless_raw.lower() not in ("0", "false", "no"),
            browser_type=browser_type,  # type: ignore[arg-type]
            launch_timeout=int(launch_timeout_raw),
            navigation_timeout=int(navigation_timeout_raw),
            default_wait=default_wait,  # type: ignore[arg-type]
            extra_launch_args=extra_args,
        )
