import pytest

from seawhirl._core.colors import interpolate_ansi_color, parse_color_spec
from seawhirl._core.exceptions import InvalidColorError


def test_parse_color_spec_variants() -> None:
    assert parse_color_spec(None) is None
    assert parse_color_spec('cyan') == ((0, 255, 255), (0, 255, 255))
    assert parse_color_spec('#ff0066') == ((255, 0, 102), (255, 0, 102))
    assert parse_color_spec((10, 20, 30)) == ((10, 20, 30), (10, 20, 30))
    assert parse_color_spec(('cyan', 'magenta')) == (
        (0, 255, 255),
        (255, 0, 255)
    )
    assert parse_color_spec('cyan,magenta') == (
        (0, 255, 255),
        (255, 0, 255)
    )


def test_parse_color_spec_invalid() -> None:
    with pytest.raises(InvalidColorError):
        parse_color_spec('not_a_color')

    with pytest.raises(InvalidColorError):
        parse_color_spec('#zzzzzz')

    with pytest.raises(InvalidColorError):
        parse_color_spec((300, 0, 0))

    with pytest.raises(InvalidColorError):
        parse_color_spec('cyan,magenta,yellow')


def test_interpolate_ansi_color() -> None:
    start = (0, 0, 0)
    end = (100, 200, 250)

    assert interpolate_ansi_color(start, end, 0.5) == '\033[38;2;50;100;125m'
    assert interpolate_ansi_color(start, end, 1.5) == '\033[38;2;100;200;250m'
    assert interpolate_ansi_color(start, end, -0.5) == '\033[38;2;0;0;0m'
