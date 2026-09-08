import dataclasses

import pytest

from seawhirl._core.config import SpinnerConfig
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


def test_config_immutability() -> None:
    config = SpinnerConfig(
        accel_secs=1.0,
        initial_fps=2.0,
        peak_animation_fps=10.0,
        loop_delay=0.1,
        frames=['1', '2'],
        easing=Logarithmic(),
        status_frames=[],
        status_fps=0.0,
        oscillation=False
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.accel_secs = 5.0
