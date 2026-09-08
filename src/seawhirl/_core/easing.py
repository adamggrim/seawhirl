import math
from typing import Protocol
from dataclasses import dataclass

__all__ = [
    'EASING_REGISTRY',
    'EasingStrategy',
    'Inertial',
    'Logarithmic',
    'Sinusoidal',
    'Spring',
    'get_easing_strategy'
]

MINIMUM_SAFE_BASE = 1.0001


class EasingStrategy(Protocol):
    """Protocol for calculating custom easing curves."""
    def calculate_multiplier(self, progress: float) -> float:
        ...


@dataclass(slots=True)
class Logarithmic:
    """Logarithmic curve for immediate acceleration."""
    base: float = 10.0

    def calculate_multiplier(self, progress: float) -> float:
        safe_base = max(MINIMUM_SAFE_BASE, self.base)
        return math.log(1 + (safe_base - 1) * progress, safe_base)


@dataclass(slots=True)
class Sinusoidal:
    """Sinusoidal curve for oscillating acceleration."""
    def calculate_multiplier(self, progress: float) -> float:
        return 0.5 * (1 - math.cos(math.pi * progress))


@dataclass(slots=True)
class Spring:
    """Spring-based curve with tension and friction."""
    tension: float = 5.0
    friction: float = 10.0

    def calculate_multiplier(self, progress: float) -> float:
        decay = math.exp(-self.tension * progress)
        oscillation = math.cos(self.friction * progress)
        return 1 - (decay * oscillation)


@dataclass(slots=True)
class Inertial:
    """Inertial curve with a power function."""
    power: float = 5.0

    def calculate_multiplier(self, progress: float) -> float:
        return math.pow(progress, self.power)


EASING_REGISTRY: dict[str, type[EasingStrategy]] = {
    'inertial': Inertial,
    'log': Logarithmic,
    'logarithmic': Logarithmic,
    'sin': Sinusoidal,
    'sine': Sinusoidal,
    'sinusoidal': Sinusoidal,
    'spring': Spring
}


def get_easing_strategy(name: str) -> EasingStrategy:
    """Factory function for retrieving easing algorithms."""
    return EASING_REGISTRY[name]()
