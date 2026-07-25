import math
import random
import sys
import time
import argparse

_SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
_NUM_FRAMES = len(_SPINNER_FRAMES)

def run_spinner(
    accel_secs: float,
    initial_fps: float,
    peak_fps: float,
    loop_delay: float
):
    current_frame = float(random.randint(0, _NUM_FRAMES - 1))
    last_rendered_idx = -1
    last_rendered_len = 0
    start_time = last_update_time = time.time()

    try:
        while True:
            now = time.time()
            elapsed_total = now - start_time
            elapsed_since_last = now - last_update_time
            last_update_time = now

            if elapsed_total < accel_secs:
                progress = elapsed_total / accel_secs
                log_progress = math.log10(1 + 9 * progress)
                current_fps = (
                    initial_fps + (peak_fps - initial_fps) * log_progress
                )
            else:
                current_fps = peak_fps

            current_frame += current_fps * elapsed_since_last
            current_frame_idx = int(current_frame) % _NUM_FRAMES

            if current_frame_idx != last_rendered_idx:
                char = _SPINNER_FRAMES[current_frame_idx]

                if last_rendered_idx == -1:
                    sys.stdout.write(char)
                else:
                    backspaces = '\b' * last_rendered_len
                    padding_spaces = ' ' * max(0, last_rendered_len - len(char))
                    back_padding = '\b' * len(padding_spaces)
                    sys.stdout.write(f'{backspaces}{char}{padding_spaces}{back_padding}')

                sys.stdout.flush()
                last_rendered_idx = current_frame_idx
                last_rendered_len = len(char)

            time.sleep(loop_delay)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--accel', type=float, required=True)
    parser.add_argument('--initial', type=float, required=True)
    parser.add_argument('--peak', type=float, required=True)
    parser.add_argument('--delay', type=float, required=True)
    args = parser.parse_args()

    run_spinner(args.accel, args.initial, args.peak, args.delay)
