"""Strings for displaying CLI messages."""

from typing import Final

__all__ = [
    'ACCEL_HELP_MSG',
    'COLOR_HELP_MSG',
    'CUSTOM_HELP_MSG',
    'DURATION_HELP_MSG',
    'EASING_HELP_MSG',
    'EPILOG_MSG',
    'ERROR_MSG',
    'OSCILLATION_HELP_MSG',
    'PRESETS_PREVIEW_MSG',
    'PREVIEW_SPINNERS_MSG',
    'SPINNER_FINISHED_MSG',
    'SPINNER_TERMINATED_MSG',
    'TEXT_HELP_MSG',
    'USAGE_MSG'
]

ACCEL_HELP_MSG: Final = 'acceleration window in seconds'
COLOR_HELP_MSG: Final = (
    "color or comma-separated gradient ('red', 'red,blue', 'red,blue,green')"
)
CUSTOM_HELP_MSG: Final = "custom frames separated by commas ('🚀,🪐,🛸')"
DURATION_HELP_MSG: Final = 'total run time in seconds'
EASING_HELP_MSG: Final = (
    "easing curve ('logarithmic', 'sinusoidal', 'spring', 'inertial')"
)
EPILOG_MSG: Final = 'To access advanced physics, use the package API.'
ERROR_MSG: Final = 'Error: {error}'
OSCILLATION_HELP_MSG: Final = 'pulse the animation speed back and forth'
PRESETS_PREVIEW_MSG: Final = 'presets:'
PREVIEW_SPINNERS_MSG: Final = 'Preview spinners directly in the terminal.\n\n'
SPINNER_FINISHED_MSG: Final = 'Spinner finished.'
SPINNER_TERMINATED_MSG: Final = '\nSpinner terminated.'
TEXT_HELP_MSG: Final = 'status text to display next to the spinner'
USAGE_MSG: Final = 'seawhirl [preset] [options]'
