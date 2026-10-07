from typing import TypeAlias

from seawhirl._core.exceptions import InvalidColorError

__all__ = [
    'ColorInput',
    'RGB',
    'interpolate_ansi_color',
    'parse_color_spec',
]

RGB: TypeAlias = tuple[int, int, int]
ColorSpec: TypeAlias = str | RGB
ColorInput: TypeAlias = ColorSpec | tuple[ColorSpec, ColorSpec]

NAMED_COLORS: dict[str, RGB] = {
    'blue': (0, 120, 255),
    'cyan': (0, 255, 255),
    'gold': (255, 215, 0),
    'green': (0, 255, 128),
    'magenta': (255, 0, 255),
    'orange': (255, 140, 0),
    'purple': (160, 32, 240),
    'red': (255, 60, 60),
    'white': (255, 255, 255),
    'yellow': (255, 220, 0),
}


def parse_rgb(color: ColorSpec) -> RGB:
    """
    Parse a color name, 6-digit hex code or RGB tuple into an RGB tuple.
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
    if clean in NAMED_COLORS:
        return NAMED_COLORS[clean]

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
        f"({list(NAMED_COLORS.keys())}), a 6-digit hex code ('#00ffcc'), "
        'or an RGB tuple.'
    )


def parse_color_spec(color: ColorInput | None) -> tuple[RGB, RGB] | None:
    """
    Normalize a single color or two-color gradient into a (start, end)
    pair.
    """
    if color is None:
        return None

    if isinstance(color, str):
        if ',' in color:
            parts = [p.strip() for p in color.split(',')]
            if len(parts) != 2 or not all(parts):
                raise InvalidColorError(
                    f"Gradient string must contain two colors: '{color}'"
                )
            return (parse_rgb(parts[0]), parse_rgb(parts[1]))
        rgb = parse_rgb(color)
        return (rgb, rgb)

    if len(color) == 2:
        first, second = color
        return (parse_rgb(first), parse_rgb(second))

    if len(color) == 3 and all(isinstance(c, int) for c in color):
        rgb = parse_rgb(color)
        return (rgb, rgb)

    raise InvalidColorError(f"Invalid color specification: '{color}'")


def interpolate_ansi_color(
    start_rgb: RGB,
    end_rgb: RGB,
    multiplier: float
) -> str:
    """
    Interpolate between two RGB colors using the easing multiplier.
    """
    t = max(0.0, min(1.0, multiplier))
    r = round(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
    g = round(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
    b = round(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
    return f'\033[38;2;{r};{g};{b}m'
