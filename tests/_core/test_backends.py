import asyncio
import io
import time
from unittest.mock import MagicMock, patch

import pytest

from seawhirl._core.backends import AsyncBackend, ThreadBackend
from seawhirl._core.exceptions import BackendStartupError


@pytest.fixture
def thread_backend(dummy_config, dummy_state) -> ThreadBackend:
    return ThreadBackend(io.StringIO(), dummy_config, dummy_state)


@pytest.fixture
def async_backend(dummy_config, dummy_state) -> AsyncBackend:
    return AsyncBackend(io.StringIO(), dummy_config, dummy_state)


def test_thread_backend_lifecycle(thread_backend: ThreadBackend) -> None:
    assert thread_backend._thread is None

    thread_backend.start()
    assert thread_backend._thread is not None
    assert thread_backend._thread.is_alive()

    thread_backend.stop()
    assert thread_backend._thread is None


def test_thread_backend_context_manager(thread_backend: ThreadBackend) -> None:
    with thread_backend:
        assert thread_backend._thread is not None
        assert thread_backend._thread.is_alive()

    assert thread_backend._thread is None


@patch('seawhirl._core.backends.RenderEngine')
def test_thread_backend_render_loop(
    mock_engine_cls: MagicMock,
    dummy_config,
    dummy_state
) -> None:
    stream = MagicMock()
    backend = ThreadBackend(stream, dummy_config, dummy_state)

    mock_engine = MagicMock()
    mock_engine_cls.return_value = mock_engine
    mock_engine.tick.return_value = 'mocked_frame'

    backend.start()
    time.sleep(0.05)
    backend.stop()

    assert stream.write.call_count > 0
    assert stream.flush.call_count > 0

    calls = stream.write.call_args_list
    assert any('mocked_frame' in str(call) for call in calls)


def test_async_backend_sync_start_raises(async_backend: AsyncBackend) -> None:
    with pytest.raises(BackendStartupError):
        async_backend.start()


def test_async_backend_sync_stop_is_noop(async_backend: AsyncBackend) -> None:
    async_backend.stop()


@pytest.mark.asyncio
async def test_async_backend_lifecycle(async_backend: AsyncBackend) -> None:
    assert async_backend._async_task is None

    await async_backend.astart()
    assert async_backend._async_task is not None
    assert not async_backend._async_task.done()

    await async_backend.astop()
    assert async_backend._async_task is None


@pytest.mark.asyncio
async def test_async_backend_context_manager(
    async_backend: AsyncBackend
) -> None:
    async with async_backend:
        assert async_backend._async_task is not None
        assert not async_backend._async_task.done()

    assert async_backend._async_task is None


@pytest.mark.asyncio
@patch('seawhirl._core.backends.RenderEngine')
async def test_async_backend_render_loop(
    mock_engine_cls: MagicMock,
    dummy_config,
    dummy_state
) -> None:
    stream = MagicMock()
    backend = AsyncBackend(stream, dummy_config, dummy_state)

    mock_engine = MagicMock()
    mock_engine_cls.return_value = mock_engine
    mock_engine.tick.return_value = 'async_mocked_frame'

    await backend.astart()
    await asyncio.sleep(0.05)
    await backend.astop()

    assert stream.write.call_count > 0
    assert stream.flush.call_count > 0

    calls = stream.write.call_args_list
    assert any('async_mocked_frame' in str(call) for call in calls)
