import io
import os
import sys
from unittest.mock import patch

import pytest

from seawhirl._core.config import SpinnerConfig
from seawhirl._core.easing import Logarithmic
from seawhirl._core.state import SpinnerState


@pytest.fixture
def mock_stdout():
    original_stdout = sys.stdout
    buffer = io.StringIO()

    buffer.isatty = lambda: True
    buffer.encoding = 'utf-8'

    sys.stdout = buffer
    yield buffer
    sys.stdout = original_stdout


@pytest.fixture
def mock_terminal_size():
    with patch('shutil.get_terminal_size') as mock_size:
        mock_size.return_value = os.terminal_size((80, 24))
        yield mock_size


@pytest.fixture
def dummy_config():
    return SpinnerConfig(
        accel_secs=1.0,
        initial_fps=2.0,
        peak_animation_fps=10.0,
        loop_delay=0.1,
        frames=['-', '\\', '|', '/'],
        easing=Logarithmic(),
        status_frames=['.', '..', '...'],
        status_fps=2.0,
        oscillation=False
    )


@pytest.fixture
def dummy_state():
    return SpinnerState(status_text='Loading')
