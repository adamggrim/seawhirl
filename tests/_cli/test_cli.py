from unittest.mock import MagicMock, patch

import pytest

from seawhirl._cli.cli import _build_parser, main
from seawhirl._core.presets import PRESETS


@pytest.fixture
def parser():
    return _build_parser()


@pytest.fixture
def mock_cli_env():
    with (
        patch('seawhirl._cli.cli.Spinner') as mock_spinner_cls,
        patch('seawhirl._cli.cli.time.sleep') as mock_sleep,
    ):
        yield mock_spinner_cls, mock_sleep


def test_parser_defaults(parser) -> None:
    args = parser.parse_args([])

    assert args.preset == 'whirl'
    assert args.accel == 3.0
    assert args.duration == 5.0
    assert args.easing == 'logarithmic'
    assert args.status_text == ''
    assert args.oscillation is False
    assert args.custom is None


def test_parser_custom_args(parser) -> None:
    args = parser.parse_args([
        'dots',
        '--accel', '1.5',
        '--duration', '2.0',
        '--easing', 'spring',
        '--text', 'It represents, in mechanics, the greatest efficiency.',
        '--oscillation'
    ])

    assert args.preset == 'dots'
    assert args.accel == 1.5
    assert args.duration == 2.0
    assert args.easing == 'spring'
    assert (
        args.status_text
        == 'It represents, in mechanics, the greatest efficiency.'
    )
    assert args.oscillation is True


def test_parser_invalid_preset(
    parser,
    capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit):
        parser.parse_args(['invalid_preset_name'])

    captured = capsys.readouterr()
    assert "invalid choice: 'invalid_preset_name'" in captured.err


@patch('sys.argv', ['seawhirl'])
def test_main_default_execution(
    mock_cli_env: tuple[MagicMock, MagicMock],
    capsys: pytest.CaptureFixture[str]
) -> None:
    mock_spinner_cls, mock_sleep = mock_cli_env
    mock_spinner_instance = mock_spinner_cls.return_value

    main()

    mock_spinner_cls.assert_called_once()
    kwargs = mock_spinner_cls.call_args.kwargs
    assert kwargs['accel_secs'] == 3.0
    assert kwargs['frames'] == PRESETS['whirl']
    assert kwargs['status_text'] == ''
    assert kwargs['oscillation'] is False
    assert kwargs['color'] is None

    mock_spinner_instance.__enter__.assert_called_once()
    mock_sleep.assert_called_once_with(5.0)
    mock_spinner_instance.__exit__.assert_called_once()

    captured = capsys.readouterr()
    assert 'Spinner finished.' in captured.out


@patch('sys.argv', ['seawhirl', '--custom', '🌊,🌲,🪨'])
def test_main_custom_frames(
    mock_cli_env: tuple[MagicMock, MagicMock]
) -> None:
    mock_spinner_cls, _ = mock_cli_env
    main()

    mock_spinner_cls.assert_called_once()
    assert mock_spinner_cls.call_args.kwargs['frames'] == ['🌊', '🌲', '🪨']


@patch('sys.argv', ['seawhirl'])
def test_main_keyboard_interrupt(
    mock_cli_env: tuple[MagicMock, MagicMock],
    capsys: pytest.CaptureFixture[str]
) -> None:
    _, mock_sleep = mock_cli_env
    mock_sleep.side_effect = KeyboardInterrupt()

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert 'Spinner terminated.' in captured.out
