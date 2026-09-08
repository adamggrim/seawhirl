import pytest

from seawhirl._core.state import SpinnerState


def test_state_instantiation() -> None:
    state = SpinnerState(status_text='Loading')
    assert state.status_text == 'Loading'


def test_state_mutability() -> None:
    state = SpinnerState(status_text='Initial')

    state.status_text = 'Covered with green pools of fir.'
    assert state.status_text == 'Covered with green pools of fir.'


def test_state_slots_enforcement() -> None:
    state = SpinnerState(status_text='Whirling')

    with pytest.raises(AttributeError):
        state.custom_attribute = 'Pointed'
