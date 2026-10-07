__all__ = [
    'BackendStartupError',
    'InvalidColorError',
    'InvalidPresetError',
    'SeawhirlError'
]


class SeawhirlError(Exception):
    """Base class for all package errors."""


class BackendStartupError(SeawhirlError):
    """Exception raised when a backend cannot be started."""


class InvalidColorError(SeawhirlError):
    """Exception raised for an invalid color."""


class InvalidPresetError(SeawhirlError):
    """Exception raised for an invalid preset name."""
