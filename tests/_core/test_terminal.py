import io
import os
import signal
import sys
import threading
from unittest.mock import ANY, MagicMock, patch

import pytest

from seawhirl._core.terminal import (
    ANSI_CARRIAGE_RETURN,
    ANSI_CLEAR_LINE,
    ANSI_HIDE_CURSOR,
    ANSI_SHOW_CURSOR,
    StreamProxy,
    TerminalLifecycle,
    enable_windows_vt_processing,
    is_supported_terminal,
)


class TestStreamProxy:
    def test_write_empty_string_returns_zero(self) -> None:
        stream = io.StringIO()
        proxy = StreamProxy(stream)

        assert proxy.write('') == 0
        assert stream.getvalue() == ''
        assert proxy._is_new_line is True

    def test_write_handles_bare_newlines(self) -> None:
        stream = io.StringIO()
        proxy = StreamProxy(stream)

        proxy.write('\n')

        assert stream.getvalue() == '\n'
        assert proxy._is_new_line is True

    def test_write_prepends_ansi_codes_for_new_lines(self) -> None:
        stream = io.StringIO()
        proxy = StreamProxy(stream)

        proxy.write('Whirl up sea...')

        expected = f'{ANSI_CARRIAGE_RETURN}{ANSI_CLEAR_LINE}Whirl up sea...'
        assert stream.getvalue() == expected
        assert proxy._is_new_line is False

    def test_write_continuous_text(self) -> None:
        stream = io.StringIO()
        proxy = StreamProxy(stream)

        proxy.write('whirl your pointed ')
        proxy.write('pines')

        expected = (
            f'{ANSI_CARRIAGE_RETURN}{ANSI_CLEAR_LINE}'
            'whirl your pointed pines'
        )
        assert stream.getvalue() == expected

    def test_write_multiline_tracks_trailing_newline(self) -> None:
        stream = io.StringIO()
        proxy = StreamProxy(stream)

        proxy.write('Whirl up, sea—\n')
        assert proxy._is_new_line is True

        proxy.write('whirl your pointed pines')
        assert proxy._is_new_line is False

        expected = (
            f'{ANSI_CARRIAGE_RETURN}{ANSI_CLEAR_LINE}Whirl up, sea—\n'
            f'{ANSI_CARRIAGE_RETURN}{ANSI_CLEAR_LINE}whirl your pointed pines'
        )
        assert stream.getvalue() == expected

    def test_delegation_methods(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = True
        stream.fileno.return_value = 1

        proxy = StreamProxy(stream)

        assert proxy.isatty() is True
        assert proxy.fileno() == 1

        proxy.flush()
        stream.flush.assert_called_once()

    def test_getattr_delegates_to_original_stream(self) -> None:
        stream = MagicMock()
        stream.encoding = 'utf-8'
        stream.errors = 'strict'

        proxy = StreamProxy(stream)

        assert proxy.encoding == 'utf-8'
        assert proxy.errors == 'strict'


class TestTerminalLifecycle:
    def test_disabled_lifecycle(self) -> None:
        stream = MagicMock()

        with TerminalLifecycle(stream, disabled=True):
            pass

        stream.write.assert_not_called()

    def test_cursor_visibility_management(self) -> None:
        stream = MagicMock()

        with TerminalLifecycle(stream, disabled=False, handle_signals=False):
            stream.write.assert_called_once_with(ANSI_HIDE_CURSOR)
            stream.write.reset_mock()

        stream.write.assert_called_once_with(ANSI_SHOW_CURSOR)

    def test_stdout_proxy_application(self) -> None:
        stream = MagicMock()
        original_stdout = sys.stdout

        with TerminalLifecycle(stream, disabled=False, handle_signals=False):
            assert isinstance(sys.stdout, StreamProxy)

        assert sys.stdout is original_stdout

    def test_stdout_proxy_shares_lifecycle_lock(self) -> None:
        stream = MagicMock()
        shared_lock = threading.Lock()

        with TerminalLifecycle(
            stream,
            disabled=False,
            handle_signals=False,
            lock=shared_lock
        ) as lifecycle:
            assert isinstance(sys.stdout, StreamProxy)
            assert sys.stdout._lock is shared_lock
            assert lifecycle.lock is shared_lock

    @patch('signal.signal')
    @patch('signal.getsignal')
    def test_signal_handler_registration(
        self,
        mock_getsignal: MagicMock,
        mock_signal: MagicMock
    ) -> None:
        stream = MagicMock()
        mock_getsignal.return_value = signal.SIG_DFL

        with TerminalLifecycle(stream, disabled=False, handle_signals=True):
            assert mock_signal.call_count == 2

        assert mock_signal.call_count == 4

    @patch('signal.signal')
    @patch('signal.getsignal')
    def test_sigint_default_int_handler_registration(
        self,
        mock_getsignal: MagicMock,
        mock_signal: MagicMock
    ) -> None:
        stream = MagicMock()
        mock_getsignal.side_effect = [
            signal.default_int_handler,
            signal.SIG_DFL
        ]

        with TerminalLifecycle(stream, disabled=False, handle_signals=True):
            assert mock_signal.call_count == 2
            mock_signal.assert_any_call(
                signal.SIGINT,
                ANY
            )


class TestWindowsVTProcessing:
    @patch('platform.system', return_value='Linux')
    def test_ignored_on_non_windows(self, _mock_system: MagicMock) -> None:
        try:
            enable_windows_vt_processing()
        except ImportError:
            pytest.fail('Should not attempt to import ctypes.windll on Linux')

    @patch('platform.system', return_value='Windows')
    def test_attempts_vt_enable_on_windows(
        self,
        _mock_system: MagicMock
    ) -> None:
        """Verify Windows standard handles are modified using ctypes."""
        mock_ctypes = MagicMock()
        with patch.dict(sys.modules, {'ctypes': mock_ctypes}):
            enable_windows_vt_processing()
            assert mock_ctypes.windll.kernel32.GetStdHandle.called


class TestIsSupportedTerminal:
    """Tests for evaluating terminal capability heuristics."""

    def test_supported_terminal(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = True
        stream.encoding = 'utf-8'

        with patch.dict(os.environ, clear=True):
            assert is_supported_terminal(stream) is True

    def test_missing_isatty_disables_support(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = False
        stream.encoding = 'utf-8'

        with patch.dict(os.environ, clear=True):
            assert is_supported_terminal(stream) is False

    def test_invalid_encoding_disables_support(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = True
        stream.encoding = 'cp1252'

        with patch.dict(os.environ, clear=True):
            assert is_supported_terminal(stream) is False

    @pytest.mark.parametrize('env_var, value', [
        ('CI', '1'),
        ('NO_COLOR', 'hurl your green over us'),
        ('TERM', 'dumb'),
    ])
    def test_environment_variables_disable_support(
        self,
        env_var: str,
        value: str
    ) -> None:
        stream = MagicMock()
        stream.isatty.return_value = True
        stream.encoding = 'utf-8'

        with patch.dict(os.environ, {env_var: value}, clear=True):
            assert is_supported_terminal(stream) is False
