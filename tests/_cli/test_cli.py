from unittest.mock import MagicMock, patch

import pytest

from seawhirl._cli.cli import _build_parser, main
from seawhirl._core.presets import PRESETS


def test_parser_defaults() -> None:
    parser = _build_parser()
    args = parser.parse_args([])

    assert args.preset == 'whirl'
    assert args.accel == 3.0
    assert args.duration == 5.0
    assert args.easing == 'logarithmic'
    assert args.status_text == ''
    assert args.oscillation is False
    assert args.custom is None


def test_parser_custom_args() -> None:
    parser = _build_parser()
    args = parser.parse_args([
        'dots',
        '--accel', '1.5',
        '--duration', '2.0',
        '--easing', 'spring',
        '--text', 'Loading',
        '--oscillation'
    ])

    assert args.preset == 'dots'
    assert args.accel == 1.5
    assert args.duration == 2.0
    assert args.easing == 'spring'
    assert args.status_text == 'Loading'
    assert args.oscillation is True


def test_parser_invalid_preset(capsys: pytest.CaptureFixture[str]) -> None:
    parser = _build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(['invalid_preset_name'])

    captured = capsys.readouterr()
    assert "invalid choice: 'invalid_preset_name'" in captured.err


@patch('seawhirl._cli.cli.Spinner')
@patch('seawhirl._cli.cli.time.sleep')
@patch('sys.argv', ['seawhirl'])
def test_main_default_execution(
    mock_sleep: MagicMock,
    mock_spinner_cls: MagicMock,
    capsys: pytest.CaptureFixture[str]
) -> None:
    mock_spinner_instance = MagicMock()
    mock_spinner_cls.return_value = mock_spinner_instance

    main()

    mock_spinner_cls.assert_called_once()
    kwargs = mock_spinner_cls.call_args.kwargs
    assert kwargs['accel_secs'] == 3.0
    assert kwargs['frames'] == PRESETS['whirl']
    assert kwargs['status_text'] == ''
    assert kwargs['oscillation'] is False

    mock_spinner_instance.__enter__.assert_called_once()
    mock_sleep.assert_called_once_with(5.0)
    mock_spinner_instance.__exit__.assert_called_once()

    captured = capsys.readouterr()
    assert 'Spinner finished.' in captured.out


@patch('seawhirl._cli.cli.Spinner')
@patch('seawhirl._cli.cli.time.sleep')
@patch('sys.argv', ['seawhirl', '--custom', '🌊,🌲,🪨'])
def test_main_custom_frames(
    _mock_sleep: MagicMock,
    mock_spinner_cls: MagicMock
) -> None:
    main()

    mock_spinner_cls.assert_called_once()
    kwargs = mock_spinner_cls.call_args.kwargs
    assert kwargs['frames'] == ['🌊', '🌲', '🪨']


@patch('seawhirl._cli.cli.Spinner')
@patch('seawhirl._cli.cli.time.sleep')
@patch('sys.argv', ['seawhirl'])
def test_main_keyboard_interrupt(
    mock_sleep: MagicMock,
    _mock_spinner_cls: MagicMock,
    capsys: pytest.CaptureFixture[str]
) -> None:
    mock_sleep.side_effect = KeyboardInterrupt()

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert 'Spinner terminated.' in captured.out
