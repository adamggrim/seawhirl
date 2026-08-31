import os
import platform
import regex
from typing import Any, TextIO

from seawhirl.constants import ANSI_CARRIAGE_RETURN, ANSI_CLEAR_LINE
from wcwidth import wcswidth

__all__ = [
    'StreamProxy',
    'enable_windows_vt_processing',
    'get_visual_width',
    'is_supported_terminal',
]

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
                self._original_stream.write(
                    f'{ANSI_CARRIAGE_RETURN}{ANSI_CLEAR_LINE}{data}'
                )
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


def is_supported_terminal(stream: TextIO) -> bool:
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

    total_width = 0

    for grapheme in regex.findall(r'\X', text):
        w = wcswidth(grapheme)
        if w < 0:
            total_width += 2
        else:
            total_width += w

    return total_width
