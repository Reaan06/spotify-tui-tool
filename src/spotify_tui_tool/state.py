"""App state manager — global application state.

Phase 1 of spotatui integration.  Manages the current view, sidebar
selection, playback state, and other UI state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from spotify_tui_tool.models import TrackInfo


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
    
    # Queue
    queue: List[TrackInfo] = field(default_factory=list)
    
    # History
    history: List[str] = field(default_factory=list)  # URIs
    
    def set_view(self, view: str) -> None:
        """Switch to a different view."""
        valid_views = {"home", "library", "playlists", "search", "queue", "settings", "help"}
        if view in valid_views:
            self.current_view = view
    
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
    
    def add_to_queue(self, track: TrackInfo) -> None:
        """Add a track to the queue."""
        self.queue.append(track)
    
    def remove_from_queue(self, index: int) -> None:
        """Remove a track from the queue by index."""
        if 0 <= index < len(self.queue):
            self.queue.pop(index)
    
    def clear_queue(self) -> None:
        """Clear the queue."""
        self.queue.clear()
    
    def add_to_history(self, uri: str) -> None:
        """Add a URI to history (most recent first, max 50)."""
        if uri in self.history:
            self.history.remove(uri)
        self.history.insert(0, uri)
        if len(self.history) > 50:
            self.history = self.history[:50]
