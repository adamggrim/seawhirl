import pytest

from seawhirl._core.exceptions import (
    BackendStartupError,
    InvalidColorError,
    InvalidPresetError,
    SeawhirlError,
)


def test_seawhirl_error_base() -> None:
    assert issubclass(SeawhirlError, Exception)


@pytest.mark.parametrize('exception_cls', [
    BackendStartupError,
    InvalidColorError,
    InvalidPresetError,
])
def test_custom_exception_inheritance(exception_cls: type[Exception]) -> None:
    assert issubclass(exception_cls, SeawhirlError)


@pytest.mark.parametrize(
    ('exception_cls', 'message'),
    [
        (SeawhirlError, 'Base failure'),
        (BackendStartupError, 'Cannot start async loop'),
        (InvalidPresetError, "Unknown style: 'nymph'"),
    ],
)
def test_exception_instantiation(
    exception_cls: type[Exception],
    message: str
) -> None:
    with pytest.raises(exception_cls, match=message):
        raise exception_cls(message)
