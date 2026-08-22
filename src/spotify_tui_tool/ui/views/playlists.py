"""Read-only user-playlists browse surface."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, Static

from spotify_tui_tool.ui.rows import rows_from_playlists
from spotify_tui_tool.ui.states import BrowseStateWidget, BrowseSurfaceMixin


class PlaylistsView(BrowseSurfaceMixin, Widget):
    """Render playlist rows with stable playlist identity."""

    DEFAULT_CSS = """
    PlaylistsView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }

    #playlists-header {
        text-style: bold;
        margin-bottom: 1;
    }

    #playlists-table {
        height: 1fr;
    }

    #playlists-state,
    #playlists-message {
        height: auto;
        padding: 1;
        content-align: center middle;
    }
    """

    is_authenticated: reactive[bool] = reactive(False)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._init_browse_surface("playlists", "playlists-table", "playlists-state")

    def compose(self) -> ComposeResult:
        yield Static("[bold]Playlists[/bold]", id="playlists-header")
        yield DataTable(id="playlists-table")
        yield BrowseStateWidget("playlists", id="playlists-state")
        yield Static(
            "[dim]Not signed in. Press Enter to log in.[/dim]",
            id="playlists-message",
        )

    def on_mount(self) -> None:
        table = self.query_one("#playlists-table", DataTable)
        table.add_columns("Name", "Tracks", "Description", "")
        self._render_rows()
        self._render_surface_state()
        self._update_display()

    def _update_display(self) -> None:
        try:
            table = self.query_one("#playlists-table", DataTable)
            message = self.query_one("#playlists-message", Static)
            state = self.query_one("#playlists-state", BrowseStateWidget)
        except Exception:
            return
        table.display = self.is_authenticated
        message.display = not self.is_authenticated
        state.display = self.is_authenticated and self.surface_state.value != "success"

    def update_playlists(self, playlists: list[dict]) -> None:
        self.set_rows(rows_from_playlists(playlists))

    def set_authenticated(self, authenticated: bool) -> None:
        self.is_authenticated = authenticated
        self._update_display()
