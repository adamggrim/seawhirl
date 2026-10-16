import runpy
from unittest.mock import patch

import pytest


@pytest.mark.parametrize(('run_name', 'expected_calls'), [
    ('__main__', 1),
    ('not_main', 0),
])
def test_main_module_execution(run_name: str, expected_calls: int) -> None:
    with patch('seawhirl._cli.cli.main') as mock_main:
        runpy.run_module('seawhirl', run_name=run_name)
        assert mock_main.call_count == expected_calls
