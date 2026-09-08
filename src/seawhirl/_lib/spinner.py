"""Main spinner interface and configuration defaults."""

import inspect
import sys
import types
from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import TextIO, TypeVar, ParamSpec, cast

from seawhirl._core.config import SpinnerConfig
from seawhirl._core.terminal import (
    TerminalLifecycle,
    enable_windows_vt_processing,
    is_supported_terminal
)
from seawhirl._core.presets import PRESETS
from seawhirl._core.backends import (
    AsyncBackend,
    SpinnerBackend,
    ThreadBackend
)
from seawhirl._core.easing import EasingStrategy, Logarithmic
from seawhirl._core.exceptions import InvalidPresetError
from seawhirl._core.state import SpinnerState


class Backend(Enum):
    """Execution modes for background rendering."""
    THREAD = 'thread'
    ASYNC = 'async'


class SpinnerDefaults:
    """Fallback physics and framing configuration constants."""
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
    """
    Entry point for creating terminal spinners.

    Acts as a decorator, context manager or manual controller.
    """
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
        oscillation: bool = False,
        handle_signals: bool = True
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

        self.state = SpinnerState(status_text=status_text)
        self.lifecycle = TerminalLifecycle(self.stream, self._disabled, handle_signals)

        self.status_frames = (
            status_frames
            if status_frames is not None
            else SpinnerDefaults.STATUS_FRAMES
        )
        self.status_fps = status_fps

        self.config = SpinnerConfig(
            accel_secs=accel_secs,
            initial_fps=initial_fps,
            peak_animation_fps=peak_animation_fps,
            loop_delay=loop_delay,
            frames=self.frames,
            easing=self.easing,
            status_frames=self.status_frames,
            status_fps=self.status_fps,
            oscillation=oscillation
        )

        self._worker: SpinnerBackend
        if self.backend == Backend.THREAD:
            self._worker = ThreadBackend(self.stream, self.config, self.state)
        elif self.backend == Backend.ASYNC:
            self._worker = AsyncBackend(self.stream, self.config, self.state)

    def start(self) -> None:
        """Manually start the animation."""
        self.lifecycle.__enter__()
        if not self._disabled:
            self._worker.start()

    def stop(self) -> None:
        """Manually stop the animation and restore terminal state."""
        try:
            if not self._disabled:
                self._worker.stop()
        finally:
            self.lifecycle.__exit__(None, None, None)

    def update(self, status_text: str) -> None:
        """
        Rewrite the status text next to the spinner.
        """
        self.state.status_text = status_text

    async def __aenter__(self) -> 'Spinner':
        self.lifecycle.__enter__()
        if not self._disabled:
            await self._worker.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None
    ) -> None:
        try:
            if not self._disabled:
                await self._worker.__aexit__(exc_type, exc_val, exc_tb)
        finally:
            self.lifecycle.__exit__(exc_type, exc_val, exc_tb)

    def __enter__(self) -> 'Spinner':
        self.lifecycle.__enter__()
        if not self._disabled:
            self._worker.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None
    ) -> None:
        try:
            if not self._disabled:
                self._worker.__exit__(exc_type, exc_val, exc_tb)
        finally:
            self.lifecycle.__exit__(exc_type, exc_val, exc_tb)

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
