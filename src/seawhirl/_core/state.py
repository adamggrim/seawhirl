"""State management for the spinner."""

from dataclasses import dataclass

__all__ = ['SpinnerState']


@dataclass(slots=True)
class SpinnerState:
    """
    Mutable state shared between the frontend `Spinner` interface and
    the background rendering engine.
    """
    status_text: str
