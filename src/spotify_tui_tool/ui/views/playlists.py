"""Playlists view — playlist list.

Phase 1 of spotatui integration.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class PlaylistsView(Widget):
    """Playlist list."""

    DEFAULT_CSS = """
    PlaylistsView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("[bold]Playlists[/bold]")
        yield Static("")
        yield Static("[dim](No playlists)[/dim]")
