"""App state manager — global application state.

Phase 1 of spotatui integration.  Manages the current view, sidebar
selection, playback state, and other UI state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from spotify_tui_tool.models import BrowseRow, TrackInfo


class BrowseStatus(str, Enum):
    """Terminal and in-flight states exposed by every browse surface."""

    LOADING = "loading"
    SUCCESS = "success"
    EMPTY = "empty"
    ERROR = "error"
    STALE = "stale"


@dataclass
class BrowseSurfaceState:
    """State for one independently refreshable browse surface."""

    status: BrowseStatus = BrowseStatus.EMPTY
    rows: List[BrowseRow] = field(default_factory=list)
    message: str = ""
    retryable: bool = False
    generation: int = 0
    view_id: str = ""


@dataclass
class AppState:
    """Global application state.
    
    This is the single source of truth for all UI state.
    Components read from and write to this state.
    """
    
    # Current view
    current_view: str = "home"
    
    # Sidebar selection
    sidebar_section: str = "library"  # sources, library, playlists
    sidebar_index: int = 0
    
    # Playback state
    is_playing: bool = False
    current_track: Optional[TrackInfo] = None
    volume: float = 0.5
    shuffle: bool = False
    repeat_mode: str = "off"  # off, track, all
    
    # Search state
    search_query: str = ""
    search_results: List[TrackInfo] = field(default_factory=list)

    # Authentication and read-only browse state
    auth_state: str = "unauthenticated"
    auth_user: Optional[dict] = None
    auth_reason: str = ""
    browse: Dict[str, BrowseSurfaceState] = field(default_factory=dict)
    
    # History
    history: List[str] = field(default_factory=list)  # URIs

    # Shell interaction
    focus_region: str = "sidebar"  # sidebar, content, playbar
    transient_view: Optional[str] = None
    view_history: List[str] = field(default_factory=list)
    api_pending: bool = False

    def __post_init__(self) -> None:
        for surface in ("library", "playlists", "search"):
            self.browse.setdefault(surface, BrowseSurfaceState())
    
    def set_view(self, view: str) -> None:
        """Switch to a different view."""
        valid_views = {
            "home", "library", "playlists", "search", "settings", "help", "login"
        }
        if view in valid_views:
            self.current_view = view

    def set_auth_state(
        self,
        state: str,
        *,
        user: Optional[dict] = None,
        reason: str = "",
    ) -> None:
        self.auth_state = state
        self.auth_user = user
        self.auth_reason = reason

    def _surface(self, name: str) -> BrowseSurfaceState:
        return self.browse.setdefault(name, BrowseSurfaceState())

    def begin_browse(self, surface: str, view_id: str) -> int:
        """Start a request and return its monotonically increasing generation."""
        current = self._surface(surface)
        current.generation += 1
        current.view_id = view_id
        current.status = BrowseStatus.LOADING
        current.message = ""
        current.retryable = False
        return current.generation

    def _request_is_current(self, surface: str, generation: int, view_id: str) -> bool:
        current = self._surface(surface)
        return current.generation == generation and current.view_id == view_id

    def accept_browse_result(
        self,
        surface: str,
        generation: int,
        view_id: str,
        rows: List[BrowseRow],
    ) -> bool:
        """Accept only the newest response for the still-active view."""
        if not self._request_is_current(surface, generation, view_id):
            return False
        current = self._surface(surface)
        current.rows = list(rows)
        current.status = BrowseStatus.SUCCESS if rows else BrowseStatus.EMPTY
        current.message = ""
        current.retryable = False
        return True

    def reject_browse_result(
        self,
        surface: str,
        generation: int,
        view_id: str,
        message: str,
    ) -> bool:
        """Record an error without discarding a previously successful result."""
        if not self._request_is_current(surface, generation, view_id):
            return False
        current = self._surface(surface)
        current.status = BrowseStatus.STALE if current.rows else BrowseStatus.ERROR
        current.message = message
        current.retryable = True
        return True

    def browse_status(self, surface: str) -> BrowseStatus:
        return self._surface(surface).status

    def browse_rows(self, surface: str) -> List[BrowseRow]:
        return list(self._surface(surface).rows)

    def browse_message(self, surface: str) -> str:
        return self._surface(surface).message

    def browse_retryable(self, surface: str) -> bool:
        return self._surface(surface).retryable
    
    def set_playing(self, playing: bool) -> None:
        """Update playback state."""
        self.is_playing = playing
    
    def set_track(self, track: Optional[TrackInfo]) -> None:
        """Update current track."""
        self.current_track = track
    
    def set_volume(self, volume: float) -> None:
        """Update volume (clamped to 0.0-1.0)."""
        self.volume = max(0.0, min(1.0, volume))
    
    def toggle_shuffle(self) -> None:
        """Toggle shuffle mode."""
        self.shuffle = not self.shuffle
    
    def cycle_repeat(self) -> None:
        """Cycle through repeat modes: off -> track -> all -> off."""
        modes = ["off", "track", "all"]
        idx = modes.index(self.repeat_mode)
        self.repeat_mode = modes[(idx + 1) % len(modes)]
    
    def set_sidebar_selection(self, section: str, index: int = 0) -> None:
        """Update sidebar selection."""
        self.sidebar_section = section
        self.sidebar_index = index

    def set_focus_region(self, region: str) -> None:
        """Set the focused shell region when it is a known target."""
        if region in {"sidebar", "content", "playbar"}:
            self.focus_region = region

    def push_transient(self, view: str, return_view: str) -> None:
        """Remember a view so a transient shell screen can be closed."""
        self.view_history.append(return_view)
        self.transient_view = view

    def pop_transient(self) -> Optional[str]:
        """Close the active transient view and return its destination."""
        self.transient_view = None
        if not self.view_history:
            return None
        return self.view_history.pop()
    
    def add_to_history(self, uri: str) -> None:
        """Add a URI to history (most recent first, max 50)."""
        if uri in self.history:
            self.history.remove(uri)
        self.history.insert(0, uri)
        if len(self.history) > 50:
            self.history = self.history[:50]
