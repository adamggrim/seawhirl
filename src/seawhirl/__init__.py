"""A Python package for accelerating CLI spinners."""

from seawhirl._core.easing import (
    EasingStrategy,
    Inertial,
    Logarithmic,
    Sinusoidal,
    Spring
)
from seawhirl._core.presets import PRESETS
from seawhirl._lib.spinner import Spinner, Backend

__all__ = [
    'Backend',
    'EasingStrategy',
    'Inertial',
    'Logarithmic',
    'PRESETS',
    'Sinusoidal',
    'Spinner',
    'Spring'
]
