import argparse
import sys
import time

from seawhirl.constants import PRESETS
from seawhirl.spinner import Spinner
from seawhirl.easing import Logarithmic, Sinusoidal, Spring, Inertial


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
        choices=['logarithmic', 'sinusoidal', 'spring', 'inertial'],
        default='logarithmic',
        help=(
            'Physics easing curve '
            "('logarithmic', 'sinusoidal', 'spring', 'inertial')"
        ),
    )
    parser.add_argument(
        '--easing-base',
        type=float,
        default=10.0,
        help='Base for logarithmic easing (default: 10.0)',
    )
    parser.add_argument(
        '--easing-power',
        type=float,
        default=5.0,
        help='Exponent for inertial easing (default: 5.0)',
    )
    parser.add_argument(
        '--easing-tension',
        type=float,
        default=5.0,
        help='Tension factor for spring easing (default: 5.0)',
    )
    parser.add_argument(
        '--easing-friction',
        type=float,
        default=10.0,
        help='Friction factor for spring easing (default: 10.0)',
    )
    parser.add_argument(
        '--status-text',
        type=str,
        default='',
        help='Initial status text to display next to the spinner',
    )
    parser.add_argument(
        '--status-fps',
        type=float,
        default=2.0,
        help='Frames per second for the status text suffix (default: 2.0)',
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

    if args.easing == 'sinusoidal':
        easing_strategy = Sinusoidal()
    elif args.easing == 'spring':
        easing_strategy = Spring(
            tension=args.easing_tension, friction=args.easing_friction
        )
    elif args.easing == 'inertial':
        easing_strategy = Inertial(power=args.easing_power)
    else:
        easing_strategy = Logarithmic(base=args.easing_base)

    try:
        spinner = Spinner(
            accel_secs=args.accel,
            initial_fps=args.initial_fps,
            peak_animation_fps=args.peak_fps,
            frames=frames,
            easing=easing_strategy,
            status_text=args.status_text,
            status_fps=args.status_fps,
        )
        with spinner:
            time.sleep(args.duration)
        print('Completed.')
    except KeyboardInterrupt:
        print('\nAborted.')
        sys.exit(1)
