"""Data models for the Spotify TUI Tool.

All models are plain dataclasses / enums so they can be constructed and
asserted against in unit tests without any external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PlaybackStatus(Enum):
    """Mirrors the three states playerctl ``--status`` can return."""

    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"

    @classmethod
    def from_playerctl(cls, raw: str) -> "PlaybackStatus":
        """Convert a playerctl status string (``"Playing"``, ``"Paused"``,
        ``"Stopped"``) to the corresponding enum member.

        Raises ``ValueError`` if *raw* does not match any known status.
        """
        mapping = {
            "Playing": cls.PLAYING,
            "Paused": cls.PAUSED,
            "Stopped": cls.STOPPED,
        }
        if raw not in mapping:
            raise ValueError(f"Unknown playback status: {raw!r}")
        return mapping[raw]


@dataclass
class TrackInfo:
    """Current-track metadata returned by ``playerctl metadata``.

    All text fields default to an empty string and numeric fields to ``0``
    so that a stopped/idle player produces a valid (if empty) object rather
    than ``None`` checks littered throughout the UI code.
    """

    artist: str = ""
    title: str = ""
    album: str = ""
    track_id: str = ""
    duration_ms: int = 0
    position_ms: int = 0
    volume: float = 0.0
    status: PlaybackStatus = PlaybackStatus.STOPPED


@dataclass
class ParsedURI:
    """A validated Spotify URI broken into its constituent parts."""

    type: str       # "track", "album", "playlist", "artist", "show", "episode"
    id: str         # 22-char base62 identifier
    uri: str        # full original URI: "spotify:track:…"
