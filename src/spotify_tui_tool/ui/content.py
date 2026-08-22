"""Content area — view switching and display.

Manages switching between views. Uses actual view widgets instead of
the placeholder ContentView.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.events import Click, MouseScrollDown, MouseScrollUp
from textual.reactive import reactive
from textual.widgets import DataTable

from spotify_tui_tool.models import BrowseRow
from spotify_tui_tool.ui.views.help import HelpView
from spotify_tui_tool.ui.views.home import HomeView
from spotify_tui_tool.ui.views.library import LibraryView
from spotify_tui_tool.ui.views.login import LoginView
from spotify_tui_tool.ui.views.playlists import PlaylistsView
from spotify_tui_tool.ui.views.search import SearchView
from spotify_tui_tool.ui.views.settings import SettingsView


class ContentArea(ScrollableContainer):
    """Center panel displaying the current view."""

    can_focus = True

    DEFAULT_CSS = """
    ContentArea {
        height: 100%;
        width: 100%;
        overflow-y: auto;
    }

    ContentArea:focus {
        background: $boost;
    }
    """

    current_view: reactive[str] = reactive("home")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.scroll_requests = 0

    VIEW_WIDGETS = {
        "home": HomeView,
        "library": LibraryView,
        "playlists": PlaylistsView,
        "search": SearchView,
        "settings": SettingsView,
        "help": HelpView,
        "login": LoginView,
    }

    def compose(self) -> ComposeResult:
        widget_cls = self.VIEW_WIDGETS.get(self.current_view, HomeView)
        yield widget_cls(id="current-view")

    async def switch_view(self, view: str) -> None:
        """Switch to a different view."""
        if view not in self.VIEW_WIDGETS:
            return
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

    def move_selection(self, delta: int) -> None:
        table = next(iter(self.query(DataTable)), None)
        if table is None:
            self.focus()
            return
        table.focus()
        if delta > 0:
            table.action_cursor_down()
        elif delta < 0:
            table.action_cursor_up()

    def scroll_region(self, direction: str) -> int:
        if direction not in {"up", "down"}:
            raise ValueError("direction must be 'up' or 'down'")
        self.scroll_requests += 1
        try:
            self.focus()
            self.app._state.set_focus_region("content")
        except Exception:
            pass
        table = next(iter(self.query(DataTable)), None)
        if table is not None:
            if direction == "down":
                table.scroll_down(animate=False)
                return 1
            table.scroll_up(animate=False)
            return -1
        try:
            self.scroll_relative(y=3 if direction == "down" else -3)
        except Exception:
            # Unit callers may exercise the contract before an App is active.
            pass
        return 1 if direction == "down" else -1

    def on_mouse_scroll_down(self, event: MouseScrollDown | None = None) -> None:
        self.scroll_region("down")
        if event is not None:
            event.stop()

    def on_mouse_scroll_up(self, event: MouseScrollUp | None = None) -> None:
        self.scroll_region("up")
        if event is not None:
            event.stop()

    def on_click(self, event: Click) -> None:
        if event.widget is self:
            self.focus()

    def activate_focused(self) -> str | BrowseRow:
        """Return the focused stored row, or the legacy content marker."""
        try:
            view = self.query_one("#current-view")
            getter = getattr(view, "get_selected_row", None)
            if getter is not None:
                row = getter()
                if row is not None:
                    return row
        except Exception:
            pass
        return "content"
