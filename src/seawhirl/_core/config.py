from dataclasses import dataclass
from seawhirl._core.easing import EasingStrategy

__all__ = ['SpinnerConfig']


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
