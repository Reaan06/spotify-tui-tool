"""Playbar component — now playing info and controls.

Phase 1 of spotatui integration.  Displays current track, progress,
volume, and control indicators.
"""

from __future__ import annotations

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.events import Click
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from spotify_tui_tool.models import PlaybackState, TrackInfo


class Playbar(Widget):
    """Bottom panel with now-playing info and controls."""

    can_focus = True

    DEFAULT_CSS = """
    Playbar {
        height: 6;
        width: 100%;
        background: $surface;
        padding: 0 1;
    }

    Playbar:focus {
        background: $boost;
    }

    #track-info {
        width: 40%;
        height: 100%;
    }

    #progress-area {
        width: 35%;
        height: 100%;
    }

    #controls-area {
        width: 25%;
        height: 100%;
    }
    """

    current_track: reactive[TrackInfo | None] = reactive(None)
    is_playing: reactive[bool] = reactive(False)
    volume: reactive[float] = reactive(0.5)
    shuffle: reactive[bool] = reactive(False)
    repeat_mode: reactive[str] = reactive("off")
    status_message: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static(id="track-info")
            yield Static(id="progress-area")
            yield Static(id="controls-area")

    def watch_current_track(self, track: TrackInfo | None) -> None:
        """Update display when track changes."""
        self._update_display()

    def watch_is_playing(self, playing: bool) -> None:
        """Update display when play state changes."""
        self._update_display()

    def watch_volume(self, volume: float) -> None:
        """Update display when volume changes."""
        self._update_display()

    def watch_shuffle(self, shuffle: bool) -> None:
        """Update display when shuffle changes."""
        self._update_display()

    def watch_repeat_mode(self, mode: str) -> None:
        """Update display when repeat mode changes."""
        self._update_display()

    def watch_status_message(self, message: str) -> None:
        self._update_display()

    def _update_display(self) -> None:
        """Update all display areas."""
        self._update_track_info()
        self._update_progress()
        self._update_controls()

    def _update_track_info(self) -> None:
        """Update track info area."""
        track = self.current_track
        if not track or (not track.artist and not track.title):
            if track and track.playback_state is PlaybackState.UNAVAILABLE:
                message = track.playback_message or "Playback unavailable."
                self.query_one("#track-info").update(escape(str(message)))
            elif track and track.playback_state is PlaybackState.STOPPED:
                self.query_one("#track-info").update("[dim]Playback stopped[/dim]")
            else:
                self.query_one("#track-info").update("[dim]No track playing[/dim]")
            return

        if track.playback_state is PlaybackState.STALE:
            status_icon = "⚠"
            prefix = "[dim]Stale[/dim] "
        else:
            status_icon = "▶" if self.is_playing else "⏸"
            prefix = ""
        self.query_one("#track-info").update(
            f"{prefix}{status_icon} {escape(str(track.artist))} — {escape(str(track.title))}"
        )

    def _update_progress(self) -> None:
        """Update progress area."""
        track = self.current_track
        if not track or track.duration_ms == 0:
            self.query_one("#progress-area").update("░░░░░░░░░░░░░░░░░░░░ --:--/--:--")
            return

        # Progress bar (0-20 chars)
        progress = min(track.position_ms / track.duration_ms, 1.0)
        bar_len = 20
        filled = int(progress * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)

        # Time display
        duration_s = track.duration_ms // 1000
        position_s = track.position_ms // 1000
        dur_min, dur_sec = divmod(duration_s, 60)
        pos_min, pos_sec = divmod(position_s, 60)

        self.query_one("#progress-area").update(
            f"{bar} {pos_min}:{pos_sec:02d}/{dur_min}:{dur_sec:02d}"
        )

    def _update_controls(self) -> None:
        """Update controls area."""
        vol_pct = int(self.volume * 100)
        controls = f"Vol: {vol_pct}%"
        if self.status_message:
            controls = f"{controls}\n{self.status_message}"
        self.query_one("#controls-area").update(controls)

    def update_track(self, track: TrackInfo | None, playing: bool) -> None:
        """Update with new track info."""
        self.current_track = track
        self.is_playing = playing

    def set_status(self, message: str, *, is_error: bool = False) -> None:
        safe_message = escape(str(message))
        self.status_message = f"[red]{safe_message}[/red]" if is_error else safe_message

    def on_click(self, event: Click) -> None:
        self.focus()
