import atexit
import inspect
import sys
from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import TextIO, TypeVar, ParamSpec, cast

from seawhirl._core.terminal import (
    StreamProxy,
    is_supported_terminal,
    enable_windows_vt_processing,
    ANSI_SHOW_CURSOR,
    ANSI_HIDE_CURSOR
)
from seawhirl._core.presets import PRESETS
from seawhirl._core.backends import ThreadBackend, AsyncBackend
from seawhirl._core.easing import EasingStrategy, Logarithmic
from seawhirl._core.exceptions import InvalidPresetError


class Backend(Enum):
    THREAD = 'thread'
    ASYNC = 'async'


class SpinnerDefaults:
    ACCEL_SECS: float = 3.0
    INITIAL_FPS: float = 6.0
    MAX_RENDER_FPS: float = 60.0
    PEAK_ANIMATION_FPS: float = 120.0
    PRESET: str = 'whirl'
    STATUS_FPS: float = 2.0
    STATUS_FRAMES: list[str] = []


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
                raise InvalidPresetError(
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
        }
        self._original_stdout: TextIO | None = None

        self.status_frames = (
            status_frames
            if status_frames is not None
            else SpinnerDefaults.STATUS_FRAMES
        )
        self.status_fps = status_fps

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

    def _restore_stdout_proxy(self) -> None:
        if self._original_stdout is not None:
            sys.stdout = self._original_stdout
            self._original_stdout = None

    def _show_cursor(self) -> None:
        if not self._disabled:
            try:
                self.stream.write(ANSI_SHOW_CURSOR)
                self.stream.flush()
            except (OSError, ValueError):
                pass

    def _hide_cursor(self) -> None:
        if not self._disabled:
            try:
                self.stream.write(ANSI_HIDE_CURSOR)
                self.stream.flush()
            except (OSError, ValueError):
                pass

    def start(self) -> None:
        if self._disabled:
            return
        self._hide_cursor()
        atexit.register(self._show_cursor)
        self._apply_stdout_proxy()
        self._worker.start()

    def stop(self) -> None:
        if self._disabled:
            return
        try:
            self._worker.stop()
        finally:
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
            await self._worker.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self._disabled:
            try:
                await self._worker.__aexit__(exc_type, exc_val, exc_tb)
            finally:
                self._restore_stdout_proxy()
                self._show_cursor()
                atexit.unregister(self._show_cursor)

    def __enter__(self):
        if not self._disabled:
            self._hide_cursor()
            atexit.register(self._show_cursor)
            self._apply_stdout_proxy()
            self._worker.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self._disabled:
            try:
                self._worker.__exit__(exc_type, exc_val, exc_tb)
            finally:
                self._restore_stdout_proxy()
                self._show_cursor()
                atexit.unregister(self._show_cursor)

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
