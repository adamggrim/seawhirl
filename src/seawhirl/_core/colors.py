"""Color parsing utilities."""

import math
from collections.abc import Sequence
from typing import TypeAlias, cast

from seawhirl._core.exceptions import InvalidColorError
from seawhirl._core.palette import COLOR_REGISTRY, RGB

__all__ = [
    'COLOR_REGISTRY',
    'ColorInput',
    'interpolate_ansi_color',
    'interpolate_indexed_ansi_color',
    'parse_color_spec',
    'register_color'
]

ColorSpec: TypeAlias = str | RGB
ColorInput: TypeAlias = ColorSpec | Sequence[ColorSpec]


def _is_rgb_tuple(value: object) -> bool:
    """Check if an object is a raw 3-integer tuple candidate for RGB."""
    return (
        isinstance(value, tuple)
        and len(value) == 3
        and all(isinstance(c, int) for c in value)
    )


def _lerp_ansi(start_rgb: RGB, end_rgb: RGB, t: float) -> str:
    """Format a linearly interpolated RGB pair as an ANSI escape
    sequence.
    """
    r = round(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
    g = round(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
    b = round(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
    return f'\033[38;2;{r};{g};{b}m'


def _parse_rgb(color: ColorSpec) -> RGB:
    """Parse a color name, 6-digit hex code or RGB tuple into an RGB
    tuple.
    """
    if isinstance(color, tuple):
        if (
            len(color) == 3
            and all(isinstance(c, int) and 0 <= c <= 255 for c in color)
        ):
            return (color[0], color[1], color[2])
        raise InvalidColorError(
            f"RGB tuple values must be integers in 0..255: '{color}'"
        )

    clean = color.strip().lower()
    if clean in COLOR_REGISTRY:
        return COLOR_REGISTRY[clean]

    hex_str = clean.lstrip('#')
    if len(hex_str) == 6:
        try:
            return (
                int(hex_str[0:2], 16),
                int(hex_str[2:4], 16),
                int(hex_str[4:6], 16)
            )
        except ValueError as e:
            raise InvalidColorError(f"Invalid hex color: '{color}'") from e

    raise InvalidColorError(
        f"Unknown color: '{color}'. Use a named color "
        f"({list(COLOR_REGISTRY.keys())}), a 6-digit hex code ('#00ffcc'), "
        'or an RGB tuple.'
    )


def parse_color_spec(color: ColorInput | None) -> tuple[RGB, ...] | None:
    """Normalize a single color, comma-separated string or sequence of
    colors into a tuple of RGB stops.
    """
    if color is None:
        return None

    if isinstance(color, str):
        if ',' in color:
            parts = [p.strip() for p in color.split(',')]
            if len(parts) < 2 or not all(parts):
                raise InvalidColorError(
                    'Gradient string must contain at least two '
                    f"non-empty colors: '{color}'"
                )
            return tuple(_parse_rgb(p) for p in parts)
        rgb = _parse_rgb(color)
        return (rgb, rgb)

    if _is_rgb_tuple(color):
        rgb = _parse_rgb(cast(RGB, color))
        return (rgb, rgb)

    if isinstance(color, Sequence):
        color_seq = cast(Sequence[ColorSpec], color)
        if len(color_seq) == 0:
            raise InvalidColorError('Color sequence cannot be empty.')
        if len(color_seq) == 1:
            rgb = _parse_rgb(color_seq[0])
            return (rgb, rgb)
        return tuple(_parse_rgb(c) for c in color_seq)

    raise InvalidColorError(f"Invalid color specification: '{color}'")


def interpolate_ansi_color(
    colors: Sequence[RGB],
    multiplier: float
) -> str:
    """Interpolate ANSI colors across RGB color stops."""
    if not colors:
        raise InvalidColorError('Provide at least one RGB color.')
    if len(colors) == 1:
        return _lerp_ansi(colors[0], colors[0], 0.0)

    t = max(0.0, min(1.0, multiplier))
    segments = len(colors) - 1
    scaled = t * segments
    idx = min(int(scaled), segments - 1)
    return _lerp_ansi(colors[idx], colors[idx + 1], scaled - idx)


def interpolate_indexed_ansi_color(
    colors: Sequence[RGB],
    color_index: float
) -> str:
    """Interpolate between adjacent RGB stops.

    Integer values of `color_index` (0, 1, 2, ...) map directly to
    `colors[i % len(colors)]`.
    """
    if not colors:
        raise InvalidColorError('Provide at least one RGB color.')
    if len(colors) == 1:
        return _lerp_ansi(colors[0], colors[0], 0.0)

    num_colors = len(colors)
    clamped = max(0.0, color_index)
    base_idx = math.floor(clamped)
    return _lerp_ansi(
        colors[base_idx % num_colors],
        colors[(base_idx + 1) % num_colors],
        clamped - base_idx
    )

def register_color(name: str, color: ColorSpec) -> None:
    """Register a custom named color into the global registry."""
    COLOR_REGISTRY[name.strip().lower()] = _parse_rgb(color)
