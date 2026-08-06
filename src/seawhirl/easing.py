import math
from typing import Protocol
from dataclasses import dataclass


class EasingStrategy(Protocol):
    def calculate_multiplier(self, progress: float) -> float:
        ...


@dataclass
class Logarithmic:
    base: float = 10.0

    def calculate_multiplier(self, progress: float) -> float:
        safe_base = max(1.0001, self.base)
        return math.log(1 + (safe_base - 1) * progress, safe_base)


@dataclass
class Sinusoidal:
    def calculate_multiplier(self, progress: float) -> float:
        return 0.5 * (1 - math.cos(math.pi * progress))


@dataclass
class Spring:
    tension: float = 5.0
    friction: float = 10.0

    def calculate_multiplier(self, progress: float) -> float:
        decay = math.exp(-self.tension * progress)
        oscillation = math.cos(self.friction * progress)
        return 1 - (decay * oscillation)


@dataclass
class Inertial:
    power: float = 5.0

    def calculate_multiplier(self, progress: float) -> float:
        return math.pow(progress, self.power)
