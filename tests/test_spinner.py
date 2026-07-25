import pytest
from seawhirl import Spinner, run_with_spinner


def test_spinner_lifecycle():
    spinner = Spinner()
    assert spinner._process is None

    spinner.start()
    assert spinner._process is not None
    assert spinner._process.poll() is None

    spinner.stop()
    assert spinner._process is None


def test_spinner_context_manager():
    with Spinner() as spinner:
        assert spinner._process is not None
        assert spinner._process.poll() is None

    assert spinner._process is None


def test_spinner_decorator():
    spinner = Spinner()

    @spinner
    def decorated_task():
        assert spinner._process is not None
        return 42

    assert decorated_task() == 42
    assert spinner._process is None


def test_spinner_exception_handling():
    spinner = Spinner()

    with pytest.raises(ValueError, match='Task failed'):
        with spinner:
            assert spinner._process is not None
            raise ValueError('Task failed')

    assert spinner._process is None


def test_run_with_spinner():
    def add(a, b):
        return a + b

    result = run_with_spinner(add, 2, 3)
    assert result == 5