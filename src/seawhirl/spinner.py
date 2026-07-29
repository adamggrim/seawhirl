import asyncio
import inspect
import sys
from enum import Enum
from functools import wraps
from typing import Callable, Any

from seawhirl.utils import is_supported_terminal, enable_windows_vt_processing
from seawhirl.constants import SpinnerDefaults, PRESETS
from seawhirl._backends import SubprocessBackend, ThreadBackend, AsyncBackend

class Backend(Enum):
    SUBPROCESS = 'subprocess'
    THREAD = 'thread'
    ASYNC = 'async'

__all__ = ['Spinner', 'run_with_spinner', 'Backend']

class Spinner:
    def __init__(
        self,
        accel_secs: float = SpinnerDefaults.ACCEL_SECS,
        initial_fps: float = SpinnerDefaults.INITIAL_FPS,
        peak_animation_fps: float = SpinnerDefaults.PEAK_ANIMATION_FPS,
        max_render_fps: float = SpinnerDefaults.MAX_RENDER_FPS,
        frames: list[str] | str | None = None,
        stream: Any | None = None,
        backend: Backend = Backend.SUBPROCESS
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

        loop_delay = 1.0 / max_render_fps
        if self.backend == Backend.SUBPROCESS:
            self._worker = SubprocessBackend(
                self.stream,
                accel_secs,
                initial_fps,
                peak_animation_fps,
                loop_delay,
                self.frames
            )
        elif self.backend == Backend.THREAD:
            self._worker = ThreadBackend(
                self.stream,
                accel_secs,
                initial_fps,
                peak_animation_fps,
                loop_delay,
                self.frames
            )
        elif self.backend == Backend.ASYNC:
            self._worker = AsyncBackend(
                self.stream,
                accel_secs,
                initial_fps,
                peak_animation_fps,
                loop_delay,
                self.frames
            )

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

    def start(self) -> None:
        if self._disabled:
            return
        self._hide_cursor()
        self._worker.start()

    def stop(self) -> None:
        if self._disabled:
            return
        self._worker.stop()
        self._show_cursor()

    async def __aenter__(self):
        if not self._disabled:
            self._hide_cursor()
            await self._worker.astart()
        return self

    async def __aexit__(self, *_):
        if not self._disabled:
            await self._worker.astop()
            self._show_cursor()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()

    def __call__(self, func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with self:
                    return await func(*args, **kwargs)
            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return sync_wrapper

    def run(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        with self:
            return func(*args, **kwargs)


def run_with_spinner(func: Callable, *args: Any, **kwargs: Any) -> Any:
    spinner = Spinner()
    return spinner.run(func, *args, **kwargs)
