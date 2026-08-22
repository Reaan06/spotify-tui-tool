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


class PlaybackState(str, Enum):
    """Truthful state of the local player transport."""

    FRESH = "fresh"
    STALE = "stale"
    STOPPED = "stopped"
    UNAVAILABLE = "unavailable"


class PlaybackFeedback(str, Enum):
    """Outcome of a playback command or row activation."""

    SUCCESS = "success"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"
    NOT_PLAYABLE = "not_playable"


@dataclass(frozen=True)
class PlaybackResult:
    """User-visible, retryable result from the player boundary."""

    feedback: PlaybackFeedback
    message: str
    retryable: bool = False

    @property
    def success(self) -> bool:
        return self.feedback is PlaybackFeedback.SUCCESS


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
    playback_state: PlaybackState = PlaybackState.STOPPED
    playback_message: str = ""

    @property
    def state(self) -> PlaybackState:
        """Short alias used by rendering and playback callers."""
        return self.playback_state

    def __post_init__(self) -> None:
        if (
            self.playback_state is PlaybackState.STOPPED
            and self.status is not PlaybackStatus.STOPPED
        ):
            self.playback_state = PlaybackState.FRESH


@dataclass
class ParsedURI:
    """A validated Spotify URI broken into its constituent parts."""

    type: str       # "track", "album", "playlist", "artist", "show", "episode"
    id: str         # 22-char base62 identifier
    uri: str        # full original URI: "spotify:track:…"


@dataclass(frozen=True)
class BrowseRow:
    """Identity-preserving row data rendered by browse surfaces.

    Display labels are deliberately separate from ``kind`` and ``id``.  A
    title can be duplicated or changed by a refresh without changing the
    identity used to map focus and selection back to the API payload.
    """

    kind: str
    id: str
    uri: str = ""
    title: str = ""
    subtitle: str = ""
    playable: bool = False
    detail: str = ""
    auxiliary: str = ""

    def __post_init__(self) -> None:
        kind = self.kind.strip().lower()
        identifier = self.id.strip()
        uri = self.uri.strip()
        if not identifier and uri:
            identifier = uri.rsplit(":", 1)[-1]
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "id", identifier)
        object.__setattr__(self, "uri", uri)

    @property
    def key(self) -> str:
        """Return the stable table key for this row."""
        return f"{self.kind}:{self.id}"

    @property
    def identity(self) -> tuple[str, str]:
        """Return the source type and identifier as a pair."""
        return self.kind, self.id

    @property
    def source_id(self) -> str:
        """Compatibility name for callers that prefer source terminology."""
        return self.id
