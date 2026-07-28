import json
import subprocess
import sys
from typing import Callable, Any

from .utils import is_supported_terminal

PRESETS: dict[str, list[str]] = {
    'braille': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
    'dots': ['.  ', '.. ', '...', '   '],
    'arc': ['◜', '◠', '◝', '◞', '◡', '◟'],
    'bounce': ['⠁', '⠂', '⠄', '⠂']
}

__all__ = ['Spinner', 'run_with_spinner', 'PRESETS']


class Spinner:
    def __init__(
        self,
        accel_secs: float = 3.0,
        initial_fps: float = 6.0,
        peak_animation_fps: float = 60.0,
        max_render_fps: float = 60.0,
        frames: list[str] | str | None = None,
        stream: Any | None = None
    ) -> None:
        self.accel_secs = accel_secs
        self.initial_fps = initial_fps
        self.peak_animation_fps = peak_animation_fps
        self.loop_delay = 1.0 / max_render_fps
        self.stream = stream or sys.stdout

        if isinstance(frames, str):
            if frames not in PRESETS:
                raise ValueError(
                    f"Unknown preset: '{frames}'. "
                    f'Available presets: {list(PRESETS.keys())}'
                )
            self.frames = PRESETS[frames]
        else:
            self.frames = frames or PRESETS['braille']

        self._disabled = not is_supported_terminal(self.stream)
        self._process: subprocess.Popen | None = None

    def _show_cursor(self) -> None:
        if not self._disabled:
            try:
                self.stream.write('\033[?25h')
                self.stream.flush()
            except (OSError, ValueError):
                pass

    def _hide_cursor(self) -> None:
        if not self._disabled:
            try:
                self.stream.write('\033[?25l')
                self.stream.flush()
            except (OSError, ValueError):
                pass

    def start(self) -> None:
        if self._disabled:
            return

        self._hide_cursor()

        # Spawn the isolated worker script.
        self._process = subprocess.Popen(
            [
                sys.executable, '-m', 'seawhirl._worker',
                '--accel', str(self.accel_secs),
                '--initial', str(self.initial_fps),
                '--peak', str(self.peak_animation_fps),
                '--delay', str(self.loop_delay),
                '--frames', json.dumps(self.frames)
            ],
            stdout=self.stream,
            stderr=subprocess.DEVNULL
        )

    def stop(self) -> None:
        if self._disabled or self._process is None:
            return

        self._process.terminate()
        self._process.wait()
        self._process = None
        self._show_cursor()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()

    def __call__(self, func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper

    def run(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        with self:
            return func(*args, **kwargs)


def run_with_spinner(func: Callable, *args: Any, **kwargs: Any) -> Any:
    spinner = Spinner()
    return spinner.run(func, *args, **kwargs)
