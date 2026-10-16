import dataclasses

import pytest

from seawhirl._core.config import SpinnerConfig, SpinnerState
from seawhirl._core.easing import Logarithmic


def test_config_instantiation() -> None:
    easing_strategy = Logarithmic()

    config = SpinnerConfig(
        accel_secs=2.5,
        initial_fps=5.0,
        peak_animation_fps=60.0,
        loop_delay=0.016,
        frames=['A', 'B', 'C'],
        easing=easing_strategy,
        status_frames=['.', '..'],
        status_fps=1.0,
        oscillation=True
    )

    assert config.accel_secs == 2.5
    assert config.initial_fps == 5.0
    assert config.peak_animation_fps == 60.0
    assert config.loop_delay == 0.016
    assert config.frames == ['A', 'B', 'C']
    assert config.easing is easing_strategy
    assert config.status_frames == ['.', '..']
    assert config.status_fps == 1.0
    assert config.oscillation is True


def test_config_immutability(dummy_config: SpinnerConfig) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        dummy_config.accel_secs = 5.0


def test_state_instantiation() -> None:
    state = SpinnerState(status_text='THE IMAGE IS NOT an idea.')
    assert state.status_text == 'THE IMAGE IS NOT an idea.'


def test_state_mutability() -> None:
    state = SpinnerState(status_text='THE IMAGE IS NOT an idea.')

    state.status_text = 'It is a radiant node or cluster.'
    assert state.status_text == 'It is a radiant node or cluster.'


def test_state_slots_enforcement() -> None:
    state = SpinnerState(
        status_text=(
            'No artist can possibly get a vortex into every poem or picture.'
        )
    )

    with pytest.raises(AttributeError):
        state.custom_attribute = 'Vorticism'
