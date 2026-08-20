"""Home view — recently played tracks.

Phase 1 of spotatui integration.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Static


class HomeView(Widget):
    """Home screen with recently played."""

    DEFAULT_CSS = """
    HomeView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("[bold]Recently Played[/bold]")
        table = DataTable()
        table.add_columns("#", "Title", "Artist", "Album", "Duration")
        # Placeholder row
        table.add_row("1", "No tracks yet", "—", "—", "--:--")
        yield table
