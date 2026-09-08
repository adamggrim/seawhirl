import math
import pytest

from seawhirl._core.easing import (
    EASING_REGISTRY,
    Inertial,
    Logarithmic,
    MINIMUM_SAFE_BASE,
    Sinusoidal,
    Spring,
    get_easing_strategy,
)


class TestLogarithmic:
    @pytest.mark.parametrize('progress, expected', [
        (0.0, 0.0),
        (1.0, 1.0),
    ])
    def test_bounds(self, progress: float, expected: float) -> None:
        easing = Logarithmic(base=10.0)
        assert easing.calculate_multiplier(progress) == pytest.approx(expected)

    def test_midpoint(self) -> None:
        easing = Logarithmic(base=10.0)
        expected = math.log(5.5, 10.0)
        assert easing.calculate_multiplier(0.5) == pytest.approx(expected)

    def test_minimum_safe_base_override(self) -> None:
        easing = Logarithmic(base=0.5)

        result = easing.calculate_multiplier(0.5)
        expected = math.log(
            1 + (MINIMUM_SAFE_BASE - 1) * 0.5,
            MINIMUM_SAFE_BASE
        )

        assert result == pytest.approx(expected)


class TestSinusoidal:
    @pytest.mark.parametrize('progress, expected', [
        (0.0, 0.0),
        (0.5, 0.5),
        (1.0, 1.0),
    ])
    def test_curve_points(self, progress: float, expected: float) -> None:
        easing = Sinusoidal()
        assert easing.calculate_multiplier(progress) == pytest.approx(expected)


class TestSpring:
    def test_initial_state(self) -> None:
        easing = Spring(tension=5.0, friction=10.0)
        assert easing.calculate_multiplier(0.0) == pytest.approx(0.0)

    def test_overshoot_oscillation(self) -> None:
        easing = Spring(tension=1.0, friction=math.pi)

        expected = 1 - (math.exp(-1.0) * math.cos(math.pi))
        assert easing.calculate_multiplier(1.0) == pytest.approx(expected)


class TestInertial:
    @pytest.mark.parametrize('progress, power, expected', [
        (0.0, 5.0, 0.0),
        (1.0, 5.0, 1.0),
        (0.5, 2.0, 0.25),
        (0.5, 3.0, 0.125),
    ])
    def test_power_curve_points(
        self,
        progress: float,
        power: float,
        expected: float
    ) -> None:
        easing = Inertial(power=power)
        assert easing.calculate_multiplier(progress) == pytest.approx(expected)


class TestFactory:
    @pytest.mark.parametrize('name, expected_type', [
        ('inertial', Inertial),
        ('log', Logarithmic),
        ('logarithmic', Logarithmic),
        ('sin', Sinusoidal),
        ('sine', Sinusoidal),
        ('sinusoidal', Sinusoidal),
        ('spring', Spring),
    ])
    def test_get_easing_strategy_types(
        self,
        name: str,
        expected_type: type
    ) -> None:
        strategy = get_easing_strategy(name)
        assert isinstance(strategy, expected_type)

    def test_invalid_strategy_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            get_easing_strategy('invalid_curve_name')

    def test_registry_completeness(self) -> None:
        expected_keys = {
            'inertial', 'log', 'logarithmic',
            'sin', 'sine', 'sinusoidal', 'spring'
        }
        assert set(EASING_REGISTRY.keys()) == expected_keys
