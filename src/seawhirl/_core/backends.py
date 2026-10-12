"""Threading and asyncio backends for rendering."""

from __future__ import annotations

import asyncio
import sys
import threading
import time
import types
from abc import ABC, abstractmethod
from typing import TextIO

from seawhirl._core.config import SpinnerConfig, SpinnerState
from seawhirl._core.engine import RenderEngine
from seawhirl._core.exceptions import BackendStartupError
from seawhirl._core.terminal import ANSI_CARRIAGE_RETURN, ANSI_CLEAR_LINE


class SpinnerBackend(ABC):
    """Abstract base class defining the contract for continuous
    rendering.
    """
    def __init__(
        self,
        stream: TextIO,
        config: SpinnerConfig,
        state: SpinnerState,
        lock: threading.Lock | None = None
    ) -> None:
        self.stream = stream
        self.config = config
        self.state = state
        self._lock = lock or threading.Lock()

    def _write_frame(self, frame: str = '') -> None:
        with self._lock:
            self.stream.write(f'{ANSI_CARRIAGE_RETURN}{ANSI_CLEAR_LINE}{frame}')
            self.stream.flush()

    @abstractmethod
    def start(self) -> None:
        """Start the synchronous rendering loop."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the synchronous rendering loop."""
        pass

    async def astart(self) -> None:
        """Start the asynchronous rendering loop. Defaults to sync
        start.
        """
        self.start()

    async def astop(self) -> None:
        """Stop the asynchronous rendering loop. Defaults to sync
        stop.
        """
        self.stop()

    def __enter__(self) -> 'SpinnerBackend':
        self.start()
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: types.TracebackType | None
    ) -> None:
        self.stop()

    async def __aenter__(self) -> 'SpinnerBackend':
        await self.astart()
        return self

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: types.TracebackType | None
    ) -> None:
        await self.astop()


class ThreadBackend(SpinnerBackend):
    """Class that delegates rendering to a daemonized background
    thread.
    """
    def __init__(
        self,
        stream: TextIO,
        config: SpinnerConfig,
        state: SpinnerState,
        lock: threading.Lock | None = None
    ) -> None:
        super().__init__(stream, config, state, lock)
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def _sync_render_loop(self) -> None:
        engine = RenderEngine(self.config, self.state)

        try:
            next_tick = time.perf_counter()
            while not self._stop_event.is_set():
                if (rendered := engine.tick(time.perf_counter())) is not None:
                    self._write_frame(rendered)

                next_tick += self.config.loop_delay
                time.sleep(max(0.0, next_tick - time.perf_counter()))
        except KeyboardInterrupt:
            pass
        except Exception as e:
            sys.stderr.write(f'\nSpinner worker encountered an error: {e}\n')
            sys.stderr.flush()
        finally:
            self._write_frame()

    def start(self) -> None:
        """Initialize the thread loop safely."""
        if self._thread is not None and self._thread.is_alive():
            return
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
    """Class that delegates rendering to the active asyncio event
    loop.
    """
    def __init__(
        self,
        stream: TextIO,
        config: SpinnerConfig,
        state: SpinnerState,
        lock: threading.Lock | None = None
    ) -> None:
        super().__init__(stream, config, state, lock)
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

    async def _awrite_frame(self, frame: str = '') -> None:
        """Write a frame without blocking the event loop."""
        if self._lock.acquire(blocking=False):
            try:
                self.stream.write(
                    f'{ANSI_CARRIAGE_RETURN}{ANSI_CLEAR_LINE}{frame}'
                )
                self.stream.flush()
            finally:
                self._lock.release()
        else:
            await asyncio.to_thread(self._write_frame, frame)

    async def _async_render_loop(self) -> None:
        """Internal asynchronous polling loop mapping engine state to 
        I/O.
        """
        engine = RenderEngine(self.config, self.state)

        try:
            while True:
                now = time.perf_counter()
                if (rendered := engine.tick(now)) is not None:
                    await self._awrite_frame(rendered)

                work_time = time.perf_counter() - now
                await asyncio.sleep(
                    max(0.0, self.config.loop_delay - work_time)
                )
        except asyncio.CancelledError:
            raise
        finally:
            self._write_frame()

    async def astart(self) -> None:
        """Schedule the worker coroutine in the active event loop."""
        if self._async_task is not None and not self._async_task.done():
            return
        self._async_task = asyncio.create_task(self._async_render_loop())

    async def astop(self) -> None:
        """Cancel the background rendering task."""
        if self._async_task is not None:
            task = self._async_task
            self._async_task = None
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
