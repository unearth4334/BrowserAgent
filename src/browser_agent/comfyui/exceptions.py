"""ComfyUI-specific exceptions."""


class ComfyUIError(Exception):
    """Base exception for ComfyUI operations."""
    pass


class WorkflowLoadError(ComfyUIError):
    """Raised when workflow fails to load."""
    pass


class QueueError(ComfyUIError):
    """Raised when workflow fails to queue."""
    pass


class ParameterError(ComfyUIError):
    """Raised when parameter setting fails."""
    pass


class ConnectionError(ComfyUIError):
    """Raised when connection to ComfyUI fails."""
    pass
