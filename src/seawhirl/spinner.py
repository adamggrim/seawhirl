import subprocess
import sys
from typing import Callable, Any

__all__ = ['Spinner', 'run_with_spinner']

class Spinner:
    def __init__(
        self,
        accel_secs: float = 3.0,
        initial_fps: float = 6.0,
        peak_animation_fps: float = 120.0,
        max_render_fps: float = 60.0
    ) -> None:
        self.accel_secs = accel_secs
        self.initial_fps = initial_fps
        self.peak_animation_fps = peak_animation_fps
        self.loop_delay = 1.0 / max_render_fps

        is_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        is_utf8 = getattr(sys.stdout, 'encoding', '').lower() in ('utf-8', 'utf8')
        self._disabled = not (is_tty and is_utf8)
        self._process: subprocess.Popen | None = None

    def _show_cursor(self) -> None:
        if not self._disabled:
            try:
                sys.stdout.write('\033[?25h')
                sys.stdout.flush()
            except (OSError, ValueError):
                pass

    def _hide_cursor(self) -> None:
        if not self._disabled:
            try:
                sys.stdout.write('\033[?25l')
                sys.stdout.flush()
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
                '--delay', str(self.loop_delay)
            ],
            stdout=sys.stdout,
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
