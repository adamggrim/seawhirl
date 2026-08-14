import asyncio
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, TextIO

from seawhirl._worker import run_spinner, RenderEngine
from seawhirl.easing import EasingStrategy


class SpinnerBackend(ABC):
    """Abstract interface for all rendering backends."""

    def __init__(
        self, stream: TextIO,
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
                self.stream,
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
        engine = RenderEngine(
            self.accel_secs,
            self.initial_fps,
            self.peak_animation_fps,
            self.frames,
            self.easing,
            self.status_state,
            self.status_frames,
            self.status_fps
        )

        try:
            while True:
                now = time.time()
                rendered_frame = engine.tick(now)

                if rendered_frame is not None:
                    self.stream.write(f'\r\033[K{rendered_frame}')
                    self.stream.flush()

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
