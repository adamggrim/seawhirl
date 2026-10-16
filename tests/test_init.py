import seawhirl
from seawhirl._core.colors import register_color
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

EXPECTED_EXPORTS: dict[str, object] = {
    'Backend': Backend,
    'BackendStartupError': BackendStartupError,
    'EasingStrategy': EasingStrategy,
    'Inertial': Inertial,
    'InvalidColorError': InvalidColorError,
    'InvalidPresetError': InvalidPresetError,
    'Logarithmic': Logarithmic,
    'PRESETS': PRESETS,
    'SeawhirlError': SeawhirlError,
    'Sinusoidal': Sinusoidal,
    'Spinner': Spinner,
    'Spring': Spring,
    'register_color': register_color,
}


def test_all_exports() -> None:
    assert hasattr(seawhirl, '__all__')
    assert getattr(seawhirl, '__all__') == list(EXPECTED_EXPORTS.keys())


def test_imports_match_origins() -> None:
    for name, origin in EXPECTED_EXPORTS.items():
        assert getattr(seawhirl, name) is origin


def test_public_namespace_cleanliness() -> None:
    public_attributes = {
        attr for attr in dir(seawhirl)
        if not attr.startswith('_')
    }
    assert public_attributes == set(EXPECTED_EXPORTS.keys())
