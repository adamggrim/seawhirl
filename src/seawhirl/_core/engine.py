import random
import regex
import shutil
import time

from seawhirl._core.easing import EasingStrategy
from seawhirl._core.terminal import ANSI_MOVE_COLUMN
from seawhirl._core.utils import get_visual_width


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


class RenderEngine:
    """
    Manages spinner animation rendering.
    """
    def __init__(
        self,
        accel_secs: float,
        initial_fps: float,
        peak_fps: float,
        frames: list[str],
        easing: EasingStrategy,
        status_state: dict[str, str],
        status_frames: list[str],
        status_fps: float,
        oscillation: bool = False
    ) -> None:
        """
        Initialize the render engine with physics properties and frames.

        Args:
            accel_secs: The seconds to reach the maximum frames per
                second.
            initial_fps: The starting frames per second.
            peak_fps: The maximum frames per second.
            frames: A sequence of strings representing animation frames.
            easing: The easing model for the animation.
            status_state: A mutable dictionary for status text.
            status_frames: Frames attached to the end of status text.
            status_fps: Frames per second for the status text animation.
            oscillation: Whether to oscillate speed.
        """
        self.accel_secs = accel_secs
        self.initial_fps = initial_fps
        self.peak_fps = peak_fps
        self.frames = frames
        self.easing = easing
        self.oscillation = oscillation
        self.status_state = status_state
        self.status_frames = status_frames
        self.status_fps = status_fps

        self.num_frames = len(self.frames)
        self.num_status_frames = (
            len(self.status_frames) if self.status_frames else 1
        )
        self.max_frame_width = max(
            (get_visual_width(f) for f in self.frames), default=0
        )

        self.current_frame = float(random.randint(0, self.num_frames - 1))
        self.current_status_frame = 0.0

        self.prev_rendered_frame = ''
        self.start_time = time.time()
        self.prev_update_time = self.start_time

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
            self.accel_secs,
            self.initial_fps,
            self.peak_fps,
            self.easing,
            self.oscillation
        )

        self.current_frame += current_fps * elapsed_since_last
        current_frame_idx = int(self.current_frame) % self.num_frames

        self.current_status_frame += self.status_fps * elapsed_since_last
        status_frame_idx = (
            int(self.current_status_frame) % self.num_status_frames
        )

        icon = self.frames[current_frame_idx]
        console_width = max(
            1, shutil.get_terminal_size(fallback=(80, 24)).columns - 1
        )

        if get_visual_width(icon) > console_width:
            rendered_frame = ''
        else:
            text = self.status_state.get('status_text', '')
            suffix = (
                self.status_frames[status_frame_idx]
                if text and self.status_frames
                else ''
            )

            if text:
                full_text = f'{text}{suffix}'
                available_width = max(
                    0, console_width - (self.max_frame_width + 1)
                )

                if get_visual_width(full_text) > available_width:
                    truncated_text = ''
                    curr_w = 0

                    # Ensure complex emojis are never sliced in half.
                    graphemes = regex.findall(r'\X', full_text)

                    for cluster in graphemes:
                        cluster_w = get_visual_width(cluster)
                        if curr_w + cluster_w > available_width - 1:
                            truncated_text += '…'
                            break
                        truncated_text += cluster
                        curr_w += cluster_w

                    full_text = truncated_text

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
