import regex
from wcwidth import wcswidth

__all__ = ['get_visual_width']


def get_visual_width(text: str) -> int:
    """
    Calculates the visual width of a string in the terminal, applying
    overrides for compound emojis that wcswidth miscalculates.
    """
    if not text:
        return 0

    total_width = 0

    for grapheme in regex.findall(r'\X', text):
        w = wcswidth(grapheme)
        if w < 0:
            total_width += 2
        else:
            total_width += w

    return total_width
