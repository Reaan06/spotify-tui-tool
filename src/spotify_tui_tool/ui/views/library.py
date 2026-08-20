"""Library view — liked songs.

Stub: liked songs are not available via playerctl.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class LibraryView(Widget):
    """Liked songs library — stub message."""

    DEFAULT_CSS = """
    LibraryView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("[bold]Liked Songs[/bold]")
        yield Static("")
        yield Static("[dim]Liked songs not available via playerctl.[/dim]")
        yield Static("[dim]Use the Spotify app or a Web API client to manage likes.[/dim]")
