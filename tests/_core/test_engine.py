import os
from unittest.mock import patch

import pytest

from seawhirl._core.config import SpinnerConfig
from seawhirl._core.easing import Logarithmic
from seawhirl._core.engine import (
    RenderEngine,
    _calculate_current_fps,
    _truncate_text,
)
from seawhirl._core.state import SpinnerState
from seawhirl._core.terminal import ANSI_MOVE_COLUMN


def test_calculate_fps_no_oscillation_before_peak() -> None:
    easing = Logarithmic()
    fps = _calculate_current_fps(
        elapsed_total=1.5,
        accel_secs=3.0,
        initial_fps=10.0,
        peak_fps=60.0,
        easing=easing,
        oscillation=False
    )

    expected_multiplier = easing.calculate_multiplier(0.5)
    expected_fps = 10.0 + (50.0 * expected_multiplier)

    assert fps == pytest.approx(expected_fps)


def test_calculate_fps_no_oscillation_after_peak() -> None:
    fps = _calculate_current_fps(
        elapsed_total=5.0,
        accel_secs=3.0,
        initial_fps=10.0,
        peak_fps=60.0,
        easing=Logarithmic(),
        oscillation=False
    )
    assert fps == 60.0


def test_calculate_fps_with_oscillation() -> None:
    easing = Logarithmic()
    fps = _calculate_current_fps(
        elapsed_total=4.5,
        accel_secs=3.0,
        initial_fps=10.0,
        peak_fps=60.0,
        easing=easing,
        oscillation=True
    )

    expected_multiplier = easing.calculate_multiplier(0.5)
    expected_fps = 10.0 + (50.0 * expected_multiplier)

    assert fps == pytest.approx(expected_fps)


def test_truncate_text_short() -> None:
    assert _truncate_text('Loading', 20) == 'Loading'


def test_truncate_text_long() -> None:
    assert _truncate_text(
        'splash your great pines / on our rocks', 24
        ) == 'splash your great pines...'


def test_truncate_text_with_emojis() -> None:
    text = 'H👨‍👩‍👧‍👦D'
    truncated = _truncate_text(text, 2)
    assert truncated == 'H...'


@pytest.fixture
def engine_config() -> SpinnerConfig:
    return SpinnerConfig(
        accel_secs=2.0,
        initial_fps=10.0,
        peak_animation_fps=10.0,  # Constant FPS for predictable math
        loop_delay=0.1,
        frames=['1', '2', '3', '4'],
        easing=Logarithmic(),
        status_frames=['.', '..', '...'],
        status_fps=10.0,
        oscillation=False
    )


def test_render_engine_initialization(engine_config: SpinnerConfig) -> None:
    state = SpinnerState(status_text='Init')
    engine = RenderEngine(engine_config, state)

    assert engine.num_frames == 4
    assert engine.num_status_frames == 3
    assert engine.max_frame_width == 1
    assert engine.prev_rendered_frame == ''


@patch('seawhirl._core.engine.shutil.get_terminal_size')
def test_render_engine_tick_changes(
    mock_terminal_size,
    engine_config: SpinnerConfig
) -> None:
    mock_terminal_size.return_value = os.terminal_size((80, 24))
    state = SpinnerState(status_text='Loading')
    engine = RenderEngine(engine_config, state)

    engine.current_frame = 0.0
    engine.current_status_frame = 0.0

    frame = engine.tick(engine.start_time)
    expected_ansi = ANSI_MOVE_COLUMN.format(col=engine.max_frame_width + 2)

    assert frame == f'1{expected_ansi}Loading.'
    assert engine.prev_rendered_frame == frame

    assert engine.tick(engine.start_time) is None

    frame_advanced = engine.tick(engine.start_time + 0.15)
    assert frame_advanced == f'2{expected_ansi}Loading..'


@patch('seawhirl._core.engine.shutil.get_terminal_size')
def test_render_engine_truncation_cache(
    mock_terminal_size,
    engine_config: SpinnerConfig
) -> None:
    mock_terminal_size.return_value = os.terminal_size((8, 24))
    state = SpinnerState(status_text='Hurling green')
    engine = RenderEngine(engine_config, state)

    engine.current_frame = 0.0
    engine.current_status_frame = 0.0

    first_frame = engine.tick(engine.start_time)
    assert '...' in first_frame

    cache_key = engine._text_cache[0]
    assert cache_key is not None
    assert cache_key[0] == 'Hurling green.'

    second_frame = engine.tick(engine.start_time + 0.15)
    assert '...' in second_frame


@patch('seawhirl._core.engine.shutil.get_terminal_size')
def test_render_engine_frame_too_wide(
    mock_terminal_size,
) -> None:
    mock_terminal_size.return_value = os.terminal_size((1, 24))
    state = SpinnerState(status_text='')
    config = SpinnerConfig(
        accel_secs=2.0, initial_fps=10.0, peak_animation_fps=10.0,
        loop_delay=0.1, frames=['██'], easing=Logarithmic(),
        status_frames=[], status_fps=10.0, oscillation=False
    )
    engine = RenderEngine(config, state)
    frame = engine.tick(engine.start_time)

    assert frame is None


@patch('seawhirl._core.engine.shutil.get_terminal_size')
def test_render_engine_no_status_text(
    mock_terminal_size,
    engine_config: SpinnerConfig
) -> None:
    mock_terminal_size.return_value = os.terminal_size((80, 24))
    state = SpinnerState(status_text='')
    engine = RenderEngine(engine_config, state)

    engine.current_frame = 0.0
    frame = engine.tick(engine.start_time)

    assert frame == '1'
