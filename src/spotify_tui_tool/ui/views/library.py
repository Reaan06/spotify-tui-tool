"""Read-only liked-songs browse surface."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, Static

from spotify_tui_tool.state import BrowseStatus
from spotify_tui_tool.ui.rows import rows_from_library
from spotify_tui_tool.ui.states import BrowseStateWidget, BrowseSurfaceMixin


class LibraryView(BrowseSurfaceMixin, Widget):
    """Render authenticated library rows while retaining their source identity."""

    DEFAULT_CSS = """
    LibraryView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }

    #library-header {
        text-style: bold;
        margin-bottom: 1;
    }

    #liked-songs-table {
        height: 1fr;
    }

    #library-state,
    #library-message {
        height: auto;
        padding: 1;
        content-align: center middle;
    }
    """

    is_authenticated: reactive[bool] = reactive(False)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._init_browse_surface("library", "liked-songs-table", "library-state")

    def compose(self) -> ComposeResult:
        yield Static("[bold]Liked Songs[/bold]", id="library-header")
        yield DataTable(id="liked-songs-table")
        yield BrowseStateWidget("library", id="library-state")
        yield Static(
            "[dim]Not signed in. Press Enter to log in.[/dim]",
            id="library-message",
        )

    def on_mount(self) -> None:
        table = self.query_one("#liked-songs-table", DataTable)
        table.add_columns("Title", "Artist", "Album", "Duration")
        self._render_rows()
        self._render_surface_state()
        self._update_display()

    def _update_display(self) -> None:
        try:
            table = self.query_one("#liked-songs-table", DataTable)
            message = self.query_one("#library-message", Static)
            state = self.query_one("#library-state", BrowseStateWidget)
        except Exception:
            return
        table.display = self.is_authenticated
        message.display = not self.is_authenticated
        state.display = self.is_authenticated and self.surface_state is not BrowseStatus.SUCCESS

    def update_liked_songs(self, songs: list[dict]) -> None:
        """Compatibility adapter for the API payload shape."""
        self.set_rows(rows_from_library(songs))

    def set_authenticated(self, authenticated: bool) -> None:
        self.is_authenticated = authenticated
        self._update_display()
