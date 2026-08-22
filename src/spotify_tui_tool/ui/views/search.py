"""Read-only track, album, and artist search surface."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, Input, Static

from spotify_tui_tool.ui.rows import rows_from_search
from spotify_tui_tool.ui.states import BrowseStateWidget, BrowseSurfaceMixin


class SearchView(BrowseSurfaceMixin, Widget):
    """Render search results without coupling labels to activation identity."""

    DEFAULT_CSS = """
    SearchView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }

    #search-header {
        text-style: bold;
        margin-bottom: 1;
    }

    #search-input {
        margin-bottom: 1;
    }

    #search-results {
        height: 1fr;
    }

    #search-state,
    #search-message {
        height: auto;
        padding: 1;
        content-align: center middle;
    }
    """

    class ResultSelected(Message):
        """Legacy message retained for the later activation slice."""

        def __init__(self, uri: str) -> None:
            self.uri = uri
            super().__init__()

    is_authenticated: reactive[bool] = reactive(False)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._init_browse_surface("search", "search-results", "search-state")

    def compose(self) -> ComposeResult:
        yield Static("[bold]Search[/bold]", id="search-header")
        yield Input(placeholder="Search tracks, albums, artists...", id="search-input")
        yield DataTable(id="search-results")
        yield BrowseStateWidget("search", id="search-state")
        yield Static(
            "[dim]Not signed in. Press Enter to log in.[/dim]",
            id="search-message",
        )

    def on_mount(self) -> None:
        table = self.query_one("#search-results", DataTable)
        table.add_columns("Name", "Artist / Genre", "Album / Info", "Duration")
        self._render_rows()
        self._render_surface_state()
        self._update_display()

    def _update_display(self) -> None:
        try:
            table = self.query_one("#search-results", DataTable)
            message = self.query_one("#search-message", Static)
            state = self.query_one("#search-state", BrowseStateWidget)
        except Exception:
            return
        table.display = self.is_authenticated
        message.display = not self.is_authenticated
        state.display = self.is_authenticated and self.surface_state.value != "success"

    def update_results(self, results: dict) -> None:
        self.set_rows(rows_from_search(results))

    def set_authenticated(self, authenticated: bool) -> None:
        self.is_authenticated = authenticated
        self._update_display()

    def get_selected_row(self):
        table = self.query_one("#search-results", DataTable)
        if table.cursor_row is None:
            return None
        if 0 <= table.cursor_row < len(self._browse_rows):
            return self._browse_rows[table.cursor_row]
        return None

    def get_selected_uri(self) -> str | None:
        """Return stored URI for compatibility, never a rendered cell value."""
        row = self.get_selected_row()
        return row.uri if row is not None and row.uri else None
