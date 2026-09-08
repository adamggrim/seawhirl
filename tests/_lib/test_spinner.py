import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from seawhirl._core.backends import AsyncBackend, ThreadBackend
from seawhirl._core.exceptions import InvalidPresetError
from seawhirl._lib.spinner import Backend, Spinner


@patch('seawhirl._lib.spinner.is_supported_terminal', return_value=True)
def test_spinner_initialization(_mock_is_supported: MagicMock) -> None:
    spinner = Spinner(
        accel_secs=1.5,
        frames='dots',
        status_text='Loading',
        oscillation=True
    )

    assert spinner.config.accel_secs == 1.5
    assert spinner.state.status_text == 'Loading'
    assert spinner.config.oscillation is True
    assert isinstance(spinner._worker, ThreadBackend)
    assert spinner._disabled is False


def test_invalid_preset_raises_error() -> None:
    with pytest.raises(InvalidPresetError, match='Unknown preset'):
        Spinner(frames='nonexistent_preset')


@patch('seawhirl._lib.spinner.is_supported_terminal', return_value=False)
@patch('seawhirl._core.terminal.TerminalLifecycle.__enter__')
def test_disabled_terminal_bypasses_rendering(
    _mock_lifecycle_enter: MagicMock,
    _mock_is_supported: MagicMock
) -> None:
    spinner = Spinner()

    with patch.object(spinner._worker, 'start') as mock_start:
        spinner.start()
        mock_start.assert_not_called()

    assert spinner._disabled is True


@patch.object(ThreadBackend, 'start')
@patch.object(ThreadBackend, 'stop')
@patch('seawhirl._lib.spinner.is_supported_terminal', return_value=True)
def test_manual_start_and_stop(
    _mock_is_supported: MagicMock,
    mock_stop: MagicMock,
    mock_start: MagicMock
) -> None:
    spinner = Spinner()

    spinner.start()
    mock_start.assert_called_once()

    spinner.stop()
    mock_stop.assert_called_once()


def test_update_status_text() -> None:
    spinner = Spinner(status_text='Initial')
    assert spinner.state.status_text == 'Initial'

    spinner.update('Updated')
    assert spinner.state.status_text == 'Updated'


@patch.object(ThreadBackend, '__enter__')
@patch.object(ThreadBackend, '__exit__')
@patch('seawhirl._lib.spinner.is_supported_terminal', return_value=True)
def test_sync_context_manager(
    _mock_is_supported: MagicMock,
    mock_exit: MagicMock,
    mock_enter: MagicMock
) -> None:
    spinner = Spinner()

    with spinner:
        mock_enter.assert_called_once()

    mock_exit.assert_called_once()


@patch.object(ThreadBackend, '__enter__')
@patch.object(ThreadBackend, '__exit__')
@patch('seawhirl._lib.spinner.is_supported_terminal', return_value=True)
def test_sync_decorator(
    _mock_is_supported: MagicMock,
    mock_exit: MagicMock,
    mock_enter: MagicMock
) -> None:
    spinner = Spinner()

    @spinner
    def mock_function() -> str:
        return 'success'

    result = mock_function()

    assert result == 'success'
    mock_enter.assert_called_once()
    mock_exit.assert_called_once()


@pytest.mark.asyncio
@patch.object(AsyncBackend, '__aenter__', new_callable=AsyncMock)
@patch.object(AsyncBackend, '__aexit__', new_callable=AsyncMock)
@patch('seawhirl._lib.spinner.is_supported_terminal', return_value=True)
async def test_async_context_manager(
    _mock_is_supported: MagicMock,
    mock_aexit: AsyncMock,
    mock_aenter: AsyncMock
) -> None:
    spinner = Spinner(backend=Backend.ASYNC)

    async with spinner:
        mock_aenter.assert_awaited_once()

    mock_aexit.assert_awaited_once()


@pytest.mark.asyncio
@patch.object(AsyncBackend, '__aenter__', new_callable=AsyncMock)
@patch.object(AsyncBackend, '__aexit__', new_callable=AsyncMock)
@patch('seawhirl._lib.spinner.is_supported_terminal', return_value=True)
async def test_async_decorator(
    _mock_is_supported: MagicMock,
    mock_aexit: AsyncMock,
    mock_aenter: AsyncMock
) -> None:
    spinner = Spinner(backend=Backend.ASYNC)

    @spinner
    async def mock_async_function() -> int:
        await asyncio.sleep(0.01)
        return 42

    result = await mock_async_function()

    assert result == 42
    mock_aenter.assert_awaited_once()
    mock_aexit.assert_awaited_once()