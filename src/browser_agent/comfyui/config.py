"""ComfyUI configuration."""

from dataclasses import dataclass
from typing import Literal
import os


@dataclass
class ComfyUIConfig:
    """ComfyUI client configuration."""
    
    # Connection
    url: str = "http://localhost:18188"
    timeout: float = 30.0
    
    # Workflow Loading
    default_load_method: Literal["ui_native", "api", "hybrid"] = "ui_native"
    chunk_size: int = 50000  # For localStorage chunking
    
    # Queuing
    default_queue_method: Literal["ui_click", "http_api"] = "ui_click"
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Monitoring
    check_interval: float = 2.0
    max_wait_time: float = 600.0
    
    # Browser
    headless: bool = True
    browser_port: int = 9999
    
    @classmethod
    def from_env(cls) -> "ComfyUIConfig":
        """Load configuration from environment variables."""
        return cls(
            url=os.getenv("COMFYUI_URL", cls.url),
            timeout=float(os.getenv("COMFYUI_TIMEOUT", str(cls.timeout))),
            headless=os.getenv("COMFYUI_HEADLESS", "true").lower() in ("true", "1", "yes"),
            browser_port=int(os.getenv("COMFYUI_BROWSER_PORT", str(cls.browser_port))),
        )
