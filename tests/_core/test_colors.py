import pytest

from seawhirl._core.colors import (
    interpolate_ansi_color,
    interpolate_indexed_ansi_color,
    parse_color_spec,
)
from seawhirl._core.exceptions import InvalidColorError

TWO_STOPS = ((0, 0, 0), (100, 200, 250))
THREE_STOPS = ((0, 0, 0), (100, 100, 100), (200, 200, 200))


@pytest.mark.parametrize(
    ('color_input', 'expected'),
    [
        (None, None),
        ('cyan', ((0, 255, 255), (0, 255, 255))),
        ('#ff0066', ((255, 0, 102), (255, 0, 102))),
        ((10, 20, 30), ((10, 20, 30), (10, 20, 30))),
        (['cyan'], ((0, 255, 255), (0, 255, 255))),
        (('cyan', 'magenta'), ((0, 255, 255), (255, 0, 255))),
        ('cyan,magenta', ((0, 255, 255), (255, 0, 255))),
        (
            'cyan,magenta,yellow',
            ((0, 255, 255), (255, 0, 255), (255, 255, 0)),
        ),
        (
            ['cyan', '#ff0066', (10, 20, 30)],
            ((0, 255, 255), (255, 0, 102), (10, 20, 30)),
        ),
    ],
)
def test_parse_color_spec_variants(color_input, expected) -> None:
    assert parse_color_spec(color_input) == expected


@pytest.mark.parametrize('invalid_input', [
    'not_a_color',
    '#zzzzzz',
    (300, 0, 0),
    'cyan,',
    [],
])
def test_parse_color_spec_invalid(invalid_input) -> None:
    with pytest.raises(InvalidColorError):
        parse_color_spec(invalid_input)


@pytest.mark.parametrize(
    ('stops', 'multiplier', 'expected_ansi'),
    [
        (TWO_STOPS, 0.5, '\033[38;2;50;100;125m'),
        (TWO_STOPS, 1.5, '\033[38;2;100;200;250m'),
        (TWO_STOPS, -0.5, '\033[38;2;0;0;0m'),
        (THREE_STOPS, 0.0, '\033[38;2;0;0;0m'),
        (THREE_STOPS, 0.25, '\033[38;2;50;50;50m'),
        (THREE_STOPS, 0.5, '\033[38;2;100;100;100m'),
        (THREE_STOPS, 0.75, '\033[38;2;150;150;150m'),
        (THREE_STOPS, 1.0, '\033[38;2;200;200;200m'),
    ],
)
def test_interpolate_ansi_color(stops, multiplier, expected_ansi) -> None:
    assert interpolate_ansi_color(stops, multiplier) == expected_ansi


@pytest.mark.parametrize(
    ('color_index', 'expected_ansi'),
    [
        (0.0, '\033[38;2;10;0;0m'),
        (0.5, '\033[38;2;15;0;0m'),
        (1.0, '\033[38;2;20;0;0m'),
        (1.5, '\033[38;2;25;0;0m'),
        (2.0, '\033[38;2;30;0;0m'),
        (2.5, '\033[38;2;20;0;0m'),
        (3.0, '\033[38;2;10;0;0m'),
    ],
)
def test_interpolate_indexed_ansi_color(color_index, expected_ansi) -> None:
    stops = ((10, 0, 0), (20, 0, 0), (30, 0, 0))
    assert interpolate_indexed_ansi_color(stops, color_index) == expected_ansi
