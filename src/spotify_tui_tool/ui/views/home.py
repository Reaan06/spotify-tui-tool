"""Home view — currently playing track.

Displays the active track from playerctl polling.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, Static

from spotify_tui_tool.models import PlaybackStatus, TrackInfo


class HomeView(Widget):
    """Home screen showing the currently playing track."""

    DEFAULT_CSS = """
    HomeView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    """

    current_track: reactive[TrackInfo | None] = reactive(None)
    is_playing: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        yield Static("[bold]Now Playing[/bold]", id="home-title")
        yield DataTable(id="home-table")

    def on_mount(self) -> None:
        table = self.query_one("#home-table", DataTable)
        table.add_columns("Field", "Value")
        self._refresh_table()

    def watch_current_track(self, track: TrackInfo | None) -> None:
        self._refresh_table()

    def watch_is_playing(self, playing: bool) -> None:
        self._refresh_table()

    def _refresh_table(self) -> None:
        try:
            table = self.query_one("#home-table", DataTable)
        except Exception:
            return
        table.clear()
        track = self.current_track
        if not track or (not track.artist and not track.title):
            table.add_row("Status", "[dim]No track playing[/dim]")
            table.add_row("Artist", "—")
            table.add_row("Title", "—")
            table.add_row("Album", "—")
            table.add_row("Duration", "—")
            table.add_row("Volume", "—")
            return

        status_str = "▶ Playing" if self.is_playing else "⏸ Paused"
        if track.status == PlaybackStatus.STOPPED:
            status_str = "⏹ Stopped"

        dur_s = track.duration_ms // 1000
        pos_s = track.position_ms // 1000
        dur_min, dur_sec = divmod(dur_s, 60)
        pos_min, pos_sec = divmod(pos_s, 60)

        table.add_row("Status", status_str)
        table.add_row("Artist", track.artist or "—")
        table.add_row("Title", track.title or "—")
        table.add_row("Album", track.album or "—")
        table.add_row("Duration", f"{pos_min}:{pos_sec:02d}/{dur_min}:{dur_sec:02d}")
        table.add_row("Volume", f"{int(track.volume * 100)}%")

    def update_track(self, track: TrackInfo | None, playing: bool) -> None:
        """Update with new track data from the app."""
        self.current_track = track
        self.is_playing = playing
