class SpinnerDefaults:
    ACCEL_SECS: float = 3.0
    INITIAL_FPS: float = 6.0
    MAX_RENDER_FPS: float = 60.0
    PEAK_ANIMATION_FPS: float = 120.0
    PRESET: str = 'braille'


PRESETS: dict[str, list[str]] = {
    'braille': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
    'dots': ['.  ', '.. ', '...', '   '],
    'line': ['-', '\\', '|', '/'],
    'arc': ['◜', '◠', '◝', '◞', '◡', '◟'],
    'bounce': ['⠁', '⠂', '⠄', '⠂'],
}
