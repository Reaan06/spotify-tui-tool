"""Content area — view switching and display.

Phase 1 of spotatui integration.  Manages switching between views.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class ContentView(Widget):
    """A placeholder view for content."""

    DEFAULT_CSS = """
    ContentView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    """

    def __init__(self, title: str, content: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self.title_text = title
        self.content_text = content

    def compose(self) -> ComposeResult:
        yield Static(f"[bold]{self.title_text}[/bold]")
        yield Static(self.content_text)


class ContentArea(Widget):
    """Center panel displaying the current view."""

    DEFAULT_CSS = """
    ContentArea {
        height: 100%;
        width: 100%;
    }
    """

    current_view: reactive[str] = reactive("home")

    VIEW_CONTENT = {
        "home": ("Home", "Recently played tracks will appear here."),
        "library": ("Library", "Your liked songs will appear here."),
        "playlists": ("Playlists", "Your playlists will appear here."),
        "search": ("Search", "Search for tracks, albums, artists."),
        "queue": ("Queue", "Your play queue will appear here."),
        "settings": ("Settings", "Configure your preferences."),
        "help": ("Help", "Press ? for keybinding reference."),
    }

    def compose(self) -> ComposeResult:
        title, content = self.VIEW_CONTENT.get(self.current_view, ("Home", ""))
        yield ContentView(title, content, id="current-view")

    async def switch_view(self, view: str) -> None:
        """Switch to a different view."""
        if view == self.current_view:
            return

        self.current_view = view

        # Remove current view
        try:
            old = self.query_one("#current-view")
            old.remove()
        except Exception:
            pass

        # Mount new view
        title, content = self.VIEW_CONTENT.get(view, ("Home", ""))
        await self.mount(ContentView(title, content, id="current-view"))
