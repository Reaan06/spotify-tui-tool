"""Queue view — current play queue.

Displays the currently playing track (playerctl does not expose the
full queue).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, Static

from spotify_tui_tool.spotify_client import QueueEntry


class QueueView(Widget):
    """Current queue display."""

    DEFAULT_CSS = """
    QueueView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    """

    queue_entries: reactive[list[QueueEntry]] = reactive(list)

    def compose(self) -> ComposeResult:
        yield Static("[bold]Queue[/bold]")
        yield DataTable(id="queue-table")

    def on_mount(self) -> None:
        table = self.query_one("#queue-table", DataTable)
        table.add_columns("#", "Title", "Artist", "Duration")
        self._refresh_table()

    def watch_queue_entries(self, entries: list[QueueEntry]) -> None:
        self._refresh_table()

    def _refresh_table(self) -> None:
        try:
            table = self.query_one("#queue-table", DataTable)
        except Exception:
            return
        table.clear()
        if not self.queue_entries:
            table.add_row("—", "[dim]Queue is empty[/dim]", "—", "—")
            return
        for i, entry in enumerate(self.queue_entries, 1):
            dur_s = entry.duration_ms // 1000
            min_, sec = divmod(dur_s, 60)
            table.add_row(
                str(i),
                entry.title or "—",
                entry.artist or "—",
                f"{min_}:{sec:02d}",
            )

    def update_queue(self, entries: list[QueueEntry]) -> None:
        """Update with new queue data from the app."""
        self.queue_entries = entries
