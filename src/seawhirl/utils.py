import platform
import shutil
from typing import Any

from wcwidth import wcswidth


def enable_windows_vt_processing() -> None:
    if platform.system() == 'Windows':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)


def is_supported_terminal(stream: Any) -> bool:
    is_tty = hasattr(stream, 'isatty') and stream.isatty()

    is_utf8 = getattr(stream, 'encoding', '').lower() in ('utf-8', 'utf8')
    return is_tty and is_utf8
