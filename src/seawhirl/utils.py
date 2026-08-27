import os
import platform
import re
from typing import Any, TextIO

from wcwidth import wcswidth

__all__ = [
    'COMPLEX_EMOJI_PATTERN',
    'StreamProxy',
    'enable_windows_vt_processing',
    'get_visual_width',
    'is_supported_terminal',
]

# Matches Unicode sequences for complex emoji presentation.
COMPLEX_EMOJI_PATTERN = re.compile(
    r"""
    (                                       # Start of capturing group.
        [\U0001F1E6-\U0001F1FF]{2}          # Regional indicators (country
                                            # flags, e.g., 🇺🇸).
        |                                   # OR
        [#*0-9]\uFE0F?\u20E3                # Keycap sequences (e.g., 1️⃣,
                                            # #️⃣).
        |                                   # OR
        (?:                                 # Start of non-capturing group for
                                            # ZWJ sequences.
            .                               # Match any character (typically a
                                            # base emoji).
            [\U0001F3FB-\U0001F3FF\uFE0F]?  # Match an optional skin tone
                                            # modifier or other variation.
            \u200D                          # Match a zero width joiner (ZWJ).
        )+                                  # Repeat one or more times.
        .                                   # Match the final base character
                                            # in the sequence.
        [\U0001F3FB-\U0001F3FF\uFE0F]?      # Match an optional final skin tone
                                            # modifier or other variation.
        |                                   # OR
        .[\U0001F3FB-\U0001F3FF]\uFE0F?     # Individual characters with a skin
                                            # tone modifier (e.g., 👍🏿).
        |                                   # OR
        .\uFE0F                             # Text symbols styled as emojis via
                                            # Variation Selector-16 (VS-16,
                                            # e.g., ❤️).
        |                                   # OR
        (?:                                 # Start of non-capturing group for
                                            # pictographic blocks.
            [\U0001F300-\U0001F64F]         # Standalone emojis in pictographic
            |                               # blocks (e.g., 🚀).
            [\U0001F680-\U0001F6FF]
            |
            [\U0001F900-\U0001F9FF]
            |
            [\U0001FA70-\U0001FAFF]
        )                                   # End of non-capturing group.
    )                                       # End of capturing group.
    """,
    re.VERBOSE
)


class StreamProxy:
    """
    Class for intercepting `print()` calls to prevent visual tearing.
    """
    def __init__(self, original_stream: TextIO) -> None:
        self._original_stream = original_stream
        self._is_new_line = True

    def write(self, data: str) -> int:
        if data == '\n':
            self._original_stream.write(data)
            self._is_new_line = True
        else:
            if self._is_new_line:
                self._original_stream.write(f'\r\033[K{data}')
                self._is_new_line = False
            else:
                self._original_stream.write(data)
        return len(data)

    def flush(self) -> None:
        self._original_stream.flush()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._original_stream, name)


def enable_windows_vt_processing() -> None:
    if platform.system() == 'Windows':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)


def is_supported_terminal(stream: Any) -> bool:
    if (
        os.environ.get('CI')
        or os.environ.get('NO_COLOR')
        or os.environ.get('TERM') == 'dumb'
    ):
        return False

    is_tty = hasattr(stream, 'isatty') and stream.isatty()
    is_utf8 = getattr(stream, 'encoding', '').lower() in ('utf-8', 'utf8')
    return is_tty and is_utf8


def get_visual_width(text: str) -> int:
    """
    Calculates the visual width of a string in the terminal, applying
    overrides for compound emojis that wcswidth miscalculates.
    """
    if not text:
        return 0

    if not COMPLEX_EMOJI_PATTERN.search(text):
        return max(0, wcswidth(text))

    total_width = 0

    for token in COMPLEX_EMOJI_PATTERN.split(text):
        if not token:
            continue

        if COMPLEX_EMOJI_PATTERN.fullmatch(token):
            total_width += 2
        else:
            total_width += max(0, wcswidth(token))

    return total_width
