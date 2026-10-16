from unittest.mock import patch

import pytest

from seawhirl._core.utils import get_visual_width, iter_grapheme_widths


@pytest.mark.parametrize('text, expected', [
    ('', 0),
    ('Oread', 5),
    ('岩石', 4),
    ('vortex 漩渦', 11),
    ('  ', 2),
])
def test_get_visual_width_standard_text(text: str, expected: int) -> None:
    assert get_visual_width(text) == expected


def test_get_visual_width_complex_graphemes() -> None:
    family_emoji = '👨‍👩‍👧‍👦'

    assert get_visual_width(family_emoji) == 2


def test_iter_grapheme_widths() -> None:
    result = iter_grapheme_widths('A👨‍👩‍👧‍👦岩')

    assert result == [('A', 1), ('👨‍👩‍👧‍👦', 2), ('岩', 2)]


@pytest.mark.parametrize(('text', 'widths', 'expected'), [
    ('HD', [-1, -1], 4),
    ('EP', [1, -1], 3),
])
@patch('seawhirl._core.utils.wcswidth')
def test_get_visual_width_fallbacks(
    mock_wcswidth,
    text: str,
    widths: list[int],
    expected: int
) -> None:
    mock_wcswidth.side_effect = widths
    assert get_visual_width(text) == expected
