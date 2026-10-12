"""Command-line argument parsing."""

import argparse
import shutil
import sys
import time

from seawhirl._cli.messages import (
    ACCEL_HELP_MSG,
    COLOR_HELP_MSG,
    CUSTOM_HELP_MSG,
    DURATION_HELP_MSG,
    EASING_HELP_MSG,
    EPILOG_MSG,
    ERROR_MSG,
    OSCILLATION_HELP_MSG,
    PRESETS_PREVIEW_MSG,
    PREVIEW_SPINNERS_MSG,
    SPINNER_FINISHED_MSG,
    SPINNER_TERMINATED_MSG,
    TEXT_HELP_MSG,
    USAGE_MSG,
)
from seawhirl._core.easing import EASING_REGISTRY, get_easing_strategy
from seawhirl._core.exceptions import SeawhirlError
from seawhirl._core.presets import PRESETS
from seawhirl._lib.spinner import Spinner


def _build_parser() -> argparse.ArgumentParser:
    """Construct and configure the command-line argument parser."""
    def formatter(prog: str) -> argparse.HelpFormatter:
        """Format help messages neatly based on maximum argument
        width.
        """
        terminal_width = shutil.get_terminal_size().columns
        return argparse.RawDescriptionHelpFormatter(
            prog,
            max_help_position=24,
            width=terminal_width
        )

    command_lines = [PRESETS_PREVIEW_MSG]
    for name, frames in PRESETS.items():
        cleaned_frames = [f.strip() for f in frames[:5] if f.strip()]
        preview_frames = cleaned_frames[:4]

        if len(cleaned_frames) > 4:
            preview_frames.append('...')

        preview = ', '.join(preview_frames)
        command_lines.append(f'  {name} ({preview})')

    presets_description = (
        PREVIEW_SPINNERS_MSG +
        '\n'.join(command_lines)
    )

    parser = argparse.ArgumentParser(
        usage=USAGE_MSG,
        description=presets_description,
        epilog=EPILOG_MSG,
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
        help=CUSTOM_HELP_MSG
    )
    parser.add_argument(
        '--accel',
        type=float,
        default=3.0,
        metavar='<secs>',
        help=ACCEL_HELP_MSG
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=5.0,
        metavar='<secs>',
        help=DURATION_HELP_MSG
    )
    parser.add_argument(
        '--easing',
        choices=list(EASING_REGISTRY),
        default='logarithmic',
        metavar='<curve>',
        help=EASING_HELP_MSG
    )
    parser.add_argument(
        '--text',
        dest='status_text',
        default='',
        metavar='<str>',
        help=TEXT_HELP_MSG
    )
    parser.add_argument(
        '--oscillation',
        action='store_true',
        help=OSCILLATION_HELP_MSG
    )
    parser.add_argument(
        '--color',
        default=None,
        metavar='<str>',
        help=COLOR_HELP_MSG,
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
            color=args.color,
        )
        with spinner:
            time.sleep(args.duration)
        print(SPINNER_FINISHED_MSG)
    except KeyboardInterrupt:
        print(SPINNER_TERMINATED_MSG)
        sys.exit(1)
    except SeawhirlError as e:
        print(ERROR_MSG.format(error=e), file=sys.stderr)
        sys.exit(1)
