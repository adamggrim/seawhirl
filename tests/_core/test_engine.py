import os

import pytest

from seawhirl._core.config import SpinnerConfig, SpinnerState
from seawhirl._core.easing import Logarithmic, Sinusoidal
from seawhirl._core.engine import (
    RenderEngine,
    _calculate_color_index,
    _truncate_text,
)
from seawhirl._core.terminal import ANSI_MOVE_COLUMN


@pytest.mark.parametrize(
    ('text', 'max_width', 'expected'),
    [
        ('NON-ENERGIZED FUTURE', 20, 'NON-ENERGIZED FUTURE'),
        (
            'splash your great pines / on our rocks',
            26,
            'splash your great pines...',
        ),
        ('H.👨‍👩‍👧‍👦D.', 4, 'H...'),
    ]
)
def test_truncate_text(text: str, max_width: int, expected: str) -> None:
    assert _truncate_text(text, max_width) == expected


@pytest.fixture
def engine_config() -> SpinnerConfig:
    return SpinnerConfig(
        accel_secs=2.0,
        initial_fps=10.0,
        peak_animation_fps=10.0,
        loop_delay=0.1,
        frames=['1', '2', '3', '4'],
        easing=Logarithmic(),
        status_frames=['.', '..', '...'],
        status_fps=10.0,
        oscillation=False
    )


def test_render_engine_initialization(engine_config: SpinnerConfig) -> None:
    state = SpinnerState(status_text='All MOMENTUM')
    engine = RenderEngine(engine_config, state)

    assert engine.num_frames == 4
    assert engine.num_status_frames == 3
    assert engine.max_frame_width == 1
    assert engine.prev_rendered_frame == ''


@pytest.mark.usefixtures('mock_terminal_size')
def test_render_engine_tick_changes(engine_config: SpinnerConfig) -> None:
    state = SpinnerState(status_text='Whirl up sea')
    engine = RenderEngine(engine_config, state)

    engine.current_frame = 0.0
    engine.current_status_frame = 0.0

    frame = engine.tick(engine.start_time)
    expected_ansi = ANSI_MOVE_COLUMN.format(col=engine.max_frame_width + 2)

    assert frame == f'1{expected_ansi}Whirl up sea.'
    assert engine.prev_rendered_frame == frame

    assert engine.tick(engine.start_time) is None

    frame_advanced = engine.tick(engine.start_time + 0.15)
    assert frame_advanced == f'2{expected_ansi}Whirl up sea..'

    frame_final = engine.tick(engine.start_time + 0.25)
    assert frame_final == f'3{expected_ansi}Whirl up sea...'


def test_render_engine_truncation_cache(
    mock_terminal_size,
    engine_config: SpinnerConfig
) -> None:
    mock_terminal_size.return_value = os.terminal_size((29, 24))
    state = SpinnerState(
        status_text='In decency one can only call it a VORTEX'
    )
    engine = RenderEngine(engine_config, state)

    engine.current_frame = 0.0
    engine.current_status_frame = 0.0

    first_frame = engine.tick(engine.start_time)
    assert first_frame is not None
    assert first_frame.endswith('In decency one can only...')

    cache_key = engine._text_cache[0]
    assert cache_key is not None
    assert cache_key[0] == 'In decency one can only call it a VORTEX.'

    engine.current_status_frame = -1.5
    second_frame = engine.tick(engine.start_time + 0.15)
    assert second_frame is not None
    assert second_frame.endswith('In decency one can only...')


def test_render_engine_frame_too_wide(mock_terminal_size) -> None:
    mock_terminal_size.return_value = os.terminal_size((1, 24))
    state = SpinnerState(status_text='')
    config = SpinnerConfig(
        accel_secs=2.0, initial_fps=10.0, peak_animation_fps=10.0,
        loop_delay=0.1, frames=['██'], easing=Logarithmic(),
        status_frames=[], status_fps=10.0, oscillation=False
    )
    engine = RenderEngine(config, state)
    assert engine.tick(engine.start_time) is None


@pytest.mark.usefixtures('mock_terminal_size')
def test_render_engine_no_status_text(engine_config: SpinnerConfig) -> None:
    state = SpinnerState(status_text='')
    engine = RenderEngine(engine_config, state)

    engine.current_frame = 0.0
    assert engine.tick(engine.start_time) == '1'


@pytest.mark.parametrize(
    ('current_val', 'expected'),
    [
        (0.0, 0.0),
        (1.0, 0.5),
        (2.0, 1.0),
        (3.0, 1.5),
        (4.0, 2.0),
    ],
)
def test_calculate_color_index_oscillation(
    current_val: float,
    expected: float
) -> None:
    easing = Sinusoidal().indexed()
    result = _calculate_color_index(current_val, 2.0, easing, oscillation=True)
    assert result == pytest.approx(expected)


@pytest.mark.usefixtures('mock_terminal_size')
def test_render_engine_indexed_color_mode() -> None:
    config = SpinnerConfig(
        accel_secs=2.0,
        initial_fps=10.0,
        peak_animation_fps=10.0,
        loop_delay=0.1,
        frames=['1'],
        easing=Sinusoidal().indexed(),
        status_frames=[],
        status_fps=10.0,
        oscillation=True,
    )
    state = SpinnerState(
        status_text='',
        colors=((10, 0, 0), (20, 0, 0), (30, 0, 0)),
    )
    engine = RenderEngine(config, state)

    assert engine.tick(engine.start_time) == '\033[38;2;10;0;0m1\033[0m'
    assert engine.tick(engine.start_time + 2.0) == '\033[38;2;20;0;0m1\033[0m'
    assert engine.tick(engine.start_time + 4.0) == '\033[38;2;30;0;0m1\033[0m'
