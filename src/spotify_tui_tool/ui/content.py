"""Content area — view switching and display.

Manages switching between views. Uses actual view widgets instead of
the placeholder ContentView.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from spotify_tui_tool.ui.views.help import HelpView
from spotify_tui_tool.ui.views.home import HomeView
from spotify_tui_tool.ui.views.library import LibraryView
from spotify_tui_tool.ui.views.playlists import PlaylistsView
from spotify_tui_tool.ui.views.queue import QueueView
from spotify_tui_tool.ui.views.search import SearchView
from spotify_tui_tool.ui.views.settings import SettingsView


class ContentArea(Widget):
    """Center panel displaying the current view."""

    DEFAULT_CSS = """
    ContentArea {
        height: 100%;
        width: 100%;
    }
    """

    current_view: reactive[str] = reactive("home")

    VIEW_WIDGETS = {
        "home": HomeView,
        "library": LibraryView,
        "playlists": PlaylistsView,
        "search": SearchView,
        "queue": QueueView,
        "settings": SettingsView,
        "help": HelpView,
    }

    def compose(self) -> ComposeResult:
        widget_cls = self.VIEW_WIDGETS.get(self.current_view, HomeView)
        yield widget_cls(id="current-view")

    async def switch_view(self, view: str) -> None:
        """Switch to a different view."""
        if view == self.current_view:
            return

        self.current_view = view

        # Remove current view
        try:
            old = self.query_one("#current-view")
            await old.remove()
        except Exception:
            pass

        # Mount new view
        widget_cls = self.VIEW_WIDGETS.get(view, HomeView)
        await self.mount(widget_cls(id="current-view"))
