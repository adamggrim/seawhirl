import random
import regex
import shutil
import time

from seawhirl._core.config import SpinnerConfig
from seawhirl._core.easing import EasingStrategy
from seawhirl._core.state import SpinnerState
from seawhirl._core.terminal import ANSI_MOVE_COLUMN
from seawhirl._core.utils import get_visual_width

DEFAULT_TERMINAL_SIZE = (80, 24)


def _calculate_current_fps(
    elapsed_total: float,
    accel_secs: float,
    initial_fps: float,
    peak_fps: float,
    easing: EasingStrategy,
    oscillation: bool = False
) -> float:
    """
    Determine the current frames per second based on the easing
    strategy.

    Args:
        elapsed_total: The time elapsed since rendering started.
        accel_secs: The seconds to reach the maximum frames per second.
        initial_fps: The starting frames per second.
        peak_fps: The maximum frames per second.
        easing: The easing model for the animation.
        oscillation: Whether to oscillate speed.

    Returns:
        float: The calculated frames per second for this tick.
    """
    if not oscillation and elapsed_total >= accel_secs:
        return peak_fps

    if oscillation:
        cycle = (elapsed_total / accel_secs) % 2.0
        progress = cycle if cycle <= 1.0 else 2.0 - cycle
    else:
        progress = elapsed_total / accel_secs

    multiplier = easing.calculate_multiplier(progress)

    return initial_fps + (peak_fps - initial_fps) * multiplier


def _truncate_text(text: str, max_width: int) -> str:
    """
    Truncate text to visual width while respecting grapheme boundaries.
    """
    truncated_text = ''
    current_width = 0

    # Ensure complex emojis remain intact.
    graphemes = regex.findall(r'\X', text)

    for cluster in graphemes:
        cluster_width = get_visual_width(cluster)
        if current_width + cluster_width > max_width - 1:
            truncated_text += '...'
            break
        truncated_text += cluster
        current_width += cluster_width

    return truncated_text


class RenderEngine:
    """Manages spinner animation rendering."""
    def __init__(
        self,
        config: SpinnerConfig,
        state: SpinnerState
    ) -> None:
        """
        Initialize the render engine with configuration and state.

        Args:
            config: Static animation configuration parameters.
            state: Mutable state for the spinner.
        """
        self.config = config
        self.state = state

        self.num_frames = len(self.config.frames)
        self.num_status_frames = (
            len(self.config.status_frames) if self.config.status_frames else 1
        )
        self.max_frame_width = max(
            (get_visual_width(f) for f in self.config.frames), default=0
        )

        self.current_frame = float(random.randint(0, self.num_frames - 1))
        self.current_status_frame = 0.0

        self.prev_rendered_frame = ''
        self.start_time = time.time()
        self.prev_update_time = self.start_time
        self._text_cache: tuple[tuple[str, int] | None, str] = (None, '')

    def tick(self, now: float) -> str | None:
        """
        Animate based on elapsed time.

        Args:
            now: The current timestamp in seconds.

        Returns:
            str | None: An ANSI-formatted string representing the
                current text, or `None` if the output is unchanged.
        """
        elapsed_total = now - self.start_time
        elapsed_since_last = now - self.prev_update_time
        self.prev_update_time = now

        current_fps = _calculate_current_fps(
            elapsed_total,
            self.config.accel_secs,
            self.config.initial_fps,
            self.config.peak_animation_fps,
            self.config.easing,
            self.config.oscillation
        )

        self.current_frame += current_fps * elapsed_since_last
        current_frame_idx = int(self.current_frame) % self.num_frames

        self.current_status_frame += (
            self.config.status_fps * elapsed_since_last
        )
        status_frame_idx = (
            int(self.current_status_frame) % self.num_status_frames
        )

        icon = self.config.frames[current_frame_idx]
        console_width = max(
            1, shutil.get_terminal_size(
                fallback=DEFAULT_TERMINAL_SIZE
            ).columns - 1
        )

        if get_visual_width(icon) > console_width:
            rendered_frame = ''
        else:
            text = self.state.status_text
            suffix = (
                self.config.status_frames[status_frame_idx]
                if text and self.config.status_frames
                else ''
            )

            if text:
                full_text = f'{text}{suffix}'
                available_width = max(
                    0, console_width - (self.max_frame_width + 1)
                )
                cache_key = (full_text, available_width)

                if self._text_cache[0] == cache_key:
                    full_text = self._text_cache[1]
                elif get_visual_width(full_text) > available_width:
                    truncated_text = _truncate_text(full_text, available_width)
                    self._text_cache = (cache_key, truncated_text)
                    full_text = truncated_text
                else:
                    self._text_cache = (cache_key, full_text)

                rendered_frame = (
                    f'{icon}'
                    f'{ANSI_MOVE_COLUMN.format(col=self.max_frame_width + 2)}'
                    f'{full_text}'
                )
            else:
                rendered_frame = icon

        if rendered_frame != self.prev_rendered_frame:
            self.prev_rendered_frame = rendered_frame
            return rendered_frame

        return None
