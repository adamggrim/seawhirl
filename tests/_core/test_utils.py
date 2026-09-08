from unittest.mock import patch

import pytest

from seawhirl._core.utils import get_visual_width


@pytest.mark.parametrize('text, expected', [
    ('', 0),
    ('pines', 5),
    ('岩石', 4),
    ('green 綠色的', 12),
    ('  ', 2),
])
def test_get_visual_width_standard_text(text: str, expected: int) -> None:
    assert get_visual_width(text) == expected


def test_get_visual_width_complex_graphemes() -> None:
    family_emoji = '👨‍👩‍👧‍👦'

    assert get_visual_width(family_emoji) == 2


@patch('seawhirl._core.utils.wcswidth')
def test_get_visual_width_negative_fallback(mock_wcswidth) -> None:
    mock_wcswidth.return_value = -1
    assert get_visual_width('AB') == 4


@patch('seawhirl._core.utils.wcswidth')
def test_get_visual_width_mixed_fallback(mock_wcswidth) -> None:
    mock_wcswidth.side_effect = [1, -1]
    assert get_visual_width('AB') == 3
