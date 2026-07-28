import asyncio
import json
import subprocess
import sys
import threading
from enum import Enum
from typing import Callable, Any

from .utils import is_supported_terminal
from ._worker import run_spinner, _calculate_current_fps

PRESETS: dict[str, list[str]] = {
    'braille': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
    'dots': ['.  ', '.. ', '...', '   '],
    'line': ['-', '\\', '|', '/'],
    'arc': ['◜', '◠', '◝', '◞', '◡', '◟'],
    'bounce': ['⠁', '⠂', '⠄', '⠂']
}


class Backend(Enum):
    SUBPROCESS = 'subprocess'
    THREAD = 'thread'
    ASYNC = 'async'


__all__ = ['Spinner', 'run_with_spinner', 'PRESETS', 'Backend']


class Spinner:
    def __init__(
        self,
        accel_secs: float = 3.0,
        initial_fps: float = 6.0,
        peak_animation_fps: float = 120.0,
        max_render_fps: float = 60.0,
        frames: list[str] | str | None = None,
        stream: Any | None = None,
        backend: Backend = Backend.SUBPROCESS
    ) -> None:
        self.accel_secs = accel_secs
        self.initial_fps = initial_fps
        self.peak_animation_fps = peak_animation_fps
        self.loop_delay = 1.0 / max_render_fps
        self.stream = stream or sys.stdout

        if isinstance(frames, str):
            if frames not in PRESETS:
                raise ValueError(
                    f"Unknown preset: '{frames}'. "
                    f'Available presets: {list(PRESETS.keys())}'
                )
            self.frames = PRESETS[frames]
        else:
            self.frames = frames or PRESETS['braille']

        self._disabled = not is_supported_terminal(self.stream)
        self.backend = backend
        self._process: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._async_task: asyncio.Task | None = None

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

        if self.backend == Backend.SUBPROCESS:
            # Spawn the isolated worker script.
            self._process = subprocess.Popen(
                [
                    sys.executable, '-m', 'seawhirl._worker',
                    '--accel', str(self.accel_secs),
                    '--initial', str(self.initial_fps),
                    '--peak', str(self.peak_animation_fps),
                    '--delay', str(self.loop_delay),
                    '--frames', json.dumps(self.frames)
                ],
                stdout=self.stream,
                stderr=subprocess.DEVNULL
            )
        elif self.backend == Backend.THREAD:
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=run_spinner,
                args=(
                    self.accel_secs,
                    self.initial_fps,
                    self.peak_animation_fps,
                    self.loop_delay,
                    self.frames,
                    self._stop_event
                ),
                daemon=True
            )
            self._thread.start()

    def stop(self) -> None:
        if self._disabled:
            return

        if self.backend == Backend.SUBPROCESS and self._process is not None:
            self._process.terminate()
            self._process.wait()
            self._process = None
        elif self.backend == Backend.THREAD and self._thread is not None:
            self._stop_event.set()
            self._thread.join()
            self._thread = None

        self._show_cursor()

    async def _async_render_loop(self) -> None:
        import random
        import time

        num_frames = len(self.frames)
        current_frame = float(random.randint(0, num_frames - 1))
        last_rendered_idx = -1
        last_rendered_len = 0
        start_time = last_update_time = time.time()

        try:
            while True:
                now = time.time()
                elapsed_total = now - start_time
                elapsed_since_last = now - last_update_time
                last_update_time = now

                current_fps = _calculate_current_fps(
                    elapsed_total, self.accel_secs, self.initial_fps, self.peak_animation_fps
                )

                current_frame += current_fps * elapsed_since_last
                current_frame_idx = int(current_frame) % num_frames

                if current_frame_idx != last_rendered_idx:
                    char = self.frames[current_frame_idx]

                    if last_rendered_idx == -1:
                        self.stream.write(char)
                    else:
                        backspaces = '\b' * last_rendered_len
                        padding_spaces = ' ' * max(0, last_rendered_len - len(char))
                        back_padding = '\b' * len(padding_spaces)
                        self.stream.write(
                            f'{backspaces}{char}{padding_spaces}{back_padding}'
                        )

                    self.stream.flush()
                    last_rendered_idx = current_frame_idx
                    last_rendered_len = len(char)

                await asyncio.sleep(self.loop_delay)
        except asyncio.CancelledError:
            pass
        finally:
            self.stream.write('\r\033[K')
            self.stream.flush()

    async def __aenter__(self):
        if self.backend == Backend.ASYNC:
            if not self._disabled:
                self._hide_cursor()
                self._async_task = asyncio.create_task(self._async_render_loop())
        else:
            self.start()
        return self

    async def __aexit__(self, *_):
        if self.backend == Backend.ASYNC:
            if self._async_task:
                self._async_task.cancel()
                try:
                    await self._async_task
                except asyncio.CancelledError:
                    pass
                self._async_task = None
            self._show_cursor()
        else:
            self.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper

    def run(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        with self:
            return func(*args, **kwargs)


def run_with_spinner(func: Callable, *args: Any, **kwargs: Any) -> Any:
    spinner = Spinner()
    return spinner.run(func, *args, **kwargs)
