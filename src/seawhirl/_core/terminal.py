import atexit
import os
import platform
import signal
import sys
import threading
from typing import TextIO

ANSI_HIDE_CURSOR = '\033[?25l'
ANSI_SHOW_CURSOR = '\033[?25h'
ANSI_CLEAR_LINE = '\033[K'
ANSI_CARRIAGE_RETURN = '\r'
ANSI_MOVE_COLUMN = '\033[{col}G'

ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
FATAL_SIGNAL_BASE = 128
STD_OUTPUT_HANDLE = -11

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


class TerminalLifecycle:
    """
    Context manager isolating all terminal mutations and signal hooks.
    """
    def __init__(
        self, stream: TextIO,
        disabled: bool,
        handle_signals: bool = True
    ):
        self.stream = stream
        self.disabled = disabled
        self.handle_signals = handle_signals
        self._original_stdout = None
        self._sigint_handler = None
        self._sigterm_handler = None

    def __enter__(self):
        if not self.disabled:
            self._hide_cursor()
            if self.handle_signals:
                self._register_signal_handlers()
            self._apply_stdout_proxy()
            atexit.register(self._cleanup)
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        if not self.disabled:
            self._cleanup()
            atexit.unregister(self._cleanup)

    def _hide_cursor(self) -> None:
        self.stream.write(ANSI_HIDE_CURSOR)
        self.stream.flush()

    def _show_cursor(self) -> None:
        self.stream.write(ANSI_SHOW_CURSOR)
        self.stream.flush()

    def _apply_stdout_proxy(self) -> None:
        if isinstance(sys.stdout, StreamProxy):
            self._original_stdout = None
        else:
            self._original_stdout = sys.stdout
            sys.stdout = StreamProxy(sys.stdout)

    def _register_signal_handlers(self) -> None:
        try:
            self._sigint_handler = signal.getsignal(signal.SIGINT)
            self._sigterm_handler = signal.getsignal(signal.SIGTERM)

            if self._sigint_handler == signal.SIG_DFL:
                signal.signal(signal.SIGINT, self._handle_signal)
            if self._sigterm_handler == signal.SIG_DFL:
                signal.signal(signal.SIGTERM, self._handle_signal)
        except ValueError:
            pass

    def _handle_signal(self, signum, frame) -> None:
        self._cleanup()

        original_handler = (
            self._sigint_handler
            if signum == signal.SIGINT
            else self._sigterm_handler
        )

        if callable(original_handler):
            original_handler(signum, frame)
        elif original_handler == signal.SIG_DFL:
            sys.exit(FATAL_SIGNAL_BASE + signum)

    def _cleanup(self) -> None:
        self._show_cursor()
        if self._original_stdout is not None:
            sys.stdout = self._original_stdout
        try:
            if self._sigint_handler is not None:
                signal.signal(signal.SIGINT, self._sigint_handler)
            if self._sigterm_handler is not None:
                signal.signal(signal.SIGTERM, self._sigterm_handler)
        except ValueError:
            pass


def enable_windows_vt_processing() -> None:
    if platform.system() == 'Windows':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        mode = ctypes.c_uint32()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(
            handle,
            mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        )


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
