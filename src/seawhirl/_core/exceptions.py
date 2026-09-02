__all__ = [
    'BackendStartupError',
    'InvalidPresetError',
    'SeawhirlError'
]


class SeawhirlError(Exception):
    """Base class for all seawhirl errors."""


class BackendStartupError(SeawhirlError):
    """Exception raised when a backend cannot be started."""


class InvalidPresetError(SeawhirlError):
    """Exception raised when an invalid preset name is requested."""
