"""NowPlaying — metadata polling, parsing, and state management.

Phase 4 of the MVP.  Polls playerctl for current track metadata,
parses the format string, and detects track changes.

Design (from exploration.md):
    NowPlaying.poll_once()   → TrackInfo (pure read, no side effects)
    NowPlaying.track_changed → bool (reset on read)
    NowPlaying.connection_lost → bool (5+ consecutive failures)
"""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Optional

from spotify_tui_tool.exceptions import (
    PlaybackError,
    PlayerctlNotFoundError,
    SpotifyNotRunningError,
    playback_error_message,
)
from spotify_tui_tool.models import PlaybackState, PlaybackStatus, TrackInfo


# ------------------------------------------------------------------
# Pure parsing helpers
# ------------------------------------------------------------------

def parse_position(raw: str) -> int:
    """Convert a playerctl position string (seconds with decimal) to ms."""
    try:
        return int(float(raw) * 1000)
    except (ValueError, TypeError):
        return 0


def parse_volume(raw: str) -> float:
    """Convert a playerctl volume string (0.0–1.0) to float."""
    try:
        return float(raw)
    except (ValueError, TypeError):
        return 0.0


def parse_duration(raw: str) -> int:
    """Convert mpris:length (microseconds) to milliseconds."""
    try:
        return int(int(raw) / 1000)
    except (ValueError, TypeError):
        return 0


def extract_track_id(url_or_path: str) -> str:
    """Extract the 22-char base62 track ID from a URL or MPRIS path."""
    # Try URL pattern first
    match = re.search(r"open\.spotify\.com/track/([a-zA-Z0-9]{22})", url_or_path)
    if match:
        return match.group(1)
    # Try MPRIS path pattern
    match = re.search(r"/track/([a-zA-Z0-9]{22})", url_or_path)
    if match:
        return match.group(1)
    return ""


def build_track_info(metadata: str, position_raw: str, status_raw: str) -> TrackInfo:
    """Parse the playerctl format output into a TrackInfo.

    The metadata format is:
        artist|title|album|duration_us|volume|url

    Fields may be empty.
    """
    parts = metadata.split("|")
    # Pad to at least 6 fields
    while len(parts) < 6:
        parts.append("")

    artist = parts[0]
    title = parts[1]
    album = parts[2]
    duration_ms = parse_duration(parts[3])
    volume = parse_volume(parts[4])
    url_or_path = parts[5]
    track_id = extract_track_id(url_or_path)
    position_ms = parse_position(position_raw)

    try:
        status = PlaybackStatus.from_playerctl(status_raw)
    except ValueError:
        status = PlaybackStatus.STOPPED

    return TrackInfo(
        artist=artist,
        title=title,
        album=album,
        track_id=track_id,
        duration_ms=duration_ms,
        position_ms=position_ms,
        volume=volume,
        status=status,
        playback_state=(
            PlaybackState.STOPPED
            if status is PlaybackStatus.STOPPED
            else PlaybackState.FRESH
        ),
    )


# ------------------------------------------------------------------
# NowPlaying class
# ------------------------------------------------------------------

# Metadata format string for playerctl
METADATA_FORMAT = "{{artist}}|{{title}}|{{album}}|{{mpris:length}}|{{volume}}|{{mpris:artUrl}}"

# Minimum poll interval in seconds (500ms)
MIN_POLL_INTERVAL = 0.5

# Connection-lost threshold (consecutive failures)
CONNECTION_LOST_THRESHOLD = 5

# A retained track becomes stale only after two missed one-second polls.
STALE_THRESHOLD = 2


class NowPlaying:
    """Manages current-track state by polling playerctl.

    Parameters:
        player: A PlayerController instance (or mock for testing).
        poll_interval: Seconds between polls.  Clamped to >= 0.5.
    """

    def __init__(self, player, poll_interval: float = 1.0) -> None:
        self._player = player
        self._poll_interval = max(poll_interval, MIN_POLL_INTERVAL)
        self._last_info: Optional[TrackInfo] = None
        self._track_changed: bool = False
        self._failure_count: int = 0
        self._connection_lost: bool = False

    @property
    def poll_interval(self) -> float:
        return self._poll_interval

    @property
    def track_changed(self) -> bool:
        """True if the last poll detected a new track.  Resets on read."""
        value = self._track_changed
        self._track_changed = False
        return value

    @property
    def connection_lost(self) -> bool:
        return self._connection_lost

    def _poll_failure(self, error: Exception) -> TrackInfo:
        self._failure_count += 1
        if self._failure_count >= CONNECTION_LOST_THRESHOLD:
            self._connection_lost = True
        message = playback_error_message(error)
        if self._last_info is not None:
            if self._failure_count < STALE_THRESHOLD:
                return self._last_info
            self._last_info = replace(
                self._last_info,
                playback_state=PlaybackState.STALE,
                playback_message=message,
            )
            return self._last_info
        return TrackInfo(
            playback_state=PlaybackState.UNAVAILABLE,
            playback_message=message,
        )

    def poll_once(self) -> TrackInfo:
        """Execute one poll cycle and return the current TrackInfo.

        On the first missed poll, returns the last-known TrackInfo unchanged;
        after two consecutive misses, it marks retained context as stale.
        On track change, sets the track_changed flag.
        """
        try:
            metadata = self._player.run("metadata", "--format", METADATA_FORMAT)
            position_raw = self._player.run("position")
            status_raw = self._player.run("status")
        except (PlayerctlNotFoundError, SpotifyNotRunningError, PlaybackError) as exc:
            return self._poll_failure(exc)
        except Exception as exc:
            return self._poll_failure(exc)

        # Successful poll — reset failure state
        self._failure_count = 0
        self._connection_lost = False

        info = build_track_info(metadata, position_raw, status_raw)

        # Detect track change
        if self._last_info is not None:
            if (info.artist, info.title) != (self._last_info.artist, self._last_info.title):
                self._track_changed = True

        self._last_info = info
        return info
