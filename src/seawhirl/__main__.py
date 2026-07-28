import argparse
import sys
import time

from .spinner import PRESETS, Spinner


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Run and test seawhirl spinner animations.'
    )

    parser.add_argument(
        '--mode',
        choices=list(PRESETS.keys()),
        default='braille',
        help='Select a built-in frame preset (default: braille)',
    )
    parser.add_argument(
        '--custom',
        type=str,
        default=None,
        help="Choose custom frames separated by commas (e.g., '🚀,🛸,🛰️')",
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
        help='Maximum frames per second (default 60.0)',
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

if __name__ == '__main__':
    main()
