import runpy
from unittest.mock import patch


def test_main_module_invokes_cli() -> None:
    with patch('seawhirl._cli.cli.main') as mock_main:
        # Simulate running `python -m seawhirl`.
        runpy.run_module('seawhirl', run_name='__main__')
        mock_main.assert_called_once()


def test_main_module_import_does_not_invoke_cli() -> None:
    with patch('seawhirl._cli.cli.main') as mock_main:
        runpy.run_module('seawhirl', run_name='not_main')
        mock_main.assert_not_called()
