import argparse
import shutil
import sys
import time

from seawhirl._core.easing import get_easing_strategy
from seawhirl._core.presets import PRESETS
from seawhirl._lib.spinner import Spinner


def _build_parser() -> argparse.ArgumentParser:
    """Construct and configure the command-line argument parser."""
    def formatter(prog: str) -> argparse.HelpFormatter:
        """
        A custom help formatter to align help messages neatly based on
        the maximum argument width.
        """
        terminal_width = shutil.get_terminal_size().columns
        return argparse.RawDescriptionHelpFormatter(
            prog,
            max_help_position=24,
            width=terminal_width
        )

    command_lines = ['presets:']
    for name, frames in PRESETS.items():
        cleaned_frames = [f.strip() for f in frames[:5] if f.strip()]
        preview_frames = cleaned_frames[:4]

        if len(cleaned_frames) > 4:
            preview_frames.append('...')

        preview = ', '.join(preview_frames)
        command_lines.append(f'  {name} ({preview})')

    presets_description = (
        'Preview spinners directly in the terminal.\n\n' +
        '\n'.join(command_lines)
    )

    parser = argparse.ArgumentParser(
        usage='seawhirl [preset] [options]',
        description=presets_description,
        epilog='To access advanced physics, use the package API.',
        formatter_class=formatter
    )

    parser.add_argument(
        'preset',
        nargs='?',
        choices=list(PRESETS.keys()),
        default='whirl',
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        '--custom',
        metavar='<str>',
        help="custom frames separated by commas ('🚀,🪐,🛸')"
    )
    parser.add_argument(
        '--accel',
        type=float,
        default=3.0,
        metavar='<secs>',
        help='acceleration window in seconds'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=5.0,
        metavar='<secs>',
        help='total run time in seconds'
    )
    parser.add_argument(
        '--easing',
        choices=[
            'logarithmic',
            'log',
            'sinusoidal',
            'sin',
            'sine',
            'spring',
            'inertial'
        ],
        default='logarithmic',
        metavar='<curve>',
        help="easing curve ('logarithmic', 'sinusoidal', 'spring', 'inertial')"
    )
    parser.add_argument(
        '--text',
        dest='status_text',
        default='',
        metavar='<str>',
        help='status text to display next to the spinner'
    )
    parser.add_argument(
        '--oscillation',
        action='store_true',
        help='pulse the animation speed back and forth'
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.custom:
        frames = args.custom.split(',')
    else:
        frames = PRESETS[args.preset]

    easing_strategy = get_easing_strategy(args.easing)

    try:
        spinner = Spinner(
            accel_secs=args.accel,
            frames=frames,
            easing=easing_strategy,
            status_text=args.status_text,
            oscillation=args.oscillation,
        )
        with spinner:
            time.sleep(args.duration)
        print('Spinner finished.')
    except KeyboardInterrupt:
        print('\nSpinner terminated.')
        sys.exit(1)
