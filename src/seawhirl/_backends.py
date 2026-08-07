import asyncio
import random
import shutil
import threading
import time
from abc import ABC, abstractmethod
from typing import Any

from wcwidth import wcswidth

from seawhirl._worker import run_spinner, _calculate_current_fps
from seawhirl.easing import EasingStrategy


class SpinnerBackend(ABC):
    """Abstract interface for all rendering backends."""

    def __init__(
        self, stream: Any,
        accel_secs: float,
        initial_fps: float,
        peak_animation_fps: float,
        loop_delay: float,
        frames: list[str],
        easing: EasingStrategy,
        status_state: dict[str, str],
        status_frames: list[str],
        status_fps: float
    ) -> None:
        self.stream = stream
        self.accel_secs = accel_secs
        self.initial_fps = initial_fps
        self.peak_animation_fps = peak_animation_fps
        self.loop_delay = loop_delay
        self.frames = frames
        self.easing = easing
        self.status_state = status_state
        self.status_frames = status_frames
        self.status_fps = status_fps

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
                self.easing,
                self._stop_event,
                self.status_state,
                self.status_frames,
                self.status_fps
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
        num_status_frames = (
            len(self.status_frames)
            if self.status_frames
            else 1
        )
        current_frame = float(random.randint(0, num_frames - 1))
        current_status_frame = 0.0
        prev_rendered_str = ''
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
                    self.peak_animation_fps,
                    self.easing
                )

                current_frame += current_fps * elapsed_since_last
                current_frame_idx = int(current_frame) % num_frames

                current_status_frame += self.status_fps * elapsed_since_last
                status_frame_idx = int(current_status_frame) % num_status_frames

                icon = self.frames[current_frame_idx]
                text = self.status_state.get('status_text', '')
                suffix = (
                    self.status_frames[status_frame_idx]
                    if text and self.status_frames
                    else ''
                )

                display_str = f'{icon} {text}{suffix}' if text else icon

                if display_str != prev_rendered_str:
                    console_width = max(10, shutil.get_terminal_size().columns - 1)

                    if wcswidth(display_str) > console_width:
                        display_str = display_str[:console_width - 2] + '…'

                    self.stream.write(f'\r\033[K{display_str}')
                    self.stream.flush()
                    prev_rendered_str = display_str

                work_time = time.time() - now
                await asyncio.sleep(max(0.0, self.loop_delay - work_time))
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
