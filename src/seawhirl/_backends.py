import asyncio
import json
import random
import subprocess
import sys
import threading
import time
from abc import ABC, abstractmethod
from typing import Any

from wcwidth import wcswidth

from seawhirl._worker import run_spinner, _calculate_current_fps


class SpinnerBackend(ABC):
    """Abstract interface for all rendering backends."""

    def __init__(
        self,
        stream: Any,
        accel_secs: float,
        initial_fps: float,
        peak_animation_fps: float,
        loop_delay: float,
        frames: list[str]
    ) -> None:
        self.stream = stream
        self.accel_secs = accel_secs
        self.initial_fps = initial_fps
        self.peak_animation_fps = peak_animation_fps
        self.loop_delay = loop_delay
        self.frames = frames

    @abstractmethod
    def start(self) -> None:
        """Start the synchronous rendering loop."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the synchronous rendering loop."""
        pass

    async def astart(self) -> None:
        """
        Start the asynchronous rendering loop. Defaults to sync start.
        """
        self.start()

    async def astop(self) -> None:
        """
        Stop the asynchronous rendering loop. Defaults to sync stop.
        """
        self.stop()


class SubprocessBackend(SpinnerBackend):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._process: subprocess.Popen | None = None

    def start(self) -> None:
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

    def stop(self) -> None:
        if self._process is not None:
            self._process.terminate()
            self._process.wait()
            self._process = None


class ThreadBackend(SpinnerBackend):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
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
        if self._thread is not None:
            self._stop_event.set()
            self._thread.join()
            self._thread = None


class AsyncBackend(SpinnerBackend):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._async_task: asyncio.Task | None = None

    def start(self) -> None:
        raise RuntimeError(
            "`AsyncBackend` cannot start synchronously. Please use 'aync with'"
            'or decorate an async function.'
        )

    def stop(self) -> None:
        pass

    async def _async_render_loop(self) -> None:
        num_frames = len(self.frames)
        current_frame = float(random.randint(0, num_frames - 1))
        prev_rendered_idx = -1
        prev_rendered_len = 0
        start_time = prev_update_time = time.time()

        try:
            while True:
                now = time.time()
                elapsed_total = now - start_time
                elapsed_since_last = now - prev_update_time
                prev_update_time = now

                current_fps = _calculate_current_fps(
                    elapsed_total,
                    self.accel_secs,
                    self.initial_fps,
                    self.peak_animation_fps
                )

                current_frame += current_fps * elapsed_since_last
                current_frame_idx = int(current_frame) % num_frames

                if current_frame_idx != prev_rendered_idx:
                    char = self.frames[current_frame_idx]
                    char_width = max(0, wcswidth(char))

                    if prev_rendered_idx == -1:
                        self.stream.write(char)
                    else:
                        backspaces = '\b' * prev_rendered_len
                        padding_spaces = ' ' * max(
                            0, prev_rendered_len - char_width
                        )
                        back_padding = '\b' * len(padding_spaces)
                        self.stream.write(
                            f'{backspaces}{char}{padding_spaces}{back_padding}'
                        )

                    self.stream.flush()
                    prev_rendered_idx = current_frame_idx
                    prev_rendered_len = char_width

                await asyncio.sleep(self.loop_delay)
        except asyncio.CancelledError:
            pass
        finally:
            self.stream.write('\r\033[K')
            self.stream.flush()

    async def astart(self) -> None:
        self._async_task = asyncio.create_task(self._async_render_loop())

    async def astop(self) -> None:
        if self._async_task:
            self._async_task.cancel()
            try:
                await self._async_task
            except asyncio.CancelledError:
                pass
            self._async_task = None
