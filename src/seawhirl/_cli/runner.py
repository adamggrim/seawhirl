import argparse
import sys
import time

from seawhirl.constants import PRESETS
from seawhirl.spinner import Spinner, Easing


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            'Run and test seawhirl spinner animations in the terminal.'
        )
    )

    parser.add_argument(
        '--mode',
        choices=list(PRESETS.keys()),
        default='whirl',
        help=(
            "Select a built-in frame preset ('whirl', 'dots', 'line', 'arc' "
            "or 'bounce')"
        ),
    )
    parser.add_argument(
        '--custom',
        type=str,
        default=None,
        help=(
            "Custom frames separated by commas (e.g., '.  ,.. ,...', or "
            "'🚀,🛸,🛰️')"
        ),
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=5.0,
        help='Total run time in seconds (default: 5.0)',
    )
    parser.add_argument(
        '--accel',
        type=float,
        default=3.0,
        help='Acceleration window in seconds (default: 3.0)',
    )
    parser.add_argument(
        '--initial-fps',
        type=float,
        default=6.0,
        help='Starting frames per second (default: 6.0)',
    )
    parser.add_argument(
        '--peak-fps',
        type=float,
        default=120.0,
        help='Peak frames per second (default: 120.0)',
    )
    parser.add_argument(
        '--easing',
        choices=[e.value for e in Easing],
        default='logarithmic',
        help=(
            'Physics easing curve '
            "('logarithmic', 'sinusoidal', 'spring', 'inertial')"
        ),
    )

    args = parser.parse_args()

    if args.custom:
        frames = args.custom.split(',')
    else:
        frames = PRESETS[args.mode]

    print(
        f"Spinning mode='{args.custom and 'custom' or args.mode}' "
        f'for {args.duration}s (accel: {args.accel}s)...'
    )

    try:
        spinner = Spinner(
            accel_secs=args.accel,
            initial_fps=args.initial_fps,
            peak_animation_fps=args.peak_fps,
            frames=frames,
        )
        with spinner:
            time.sleep(args.duration)
        print('Completed.')
    except KeyboardInterrupt:
        print('\nAborted.')
        sys.exit(1)
