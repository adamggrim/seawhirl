import asyncio
import time
import types
import threading
import sys
from abc import ABC, abstractmethod
from typing import TextIO

from seawhirl._core.easing import EasingStrategy
from seawhirl._core.engine import RenderEngine
from seawhirl._core.terminal import ANSI_CARRIAGE_RETURN, ANSI_CLEAR_LINE
from seawhirl._core.exceptions import BackendStartupError


class SpinnerBackend(ABC):
    """
    Abstract base class defining the contract for continuous rendering
    execution strategies.
    """
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
        status_fps: float,
        oscillation: bool = False
    ) -> None:
        self.stream = stream
        self.accel_secs = accel_secs
        self.initial_fps = initial_fps
        self.peak_animation_fps = peak_animation_fps
        self.loop_delay = loop_delay
        self.frames = frames
        self.easing = easing
        self.oscillation = oscillation
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

    def __enter__(self) -> 'SpinnerBackend':
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None
    ) -> None:
        self.stop()

    async def __aenter__(self) -> 'SpinnerBackend':
        await self.astart()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None
    ) -> None:
        await self.astop()


class ThreadBackend(SpinnerBackend):
    """
    Implementation that delegates rendering to a daemonized background
    thread. Standard print statements must be intercepted to prevent
    terminal tearing.
    """
    def __init__(
        self,
        stream: TextIO,
        accel_secs: float,
        initial_fps: float,
        peak_animation_fps: float,
        loop_delay: float,
        frames: list[str],
        easing: EasingStrategy,
        status_state: dict[str, str],
        status_frames: list[str],
        status_fps: float,
        oscillation: bool
    ) -> None:
        super().__init__(
            stream,
            accel_secs,
            initial_fps,
            peak_animation_fps,
            loop_delay,
            frames, easing,
            status_state,
            status_frames,
            status_fps,
            oscillation
        )
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def _sync_render_loop(self) -> None:
        """Internal synchronous polling loop mapping Engine state to IO."""
        engine = RenderEngine(
            self.accel_secs,
            self.initial_fps,
            self.peak_animation_fps,
            self.frames,
            self.easing,
            self.status_state,
            self.status_frames,
            self.status_fps,
            self.oscillation
        )

        try:
            next_tick = time.time()
            while not self._stop_event.is_set():
                now = time.time()
                rendered_frame = engine.tick(now)

                if rendered_frame is not None:
                    self.stream.write(
                        f'{ANSI_CARRIAGE_RETURN}{ANSI_CLEAR_LINE}'
                        f'{rendered_frame}'
                    )
                    self.stream.flush()

                next_tick += self.loop_delay
                time.sleep(max(0.0, next_tick - time.time()))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            sys.stderr.write(f'\nSpinner worker encountered an error: {e}\n')
            sys.stderr.flush()
        finally:
            self.stream.write(f'{ANSI_CARRIAGE_RETURN}{ANSI_CLEAR_LINE}')
            self.stream.flush()

    def start(self) -> None:
        """Initialize the thread loop safely."""
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._sync_render_loop,
            daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Issue shutdown signals to the running thread and join."""
        if self._thread is not None:
            self._stop_event.set()
            self._thread.join()
            self._thread = None


class AsyncBackend(SpinnerBackend):
    """
    Implementation that delegates rendering to the active asyncio event
    loop. Permits smooth integration into existing coroutines without
    thread management overhead.
    """
    def __init__(
        self,
        stream: TextIO,
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
        super().__init__(
            stream, accel_secs, initial_fps, peak_animation_fps,
            loop_delay, frames, easing, status_state,
            status_frames, status_fps
        )
        self._async_task: asyncio.Task[None] | None = None

    def start(self) -> None:
        """Block illegal synchronous invocations."""
        raise BackendStartupError(
            "`AsyncBackend` cannot start synchronously. Please use 'async "
            "with' or decorate an async function."
        )

    def stop(self) -> None:
        """No-op for synchronous exit to accommodate strict typing."""
        pass

    async def _async_render_loop(self) -> None:
        """Internal asynchronous polling loop mapping Engine state to IO."""
        engine = RenderEngine(
            self.accel_secs,
            self.initial_fps,
            self.peak_animation_fps,
            self.frames,
            self.easing,
            self.status_state,
            self.status_frames,
            self.status_fps,
            self.oscillation
        )

        try:
            while True:
                now = time.time()
                rendered_frame = engine.tick(now)

                if rendered_frame is not None:
                    self.stream.write(
                        f'{ANSI_CARRIAGE_RETURN}{ANSI_CLEAR_LINE}'
                        f'{rendered_frame}'
                    )
                    self.stream.flush()

                work_time = time.time() - now
                await asyncio.sleep(max(0.0, self.loop_delay - work_time))
        except asyncio.CancelledError:
            pass
        finally:
            self.stream.write(f'{ANSI_CARRIAGE_RETURN}{ANSI_CLEAR_LINE}')
            self.stream.flush()

    async def astart(self) -> None:
        """Schedule the worker coroutine in the active event loop."""
        self._async_task = asyncio.create_task(self._async_render_loop())

    async def astop(self) -> None:
        """Cancel the scheduled execution trace."""
        if self._async_task:
            self._async_task.cancel()
            try:
                await self._async_task
            except asyncio.CancelledError:
                pass
            self._async_task = None
