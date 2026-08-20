"""Search view — search input and results.

Stub: search requires the Spotify Web API.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Input, Static


class SearchView(Widget):
    """Search with input — stub for Web API integration."""

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
        yield Static("[dim]Search requires the Spotify Web API.[/dim]")
        yield Static("[dim]Paste a Spotify URI or URL to play via playerctl.[/dim]")
