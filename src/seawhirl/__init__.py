"""A Python package for accelerating CLI spinners."""

from seawhirl._core.easing import (
    EasingStrategy,
    Inertial,
    Logarithmic,
    Sinusoidal,
    Spring
)
from seawhirl._core.exceptions import (
    BackendStartupError,
    InvalidColorError,
    InvalidPresetError,
    SeawhirlError
)
from seawhirl._core.presets import PRESETS
from seawhirl._lib.spinner import Spinner, Backend

__all__ = [
    'Backend',
    'BackendStartupError',
    'EasingStrategy',
    'Inertial',
    'InvalidColorError',
    'InvalidPresetError',
    'Logarithmic',
    'PRESETS',
    'SeawhirlError',
    'Sinusoidal',
    'Spinner',
    'Spring'
]
