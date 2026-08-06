import random
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
    state = status_state or {}
    s_frames = status_frames or ['']

    num_frames = len(frames)
    num_status_frames = len(s_frames)

    current_frame = float(random.randint(0, num_frames - 1))
    current_status_frame = 0.0

    prev_rendered_str = ''
    start_time = prev_update_time = time.time()

    try:
        while stop_event is None or not stop_event.is_set():
            now = time.time()
            elapsed_total = now - start_time
            elapsed_since_last = now - prev_update_time
            prev_update_time = now

            current_fps = _calculate_current_fps(
                elapsed_total, accel_secs, initial_fps, peak_fps, easing
            )

            current_frame += current_fps * elapsed_since_last
            current_frame_idx = int(current_frame) % num_frames

            current_status_frame += status_fps * elapsed_since_last
            status_frame_idx = int(current_status_frame) % num_status_frames

            icon = frames[current_frame_idx]
            text = state.get('status_text', '')
            suffix = s_frames[status_frame_idx] if text else ''

            display_str = f'{icon} {text}{suffix}' if text else icon

            if display_str != prev_rendered_str:
                char_width = max(0, wcswidth(display_str))
                prev_width = max(0, wcswidth(prev_rendered_str))

                if prev_rendered_str == '':
                    sys.stdout.write(display_str)
                else:
                    backspaces = '\b' * prev_width
                    padding_spaces = ' ' * max(0, prev_width - char_width)
                    back_padding = '\b' * len(padding_spaces)
                    sys.stdout.write(
                        f'{backspaces}{display_str}{padding_spaces}'
                        '{back_padding}'
                    )

                sys.stdout.flush()
                prev_rendered_str = display_str

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
