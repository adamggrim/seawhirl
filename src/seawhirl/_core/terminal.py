from __future__ import annotations

import atexit
import os
import platform
import signal
import sys
import threading
import types
from typing import Any, TextIO

ANSI_HIDE_CURSOR = '\033[?25l'
ANSI_SHOW_CURSOR = '\033[?25h'
ANSI_CLEAR_LINE = '\033[K'
ANSI_CARRIAGE_RETURN = '\r'
ANSI_MOVE_COLUMN = '\033[{col}G'
ANSI_RESET_COLOR = '\033[0m'

ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
FATAL_SIGNAL_BASE = 128
STD_OUTPUT_HANDLE = -11

class StreamProxy:
    """
    Class for intercepting `print()` calls to prevent visual tearing.
    """
    def __init__(
        self,
        original_stream: TextIO,
        lock: threading.Lock | None = None
    ) -> None:
        self._original_stream = original_stream
        self._is_new_line = True
        self._lock = lock or threading.Lock()

    def write(self, data: str) -> int:
        if not data:
            return 0
        with self._lock:
            if self._is_new_line and data != '\n':
                self._original_stream.write(
                    f'{ANSI_CARRIAGE_RETURN}{ANSI_CLEAR_LINE}{data}'
                )
            else:
                self._original_stream.write(data)
            self._is_new_line = data.endswith('\n')
            return len(data)

    def flush(self) -> None:
        with self._lock:
            self._original_stream.flush()

    def isatty(self) -> bool:
        return self._original_stream.isatty()

    def fileno(self) -> int:
        return self._original_stream.fileno()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._original_stream, name)


class TerminalLifecycle:
    """
    Context manager isolating all terminal mutations and signal hooks.
    """
    def __init__(
        self,
        stream: TextIO,
        disabled: bool = False,
        handle_signals: bool = True,
        lock: threading.Lock | None = None
    ) -> None:
        self.stream = stream
        self.disabled = disabled
        self.handle_signals = handle_signals
        self.lock = lock or threading.Lock()
        self._original_stdout: TextIO | None = None
        self._original_signals: dict[signal.Signals, Any] = {}

    def __enter__(self) -> 'TerminalLifecycle':
        if not self.disabled:
            self._hide_cursor()
            if self.handle_signals:
                self._register_signal_handlers()
            self._apply_stdout_proxy()
            atexit.register(self._cleanup)
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: types.TracebackType | None
    ) -> None:
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
            sys.stdout = StreamProxy(sys.stdout, lock=self.lock)

    def _register_signal_handlers(self) -> None:
        default_handlers = (signal.SIG_DFL, signal.default_int_handler)
        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                orig = signal.getsignal(sig)
                self._original_signals[sig] = orig
                if orig in default_handlers:
                    signal.signal(sig, self._handle_signal)
        except ValueError:
            pass

    def _handle_signal(
        self,
        signum: int,
        frame: types.FrameType | None
    ) -> None:
        self._cleanup()
        original_handler = self._original_signals.get(signal.Signals(signum))

        if callable(original_handler):
            original_handler(signum, frame)
        elif original_handler == signal.SIG_DFL:
            sys.exit(FATAL_SIGNAL_BASE + signum)

    def _cleanup(self) -> None:
        self._show_cursor()
        if self._original_stdout is not None:
            sys.stdout = self._original_stdout
        try:
            for sig, handler in self._original_signals.items():
                signal.signal(sig, handler)
        except ValueError:
            pass


def enable_windows_vt_processing() -> None:
    if platform.system() == 'Windows':
        import ctypes
        kernel32 = getattr(ctypes, 'windll').kernel32
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
