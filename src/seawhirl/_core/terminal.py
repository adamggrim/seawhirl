import os
import platform
import threading
from typing import TextIO

ANSI_HIDE_CURSOR = '\033[?25l'
ANSI_SHOW_CURSOR = '\033[?25h'
ANSI_CLEAR_LINE = '\033[K'
ANSI_CARRIAGE_RETURN = '\r'
ANSI_MOVE_COLUMN = '\033[{col}G'


class StreamProxy:
    """
    Class for intercepting `print()` calls to prevent visual tearing.
    """
    def __init__(self, original_stream: TextIO) -> None:
        self._original_stream = original_stream
        self._is_new_line = True
        self._lock = threading.Lock()

    def write(self, data: str) -> int:
        with self._lock:
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
        with self._lock:
            self._original_stream.flush()

    def isatty(self) -> bool:
        return self._original_stream.isatty()

    def fileno(self) -> int:
        return self._original_stream.fileno()


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
