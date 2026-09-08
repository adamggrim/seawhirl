import asyncio
import io
import time
from unittest.mock import MagicMock, patch

import pytest

from seawhirl._core.backends import AsyncBackend, ThreadBackend
from seawhirl._core.exceptions import BackendStartupError


def test_thread_backend_lifecycle(dummy_config, dummy_state) -> None:
    stream = io.StringIO()
    backend = ThreadBackend(stream, dummy_config, dummy_state)

    assert backend._thread is None

    backend.start()
    assert backend._thread is not None
    assert backend._thread.is_alive()

    backend.stop()
    assert backend._thread is None


def test_thread_backend_context_manager(dummy_config, dummy_state) -> None:
    stream = io.StringIO()
    backend = ThreadBackend(stream, dummy_config, dummy_state)

    with backend:
        assert backend._thread is not None
        assert backend._thread.is_alive()

    assert backend._thread is None


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


def test_async_backend_sync_start_raises(dummy_config, dummy_state) -> None:
    stream = io.StringIO()
    backend = AsyncBackend(stream, dummy_config, dummy_state)

    with pytest.raises(BackendStartupError):
        backend.start()


def test_async_backend_sync_stop_is_noop(dummy_config, dummy_state) -> None:
    stream = io.StringIO()
    backend = AsyncBackend(stream, dummy_config, dummy_state)

    backend.stop()


@pytest.mark.asyncio
async def test_async_backend_lifecycle(dummy_config, dummy_state) -> None:
    stream = io.StringIO()
    backend = AsyncBackend(stream, dummy_config, dummy_state)

    assert backend._async_task is None

    await backend.astart()
    assert backend._async_task is not None
    assert not backend._async_task.done()

    await backend.astop()
    assert backend._async_task is None


@pytest.mark.asyncio
async def test_async_backend_context_manager(
    dummy_config,
    dummy_state
) -> None:
    stream = io.StringIO()
    backend = AsyncBackend(stream, dummy_config, dummy_state)

    async with backend:
        assert backend._async_task is not None
        assert not backend._async_task.done()

    assert backend._async_task is None


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
