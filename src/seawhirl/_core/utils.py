import regex
from wcwidth import wcswidth

__all__ = ['get_visual_width', 'iter_grapheme_widths']


def iter_grapheme_widths(text: str) -> list[tuple[str, int]]:
    """Return (grapheme, visual_width) pairs for a string."""
    return [
        (g, 2 if (w := wcswidth(g)) < 0 else w)
        for g in regex.findall(r'\X', text)
    ]


def get_visual_width(text: str) -> int:
    """Calculates the visual width of a string in the terminal."""
    return sum(w for _, w in iter_grapheme_widths(text))
