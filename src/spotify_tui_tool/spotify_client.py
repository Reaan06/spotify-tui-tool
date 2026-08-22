"""SpotifyClient — unified service layer for all Spotify data.

Wraps PlayerController and NowPlaying to provide a single interface
for the UI layer.  Handles metadata, playback status, and stubs for
features not available via playerctl.
"""

from __future__ import annotations

from typing import List, Optional

from spotify_tui_tool.exceptions import (
    PlaybackError,
    PlayerctlNotFoundError,
    SpotifyNotRunningError,
    playback_error_message,
)
from spotify_tui_tool.models import (
    BrowseRow,
    PlaybackFeedback,
    PlaybackResult,
    PlaybackStatus,
    TrackInfo,
)
from spotify_tui_tool.now_playing import NowPlaying
from spotify_tui_tool.playerctl import PlayerController
from spotify_tui_tool.ui.rows import activation_uri
from spotify_tui_tool.web_api import SpotifyWebAPI


class SpotifyClient:
    """Unified data service for the TUI.

    Parameters:
        player: A PlayerController instance (or mock).
        poll_interval: Seconds between polls, forwarded to NowPlaying.
        web_api: Optional SpotifyWebAPI instance for authenticated features.
    """

    def __init__(
        self,
        player: Optional[PlayerController] = None,
        poll_interval: float = 1.0,
        web_api: Optional[SpotifyWebAPI] = None,
    ) -> None:
        self._player = player or PlayerController()
        self._now_playing = NowPlaying(player=self._player, poll_interval=poll_interval)
        self._web_api = web_api

    @property
    def player(self) -> PlayerController:
        return self._player

    @property
    def now_playing(self) -> NowPlaying:
        return self._now_playing

    @property
    def web_api(self) -> Optional[SpotifyWebAPI]:
        return self._web_api

    @web_api.setter
    def web_api(self, api: SpotifyWebAPI) -> None:
        self._web_api = api

    @property
    def is_authenticated(self) -> bool:
        return self._web_api is not None

    # ------------------------------------------------------------------
    # Playback controls — playerctl/MPRIS is the sole transport authority
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
        """Seek relative to the current position using signed seconds."""
        seconds = milliseconds / 1000
        self._player.run("position", f"{seconds:+g}")

    def activate_row(self, row: BrowseRow) -> PlaybackResult:
        """Open a playable row through playerctl, preserving its URI exactly."""
        uri = activation_uri(row)
        if uri is None:
            return PlaybackResult(
                PlaybackFeedback.NOT_PLAYABLE,
                "This item cannot be played through the local player.",
            )
        try:
            self._player.open_uri(uri)
        except (PlayerctlNotFoundError, SpotifyNotRunningError) as exc:
            return PlaybackResult(
                PlaybackFeedback.UNAVAILABLE,
                playback_error_message(exc),
                retryable=True,
            )
        except PlaybackError as exc:
            return PlaybackResult(
                PlaybackFeedback.FAILED,
                playback_error_message(exc),
                retryable=True,
            )
        return PlaybackResult(PlaybackFeedback.SUCCESS, "Playback started via the local player.")

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
    # Web API features — authenticated access
    # ------------------------------------------------------------------

    def get_liked_songs(self) -> List[TrackInfo]:
        """Return liked songs via Web API, or empty list if not authenticated."""
        if not self._web_api:
            return []
        items = self._web_api.get_liked_songs(limit=50)
        return [
            TrackInfo(
                artist=", ".join(a["name"] for a in t.get("track", {}).get("artists", [])),
                title=t.get("track", {}).get("name", ""),
                album=t.get("track", {}).get("album", {}).get("name", ""),
                track_id=t.get("track", {}).get("id", ""),
                duration_ms=t.get("track", {}).get("duration_ms", 0),
            )
            for t in items
        ]

    def get_playlists(self) -> List[str]:
        """Return playlist names via Web API, or empty list if not authenticated."""
        if not self._web_api:
            return []
        items = self._web_api.get_playlists()
        return [p.get("name", "") for p in items]

    def search(self, query: str) -> List[TrackInfo]:
        """Search tracks via Web API, or empty list if not authenticated."""
        if not self._web_api:
            return []
        data = self._web_api.search(query, types="track")
        tracks = data.get("tracks", {}).get("items", [])
        return [
            TrackInfo(
                artist=", ".join(a["name"] for a in t.get("artists", [])),
                title=t.get("name", ""),
                album=t.get("album", {}).get("name", ""),
                track_id=t.get("id", ""),
                duration_ms=t.get("duration_ms", 0),
            )
            for t in tracks
        ]
