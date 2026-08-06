import math
import random
import sys
import threading
import time

from wcwidth import wcswidth


def _calculate_current_fps(
    elapsed_total: float,
    accel_secs: float,
    initial_fps: float,
    peak_fps: float,
    easing: str
) -> float:
    if elapsed_total >= accel_secs:
        return peak_fps

    progress = elapsed_total / accel_secs

    if easing == 'sinusoidal':
        multiplier = 0.5 * (1 - math.cos(math.pi * progress))
    elif easing == 'spring':
        multiplier = 1 - math.exp(-5 * progress) * math.cos(10 * progress)
    elif easing == 'inertial':
        multiplier = math.pow(progress, 5)
    else:
        multiplier = math.log10(1 + 9 * progress)

    return initial_fps + (peak_fps - initial_fps) * multiplier


def run_spinner(
    accel_secs: float,
    initial_fps: float,
    peak_fps: float,
    loop_delay: float,
    frames: list[str],
    easing: str,
    stop_event: threading.Event | None = None
) -> None:
    num_frames = len(frames)
    current_frame = float(random.randint(0, num_frames - 1))
    prev_rendered_idx = -1
    prev_rendered_len = 0
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

            if current_frame_idx != prev_rendered_idx:
                char = frames[current_frame_idx]
                char_width = max(0, wcswidth(char))

                if prev_rendered_idx == -1:
                    sys.stdout.write(char)
                else:
                    backspaces = '\b' * prev_rendered_len
                    padding_spaces = ' ' * max(0, prev_rendered_len - char_width)
                    back_padding = '\b' * len(padding_spaces)
                    sys.stdout.write(
                        f'{backspaces}{char}{padding_spaces}{back_padding}'
                    )

                sys.stdout.flush()
                prev_rendered_idx = current_frame_idx
                prev_rendered_len = char_width

            time.sleep(loop_delay)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        sys.stderr.write(f'\nSpinner worker encountered an error: {e}\n')
        sys.stderr.flush()
    finally:
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()
