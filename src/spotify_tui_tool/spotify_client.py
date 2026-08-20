"""SpotifyClient — unified service layer for all Spotify data.

Wraps PlayerController and NowPlaying to provide a single interface
for the UI layer.  Handles metadata, playback status, and stubs for
features not available via playerctl.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from spotify_tui_tool.exceptions import (
    PlaybackError,
    SpotifyNotRunningError,
)
from spotify_tui_tool.models import PlaybackStatus, TrackInfo
from spotify_tui_tool.now_playing import NowPlaying
from spotify_tui_tool.playerctl import PlayerController


@dataclass
class QueueEntry:
    """A simplified track entry for the queue display."""

    artist: str = ""
    title: str = ""
    duration_ms: int = 0


class SpotifyClient:
    """Unified data service for the TUI.

    Parameters:
        player: A PlayerController instance (or mock).
        poll_interval: Seconds between polls, forwarded to NowPlaying.
    """

    def __init__(
        self,
        player: Optional[PlayerController] = None,
        poll_interval: float = 1.0,
    ) -> None:
        self._player = player or PlayerController()
        self._now_playing = NowPlaying(player=self._player, poll_interval=poll_interval)

    @property
    def player(self) -> PlayerController:
        return self._player

    @property
    def now_playing(self) -> NowPlaying:
        return self._now_playing

    # ------------------------------------------------------------------
    # Playback controls (delegate to playerctl)
    # ------------------------------------------------------------------

    def play_pause(self) -> None:
        """Toggle play/pause."""
        self._player.play_pause()

    def next_track(self) -> None:
        """Skip to next track."""
        self._player.next()

    def previous_track(self) -> None:
        """Return to previous track."""
        self._player.previous()

    def get_volume(self) -> float:
        """Return current volume (0.0–1.0)."""
        return self._player.get_volume()

    def set_volume(self, level: float) -> None:
        """Set volume (0.0–1.0)."""
        self._player.set_volume(level)

    def seek(self, milliseconds: int) -> None:
        """Seek forward (positive) or backward (negative) by ms."""
        self._player.run("position", str(milliseconds))

    # ------------------------------------------------------------------
    # Data access
    # ------------------------------------------------------------------

    def poll(self) -> TrackInfo:
        """Poll playerctl for current track metadata.

        Returns the latest TrackInfo. On failure, returns the last known
        TrackInfo or an empty one.
        """
        return self._now_playing.poll_once()

    def get_current_track(self) -> TrackInfo:
        """Return the last-polled TrackInfo without hitting playerctl."""
        if self._now_playing._last_info is not None:
            return self._now_playing._last_info
        return TrackInfo()

    def get_status(self) -> PlaybackStatus:
        """Return the current playback status."""
        return self._player.get_status()

    # ------------------------------------------------------------------
    # Stubs for features not available via playerctl
    # ------------------------------------------------------------------

    def get_liked_songs(self) -> List[TrackInfo]:
        """Stub — liked songs are not available via playerctl."""
        return []

    def get_playlists(self) -> List[str]:
        """Stub — playlist browsing requires Spotify Web API."""
        return []

    def search(self, query: str) -> List[TrackInfo]:
        """Stub — search requires Spotify Web API."""
        return []

    def get_queue(self) -> List[QueueEntry]:
        """Return current track info for the queue view.

        playerctl does not expose the full queue; we show the current
        track as the only queue entry.
        """
        info = self.get_current_track()
        if not info.artist and not info.title:
            return []
        return [
            QueueEntry(
                artist=info.artist,
                title=info.title,
                duration_ms=info.duration_ms,
            )
        ]
