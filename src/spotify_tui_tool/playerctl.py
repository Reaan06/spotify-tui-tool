"""PlayerController — a thin wrapper around the ``playerctl`` subprocess.

Every public method maps 1:1 to a playerctl command.  Errors are translated
into typed exceptions so callers never have to parse stderr themselves.

The design follows the exploration.md architecture:
    PlayerController.run(*args) -> str   # subprocess wrapper
    PlayerController.play/pause/next/...   # transport controls
    PlayerController.get_volume/set_volume   # volume control
    PlayerController.get_status             # status -> PlaybackStatus
"""

from __future__ import annotations

import subprocess

from spotify_tui_tool.exceptions import (
    PlayerctlNotFoundError,
    SpotifyNotRunningError,
    PlaybackError,
)
from spotify_tui_tool.models import PlaybackStatus


class PlayerController:
    """Wraps ``playerctl`` subprocess calls for a single MPRIS player.

    Parameters:
        player_name: The MPRIS player identifier (default ``spotify``).
    """

    def __init__(self, player_name: str = "spotify") -> None:
        self.player_name = player_name

    # ------------------------------------------------------------------
    # Low-level subprocess runner
    # ------------------------------------------------------------------

    def run(self, *args: str) -> str:
        """Execute ``playerctl --player=<name> <args>`` and return stdout.

        Raises:
            PlayerctlNotFoundError: Binary not on $PATH.
            SpotifyNotRunningError: No MPRIS player matching *player_name*.
            PlaybackError: Any other non-zero exit code.
        """
        cmd = ["playerctl", f"--player={self.player_name}", *args]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            raise PlayerctlNotFoundError()

        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "No players found" in stderr or "No player" in stderr:
                raise SpotifyNotRunningError()
            raise PlaybackError(stderr or "playerctl command failed", stderr)

        return result.stdout.strip()

    # ------------------------------------------------------------------
    # Transport controls
    # ------------------------------------------------------------------

    def play(self) -> None:
        """Start playback."""
        self.run("play")

    def pause(self) -> None:
        """Pause playback."""
        self.run("pause")

    def play_pause(self) -> None:
        """Toggle between play and pause."""
        self.run("play-pause")

    def next(self) -> None:
        """Skip to the next track."""
        self.run("next")

    def previous(self) -> None:
        """Return to the previous track."""
        self.run("previous")

    def open_uri(self, uri: str) -> None:
        """Open a Spotify URI via ``playerctl open``."""
        self.run("open", uri)

    # ------------------------------------------------------------------
    # Volume control
    # ------------------------------------------------------------------

    def get_volume(self) -> float:
        """Return the current volume as a float in [0.0, 1.0]."""
        return float(self.run("volume"))

    def set_volume(self, level: float) -> None:
        """Set the volume.

        Raises:
            ValueError: If *level* is outside the range [0.0, 1.0].
        """
        if not 0.0 <= level <= 1.0:
            raise ValueError("Volume must be between 0.0 and 1.0")
        self.run("volume", str(level))

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> PlaybackStatus:
        """Return the current playback status as a :class:`PlaybackStatus`."""
        return PlaybackStatus.from_playerctl(self.run("status"))
