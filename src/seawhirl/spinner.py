import atexit
import inspect
import shutil
import signal
import sys
import threading
import types
from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import Any, TextIO, TypeVar, ParamSpec, cast

from seawhirl.utils import (
    is_supported_terminal,
    enable_windows_vt_processing,
    StreamProxy
)
from seawhirl.constants import SpinnerDefaults, PRESETS
from seawhirl._backends import ThreadBackend, AsyncBackend
from seawhirl.easing import EasingStrategy, Logarithmic


class Backend(Enum):
    THREAD = 'thread'
    ASYNC = 'async'


__all__ = ['Spinner', 'Backend']

P = ParamSpec('P')
T = TypeVar('T')


class Spinner:
    def __init__(
        self,
        accel_secs: float = SpinnerDefaults.ACCEL_SECS,
        initial_fps: float = SpinnerDefaults.INITIAL_FPS,
        peak_animation_fps: float = SpinnerDefaults.PEAK_ANIMATION_FPS,
        peak_render_fps: float = SpinnerDefaults.MAX_RENDER_FPS,
        frames: list[str] | str | None = None,
        stream: TextIO | None = None,
        backend: Backend = Backend.THREAD,
        easing: EasingStrategy | None = None,
        status_text: str = '',
        status_frames: list[str] | None = None,
        status_fps: float = SpinnerDefaults.STATUS_FPS,
        oscillation: bool = False
    ) -> None:
        self.stream = stream or sys.stdout

        if isinstance(frames, str):
            if frames not in PRESETS:
                raise ValueError(
                    f"Unknown preset: '{frames}'. "
                    f'Available presets: {list(PRESETS.keys())}'
                )
            self.frames = PRESETS[frames]
        else:
            self.frames = frames or PRESETS[SpinnerDefaults.PRESET]

        self._disabled = not is_supported_terminal(self.stream)
        if not self._disabled:
            enable_windows_vt_processing()

        self.backend = backend
        self.easing = easing or Logarithmic()
        loop_delay = 1.0 / peak_render_fps

        self._state = {
            'status_text': status_text,
            'console_width': max(
                10, shutil.get_terminal_size().columns - 1
            )
        }
        self._old_sigwinch = None
        self.status_frames = (
            status_frames
            if status_frames is not None
            else SpinnerDefaults.STATUS_FRAMES
        )
        self.status_fps = status_fps
        self._original_stdout: TextIO | None = None

        if self.backend == Backend.THREAD:
            self._worker = ThreadBackend(
                self.stream,
                accel_secs,
                initial_fps,
                peak_animation_fps,
                loop_delay,
                self.frames,
                self.easing,
                self._state,
                self.status_frames,
                self.status_fps,
                oscillation
            )
        elif self.backend == Backend.ASYNC:
            self._worker = AsyncBackend(
                self.stream,
                accel_secs,
                initial_fps,
                peak_animation_fps,
                loop_delay,
                self.frames,
                self.easing,
                self._state,
                self.status_frames,
                self.status_fps,
                oscillation
            )

    def _apply_stdout_proxy(self) -> None:
        if self.stream == sys.stdout:
            self._original_stdout = sys.stdout
            sys.stdout = cast(TextIO, StreamProxy(sys.stdout))

    def _show_cursor(self) -> None:
        if not self._disabled:
            try:
                self.stream.write('\033[?25h')
                self.stream.flush()
            except (OSError, ValueError):
                pass

    def _hide_cursor(self) -> None:
        if not self._disabled:
            try:
                self.stream.write('\033[?25l')
                self.stream.flush()
            except (OSError, ValueError):
                pass

    def _on_resize(self, signum: int, frame: types.FrameType | None) -> None:
        self._state['console_width'] = max(
            10, shutil.get_terminal_size().columns - 1
        )
        if callable(self._old_sigwinch):
            self._old_sigwinch(signum, frame)

    def _register_resize_handler(self) -> None:
        self._old_sigwinch = None
        if (
            hasattr(signal, 'SIGWINCH')
            and threading.current_thread() is threading.main_thread()
        ):
            try:
                self._old_sigwinch = signal.getsignal(signal.SIGWINCH)
                signal.signal(signal.SIGWINCH, self._on_resize)
            except (ValueError, OSError):
                pass

    def _restore_resize_handler(self) -> None:
        if (
            hasattr(signal, 'SIGWINCH')
            and threading.current_thread() is threading.main_thread()
        ):
            try:
                if self._old_sigwinch is not None:
                    signal.signal(signal.SIGWINCH, self._old_sigwinch)
            except (ValueError, OSError):
                pass

    def _restore_stdout_proxy(self) -> None:
        if self._original_stdout is not None:
            sys.stdout = self._original_stdout
            self._original_stdout = None

    def start(self) -> None:
        if self._disabled:
            return
        self._hide_cursor()
        atexit.register(self._show_cursor)
        self._apply_stdout_proxy()
        self._register_resize_handler()
        self._worker.start()

    def stop(self) -> None:
        if self._disabled:
            return
        self._worker.stop()
        self._restore_resize_handler()
        self._restore_stdout_proxy()
        self._show_cursor()
        atexit.unregister(self._show_cursor)

    def update(self, status_text: str) -> None:
        """
        Dynamically update the status text while the spinner is running.
        """
        self._state['status_text'] = status_text

    async def __aenter__(self):
        if not self._disabled:
            self._hide_cursor()
            atexit.register(self._show_cursor)
            self._apply_stdout_proxy()
            self._register_resize_handler()
            await self._worker.astart()
        return self

    async def __aexit__(self, *_):
        if not self._disabled:
            await self._worker.astop()
            self._restore_resize_handler()
            self._restore_stdout_proxy()
            self._show_cursor()
            atexit.unregister(self._show_cursor)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()

    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                async with self:
                    return await func(*args, **kwargs)
            return cast(Callable[P, T], async_wrapper)

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            with self:
                return func(*args, **kwargs)
        return cast(Callable[P, T], sync_wrapper)
