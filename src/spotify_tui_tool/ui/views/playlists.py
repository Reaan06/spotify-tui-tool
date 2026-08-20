"""Playlists view — playlist list.

Stub: playlist browsing requires the Spotify Web API.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class PlaylistsView(Widget):
    """Playlist list — stub message."""

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
        yield Static("[dim]Playlist browsing not available via playerctl.[/dim]")
        yield Static("[dim]Use spotatui or the Spotify Web API for playlist management.[/dim]")
