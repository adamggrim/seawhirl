from seawhirl._core.presets import PRESETS


def test_presets_is_dictionary() -> None:
    assert isinstance(PRESETS, dict)


def test_presets_contains_expected_keys() -> None:
    expected_keys = {
        'arc',
        'blink',
        'bounce',
        'dots',
        'line',
        'whirl'
    }
    assert expected_keys.issubset(PRESETS.keys())


def test_preset_frame_types_and_length() -> None:
    for name, frames in PRESETS.items():
        assert isinstance(name, str)
        assert isinstance(frames, list)
        assert len(frames) > 0

        for frame in frames:
            assert isinstance(frame, str)


def test_specific_preset_content() -> None:
    assert PRESETS['blink'] == ['█', '░']
    assert PRESETS['line'] == ['-', '\\', '|', '/']
