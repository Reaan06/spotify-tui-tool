"""Sidebar component — source selector, library, playlists.

Supports j/k navigation with visual highlighting.
"""

from __future__ import annotations

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.events import Click, MouseScrollDown, MouseScrollUp
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class SidebarItem(Static):
    """A single item in the sidebar."""

    can_focus = True

    DEFAULT_CSS = """
    SidebarItem {
        padding: 0 1;
        height: 1;
    }

    SidebarItem:hover {
        background: $primary;
    }

    SidebarItem.highlighted {
        background: $primary;
        text-style: bold;
    }

    SidebarItem:focus {
        background: $primary;
        text-style: bold;
    }
    """

    def __init__(
        self,
        label: str,
        *,
        section: str = "",
        view: str = "",
        compact_label: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__("", **kwargs)
        self.label_text = label
        self.compact_label = compact_label or label[:2]
        self.item_id = kwargs.get("id", "")
        self.section = section
        self.view = view
        self._compact = False
        self._selected = False
        self.is_highlighted = False
        self._refresh_label()

    class Selected(Message):
        """Emitted when an item is selected."""

        def __init__(self, item_id: str, section: str, view: str = "") -> None:
            self.item_id = item_id
            self.section = section
            self.view = view
            super().__init__()

    def _refresh_label(self) -> None:
        label = self.compact_label if self._compact else self.label_text
        marker = "▸ " if self._selected else "  "
        self.update(f"{marker}{label}")

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.is_highlighted = selected
        self._refresh_label()

    def set_compact(self, compact: bool) -> None:
        self._compact = compact
        self._refresh_label()

    def on_click(self, event: Click) -> None:
        self.focus()
        self.post_message(self.Selected(self.item_id, self.section, self.view))
        event.stop()


class SidebarSection(Static):
    """A section header in the sidebar."""

    DEFAULT_CSS = """
    SidebarSection {
        padding: 1 1 0 1;
        height: 1;
        text-style: bold;
        color: $primary;
    }
    """

    def __init__(self, label: str, *, compact_label: str | None = None, **kwargs) -> None:
        super().__init__(label, **kwargs)
        self.label_text = label
        self.compact_label = compact_label or label[:3]

    def set_compact(self, compact: bool) -> None:
        self.update(self.compact_label if compact else self.label_text)


class Sidebar(Widget):
    """Left panel with source selector, library, playlists."""

    can_focus = True

    DEFAULT_CSS = """
    Sidebar {
        width: 100%;
        height: 100%;
        background: $surface;
    }

    Sidebar:focus {
        background: $boost;
    }

    #sources-section {
        height: auto;
    }

    #library-section {
        height: auto;
    }

    #playlists-section {
        height: 1fr;
    }

    #login-section {
        height: auto;
        padding: 1 0;
        border-top: solid $primary;
    }

    #login-status {
        padding: 0 1;
        height: 1;
    }
    """

    SOURCES = [
        ("Spotify", "source-spotify"),
    ]

    LIBRARY = [
        ("Liked Songs", "lib-liked"),
        ("Albums", "lib-albums"),
        ("Artists", "lib-artists"),
    ]

    selected_index: reactive[int] = reactive(0)
    current_section: reactive[str] = reactive("library")
    is_logged_in: reactive[bool] = reactive(False)
    username: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        with Vertical(id="sources-section"):
            yield SidebarSection("Sources", compact_label="Src")
            for label, item_id in self.SOURCES:
                yield SidebarItem(
                    label,
                    id=item_id,
                    section="sources",
                    view="home",
                    compact_label=self._compact_label(item_id),
                )

        with Vertical(id="library-section"):
            yield SidebarSection("Library", compact_label="Lib")
            for label, item_id in self.LIBRARY:
                yield SidebarItem(
                    label,
                    id=item_id,
                    section="library",
                    view="library",
                    compact_label=self._compact_label(item_id),
                )

        with Vertical(id="playlists-section"):
            yield SidebarSection("Playlists", compact_label="Pls")
            yield SidebarItem(
                "(No playlists)",
                id="playlists-empty",
                section="playlists",
                view="playlists",
                compact_label="Pls",
            )

        with Vertical(id="login-section"):
            yield Static("[dim]Not logged in[/dim]", id="login-status")

    @staticmethod
    def _compact_label(item_id: str) -> str:
        return {
            "source-spotify": "Sp",
            "lib-liked": "Li",
            "lib-albums": "Al",
            "lib-artists": "Ar",
        }.get(item_id, item_id[:2])

    def get_all_items(self) -> list[SidebarItem]:
        """Get all sidebar items in order."""
        return list(self.query(SidebarItem))

    def get_selected_item(self) -> SidebarItem:
        return self.get_all_items()[self.selected_index]

    def on_mount(self) -> None:
        self._apply_selection()

    def _apply_selection(self) -> None:
        items = self.get_all_items()
        for index, item in enumerate(items):
            item.set_selected(index == self.selected_index)

    def move_selection(self, delta: int) -> None:
        """Move selection by delta (-1 up, +1 down)."""
        items = self.get_all_items()
        if not items:
            return

        # Remove current highlight
        if 0 <= self.selected_index < len(items):
            items[self.selected_index].remove_class("highlighted")

        # Update index
        self.selected_index = max(0, min(self.selected_index + delta, len(items) - 1))

        # Apply new highlight
        self._apply_selection()

    def activate_selection(self) -> None:
        item = self.get_selected_item()
        item.post_message(item.Selected(item.item_id, item.section, item.view))

    def set_compact(self, compact: bool) -> None:
        for item in self.get_all_items():
            item.set_compact(compact)
        for section in self.query(SidebarSection):
            section.set_compact(compact)

    def on_mouse_scroll_down(self, event: MouseScrollDown) -> None:
        self.move_selection(1)
        event.stop()

    def on_mouse_scroll_up(self, event: MouseScrollUp) -> None:
        self.move_selection(-1)
        event.stop()

    def update_login_status(self, logged_in: bool, username: str = "") -> None:
        """Update login status display."""
        self.is_logged_in = logged_in
        self.username = username
        status = self.query_one("#login-status")
        if logged_in:
            status.update(f"[green]Logged in as {escape(username)}[/green]")
        else:
            status.update("[dim]Not logged in[/dim]")

    def on_sidebar_item_selected(self, event: SidebarItem.Selected) -> None:
        """Handle item selection."""
        self.current_section = event.section
        for index, item in enumerate(self.get_all_items()):
            if item.item_id == event.item_id:
                self.selected_index = index
                break
        self._apply_selection()
