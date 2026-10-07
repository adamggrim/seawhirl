import seawhirl
from seawhirl._core.easing import (
    EasingStrategy,
    Inertial,
    Logarithmic,
    Sinusoidal,
    Spring,
)
from seawhirl._core.exceptions import (
    BackendStartupError,
    InvalidColorError,
    InvalidPresetError,
    SeawhirlError,
)
from seawhirl._core.presets import PRESETS
from seawhirl._lib.spinner import Backend, Spinner


def test_all_exports() -> None:
    expected_exports = [
        'Backend',
        'BackendStartupError',
        'EasingStrategy',
        'Inertial',
        'InvalidColorError',
        'InvalidPresetError',
        'Logarithmic',
        'PRESETS',
        'SeawhirlError',
        'Sinusoidal',
        'Spinner',
        'Spring'
    ]

    assert hasattr(seawhirl, '__all__')
    assert getattr(seawhirl, '__all__') == expected_exports


def test_imports_match_origins() -> None:
    assert seawhirl.Backend is Backend
    assert seawhirl.BackendStartupError is BackendStartupError
    assert seawhirl.EasingStrategy is EasingStrategy
    assert seawhirl.Inertial is Inertial
    assert seawhirl.InvalidColorError is InvalidColorError
    assert seawhirl.InvalidPresetError is InvalidPresetError
    assert seawhirl.Logarithmic is Logarithmic
    assert seawhirl.PRESETS is PRESETS
    assert seawhirl.SeawhirlError is SeawhirlError
    assert seawhirl.Sinusoidal is Sinusoidal
    assert seawhirl.Spinner is Spinner
    assert seawhirl.Spring is Spring


def test_public_namespace_cleanliness() -> None:
    public_attributes = {
        attr for attr in dir(seawhirl)
        if not attr.startswith('_')
    }

    expected_attributes = set(getattr(seawhirl, '__all__'))

    assert public_attributes == expected_attributes
