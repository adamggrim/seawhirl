"""Spinner configuration objects."""

from dataclasses import dataclass
from seawhirl._core.easing import EasingStrategy

__all__ = ['SpinnerConfig', 'SpinnerState']


@dataclass(slots=True, frozen=True)
class SpinnerConfig:
    """Immutable configuration passed through the rendering pipeline."""
    accel_secs: float
    initial_fps: float
    peak_animation_fps: float
    loop_delay: float
    frames: list[str]
    easing: EasingStrategy
    status_frames: list[str]
    status_fps: float
    oscillation: bool


@dataclass(slots=True)
class SpinnerState:
    """Mutable state shared between the frontend interface and rendering engine."""
    status_text: str