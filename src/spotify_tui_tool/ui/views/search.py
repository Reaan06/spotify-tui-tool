"""Search view — search input and results.

Phase 1 of spotatui integration.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Input, Static


class SearchView(Widget):
    """Search with input and results tabs."""

    DEFAULT_CSS = """
    SearchView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }

    #search-input {
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("[bold]Search[/bold]")
        yield Input(placeholder="Search tracks, albums, artists...", id="search-input")
        yield Static("")
        yield Static("[dim]Enter a search query above[/dim]")
