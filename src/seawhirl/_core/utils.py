import importlib.resources
import json
from typing import Any

import regex
from wcwidth import wcswidth

__all__ = ['get_visual_width', 'load_json_data']


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


def load_json_data(filename: str) -> dict[str, Any]:
    """Load JSON data from the _core/data directory."""
    pkg_files = importlib.resources.files(__package__.split('.')[0])
    resource = pkg_files.joinpath('_core', 'data', filename)
    return json.loads(resource.read_text(encoding='utf-8'))
