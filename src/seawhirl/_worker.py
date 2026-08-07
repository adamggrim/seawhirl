import random
import shutil
import sys
import threading
import time

from wcwidth import wcswidth

from seawhirl.easing import EasingStrategy


def _calculate_current_fps(
    elapsed_total: float,
    accel_secs: float,
    initial_fps: float,
    peak_fps: float,
    easing: EasingStrategy
) -> float:
    if elapsed_total >= accel_secs:
        return peak_fps

    progress = elapsed_total / accel_secs
    multiplier = easing.calculate_multiplier(progress)

    return initial_fps + (peak_fps - initial_fps) * multiplier


class RenderEngine:
    def __init__(
        self,
        accel_secs: float,
        initial_fps: float,
        peak_fps: float,
        frames: list[str],
        easing: EasingStrategy,
        status_state: dict[str, str],
        status_frames: list[str],
        status_fps: float
    ) -> None:
        self.accel_secs = accel_secs
        self.initial_fps = initial_fps
        self.peak_fps = peak_fps
        self.frames = frames
        self.easing = easing
        self.status_state = status_state
        self.status_frames = status_frames
        self.status_fps = status_fps

        self.num_frames = len(self.frames)
        self.num_status_frames = (
            len(self.status_frames) if self.status_frames else 1
        )
        self.max_frame_width = max(
            (max(0, wcswidth(f)) for f in self.frames), default=0
        )

        self.current_frame = float(random.randint(0, self.num_frames - 1))
        self.current_status_frame = 0.0

        self.prev_rendered_str = ''
        self.start_time = time.time()
        self.prev_update_time = self.start_time

    def tick(self, now: float) -> str | None:
        elapsed_total = now - self.start_time
        elapsed_since_last = now - self.prev_update_time
        self.prev_update_time = now

        current_fps = _calculate_current_fps(
            elapsed_total,
            self.accel_secs,
            self.initial_fps,
            self.peak_fps,
            self.easing
        )

        self.current_frame += current_fps * elapsed_since_last
        current_frame_idx = int(self.current_frame) % self.num_frames

        self.current_status_frame += self.status_fps * elapsed_since_last
        status_frame_idx = (
            int(self.current_status_frame) % self.num_status_frames
        )

        icon = self.frames[current_frame_idx]
        text = self.status_state.get('status_text', '')
        suffix = (
            self.status_frames[status_frame_idx]
            if text and self.status_frames
            else ''
        )

        if text:
            icon_width = max(0, wcswidth(icon))
            padding = ' ' * (self.max_frame_width - icon_width)
            display_str = f'{icon}{padding} {text}{suffix}'
        else:
            display_str = icon

        if display_str != self.prev_rendered_str:
            console_width = max(10, shutil.get_terminal_size().columns - 1)

            if wcswidth(display_str) > console_width:
                display_str = display_str[:console_width - 2] + '…'

            self.prev_rendered_str = display_str
            return display_str

        return None


def run_spinner(
    accel_secs: float,
    initial_fps: float,
    peak_fps: float,
    loop_delay: float,
    frames: list[str],
    easing: EasingStrategy,
    stop_event: threading.Event | None = None,
    status_state: dict[str, str] | None = None,
    status_frames: list[str] | None = None,
    status_fps: float = 2.0
) -> None:
    engine = RenderEngine(
        accel_secs,
        initial_fps,
        peak_fps,
        frames,
        easing,
        status_state or {},
        status_frames or [''],
        status_fps
    )

    try:
        while stop_event is None or not stop_event.is_set():
            now = time.time()
            display_str = engine.tick(now)

            if display_str is not None:
                sys.stdout.write(f'\r\033[K{display_str}')
                sys.stdout.flush()

            work_time = time.time() - now
            time.sleep(max(0.0, loop_delay - work_time))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        sys.stderr.write(f'\nSpinner worker encountered an error: {e}\n')
        sys.stderr.flush()
    finally:
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()
