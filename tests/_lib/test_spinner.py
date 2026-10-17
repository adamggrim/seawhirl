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
        status_text='The vortex is the point of maximum energy.',
        oscillation=True
    )

    assert spinner.config.accel_secs == 1.5
    assert (
        spinner.state.status_text
        == 'The vortex is the point of maximum energy.'
    )
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


@pytest.fixture
def patched_thread_spinner():
    with (
        patch('seawhirl._lib.spinner.is_supported_terminal', return_value=True),
        patch.object(ThreadBackend, 'start') as mock_start,
        patch.object(ThreadBackend, 'stop') as mock_stop,
    ):
        yield Spinner(), mock_start, mock_stop


@pytest.fixture
def patched_async_spinner():
    with (
        patch('seawhirl._lib.spinner.is_supported_terminal', return_value=True),
        patch.object(
            AsyncBackend, 'astart', new_callable=AsyncMock
        ) as mock_astart,
        patch.object(
            AsyncBackend, 'astop', new_callable=AsyncMock
        ) as mock_astop,
    ):
        yield Spinner(), mock_astart, mock_astop


def test_manual_start_and_stop(patched_thread_spinner) -> None:
    spinner, mock_start, mock_stop = patched_thread_spinner

    spinner.start()
    mock_start.assert_called_once()

    spinner.stop()
    mock_stop.assert_called_once()


def test_update_status_text_and_color() -> None:
    spinner = Spinner(
        status_text='The Image is the poet’s pigment.',
        color='cyan'
    )
    assert spinner.state.status_text == 'The Image is the poet’s pigment.'
    assert spinner.state.colors == ((0, 255, 255), (0, 255, 255))

    spinner.update(
        'The painter should use his colour because he sees it or feels it.',
        color=('cyan', 'green')
    )
    assert (
        spinner.state.status_text
        == 'The painter should use his colour because he sees it or feels it.'
    )
    assert spinner.state.colors == ((0, 255, 255), (0, 128, 0))


def test_sync_context_manager(patched_thread_spinner) -> None:
    spinner, mock_start, mock_stop = patched_thread_spinner

    with spinner:
        mock_start.assert_called_once()

    mock_stop.assert_called_once()


def test_sync_decorator(patched_thread_spinner) -> None:
    spinner, mock_start, mock_stop = patched_thread_spinner

    @spinner
    def mock_function() -> str:
        return 'success'

    assert mock_function() == 'success'
    mock_start.assert_called_once()
    mock_stop.assert_called_once()


@pytest.mark.asyncio
async def test_async_context_manager(patched_async_spinner) -> None:
    spinner, mock_astart, mock_astop = patched_async_spinner

    async with spinner:
        mock_astart.assert_awaited_once()

    mock_astop.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_decorator(patched_async_spinner) -> None:
    spinner, mock_astart, mock_astop = patched_async_spinner

    @spinner
    async def mock_async_function() -> int:
        await asyncio.sleep(0.01)
        return 42

    assert await mock_async_function() == 42
    mock_astart.assert_awaited_once()
    mock_astop.assert_awaited_once()
