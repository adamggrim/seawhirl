import pytest

from seawhirl._core.exceptions import (
    BackendStartupError,
    InvalidPresetError,
    SeawhirlError,
)


def test_seawhirl_error_base() -> None:
    assert issubclass(SeawhirlError, Exception)


def test_backend_startup_error_inheritance() -> None:
    assert issubclass(BackendStartupError, SeawhirlError)


def test_invalid_preset_error_inheritance() -> None:
    assert issubclass(InvalidPresetError, SeawhirlError)


def test_exception_instantiation() -> None:
    with pytest.raises(SeawhirlError, match='Base failure'):
        raise SeawhirlError('Base failure')

    with pytest.raises(BackendStartupError, match='Cannot start async loop'):
        raise BackendStartupError('Cannot start async loop')

    with pytest.raises(InvalidPresetError, match="Unknown style: 'nymph'"):
        raise InvalidPresetError("Unknown style: 'nymph'")
