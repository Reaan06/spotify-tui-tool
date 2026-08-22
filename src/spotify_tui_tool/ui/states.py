"""Shared rendering for explicit browse surface states."""

from __future__ import annotations

from rich.markup import escape
from textual.widgets import DataTable, Static

from spotify_tui_tool.state import BrowseStatus, BrowseSurfaceState
from spotify_tui_tool.ui.rows import BrowseRowActivated

BrowseState = BrowseStatus


def browse_state_text(
    status: BrowseStatus | str,
    *,
    surface: str,
    message: str = "",
) -> str:
    """Return honest, user-facing copy for a browse state."""
    resolved = status if isinstance(status, BrowseStatus) else BrowseStatus(status)
    labels = {
        "library": "liked songs",
        "playlists": "playlists",
        "search": "search results",
    }
    label = labels.get(surface, surface)
    if resolved is BrowseStatus.LOADING:
        return f"Loading {label}…"
    if resolved is BrowseStatus.EMPTY:
        return f"No {label} found. Press r to retry."
    if resolved is BrowseStatus.ERROR:
        detail = f" {escape(message)}" if message else ""
        return f"Browse error:{detail} Press r to retry."
    if resolved is BrowseStatus.STALE:
        detail = f" {escape(message)}" if message else " Refresh failed."
        return f"Showing stale {label}.{detail} Press r to retry."
    return ""


class BrowseStateWidget(Static):
    """Small state surface that never replaces the persistent shell."""

    def __init__(self, surface: str, **kwargs) -> None:
        super().__init__("", **kwargs)
        self.surface = surface
        self.status = BrowseStatus.EMPTY
        self.message = ""

    def set_state(self, status: BrowseStatus | str, message: str = "") -> None:
        self.status = status if isinstance(status, BrowseStatus) else BrowseStatus(status)
        self.message = message
        self.update(
            browse_state_text(
                self.status,
                surface=self.surface,
                message=message,
            )
        )


# A concise alias for callers that want to compose the state widget directly.
SurfaceState = BrowseStateWidget


class BrowseSurfaceMixin:
    """Reusable state/row plumbing for library, playlist, and search views."""

    surface_name = ""
    table_id = ""
    state_id = ""

    def _init_browse_surface(self, surface: str, table_id: str, state_id: str) -> None:
        self.surface_name = surface
        self.table_id = table_id
        self.state_id = state_id
        self._browse_rows = []
        self.surface_state = BrowseStatus.EMPTY
        self.surface_message = ""

    def _row_cells(self, row) -> tuple[str, ...]:
        return tuple(
            escape(str(cell))
            for cell in (row.title, row.subtitle, row.detail, row.auxiliary)
        )

    def _render_rows(self) -> None:
        try:
            table = self.query_one(f"#{self.table_id}", DataTable)
        except Exception:
            return
        table.cursor_type = "row"
        table.clear()
        for row in self._browse_rows:
            table.add_row(*self._row_cells(row), key=row.key)

    def _render_surface_state(self) -> None:
        try:
            widget = self.query_one(f"#{self.state_id}", BrowseStateWidget)
            widget.set_state(self.surface_state, self.surface_message)
        except Exception:
            return

    def set_rows(self, rows) -> None:
        self._browse_rows = list(rows)
        self.surface_state = BrowseStatus.SUCCESS if self._browse_rows else BrowseStatus.EMPTY
        self.surface_message = ""
        self._render_rows()
        self._render_surface_state()
        if hasattr(self, "_update_display"):
            self._update_display()

    def set_loading(self) -> None:
        self.surface_state = BrowseStatus.LOADING
        self.surface_message = ""
        self._render_surface_state()
        if hasattr(self, "_update_display"):
            self._update_display()

    def set_error(self, message: str) -> None:
        self.surface_state = BrowseStatus.STALE if self._browse_rows else BrowseStatus.ERROR
        self.surface_message = message
        self._render_surface_state()
        if hasattr(self, "_update_display"):
            self._update_display()

    def row_for_key(self, key: str):
        return next((row for row in self._browse_rows if row.key == key), None)

    def get_selected_row(self):
        """Resolve the focused table position back to stored row data."""
        try:
            table = self.query_one(f"#{self.table_id}", DataTable)
            index = table.cursor_row
        except Exception:
            return None
        if index is None or not 0 <= index < len(self._browse_rows):
            return None
        return self._browse_rows[index]

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        key = getattr(event.row_key, "value", event.row_key) or ""
        row = self.row_for_key(key)
        if row is not None:
            self.post_message(BrowseRowActivated(row))

    @property
    def browse_rows(self):
        return list(self._browse_rows)

__all__ = [
    "BrowseState",
    "BrowseStateWidget",
    "BrowseStatus",
    "BrowseSurfaceState",
    "SurfaceState",
    "browse_state_text",
]
