"""Sidebar component — source selector, library, playlists.

Phase 1 of spotatui integration.  Displays navigation sections.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


class SidebarItem(Static):
    """A single item in the sidebar."""

    DEFAULT_CSS = """
    SidebarItem {
        padding: 0 1;
        height: 1;
    }

    SidebarItem:hover {
        background: $primary;
    }

    SidebarItem.selected {
        background: $primary;
        text-style: bold;
    }
    """

    def __init__(self, label: str, **kwargs) -> None:
        super().__init__(label, **kwargs)
        self.label_text = label

    class Selected(Message):
        """Emitted when an item is selected."""

        def __init__(self, item_id: str, section: str) -> None:
            self.item_id = item_id
            self.section = section
            super().__init__()


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


class Sidebar(Widget):
    """Left panel with source selector, library, playlists."""

    DEFAULT_CSS = """
    Sidebar {
        width: 100%;
        height: 100%;
        background: $surface;
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
    """

    SOURCES = [
        ("Spotify", "source-spotify"),
        ("Local", "source-local"),
        ("Radio", "source-radio"),
    ]

    LIBRARY = [
        ("Liked Songs", "lib-liked"),
        ("Albums", "lib-albums"),
        ("Artists", "lib-artists"),
    ]

    selected_index: reactive[int] = reactive(0)
    current_section: reactive[str] = reactive("library")

    def compose(self) -> ComposeResult:
        with Vertical(id="sources-section"):
            yield SidebarSection("Sources")
            for label, item_id in self.SOURCES:
                yield SidebarItem(f"  {label}", id=item_id)

        with Vertical(id="library-section"):
            yield SidebarSection("Library")
            for label, item_id in self.LIBRARY:
                yield SidebarItem(f"  {label}", id=item_id)

        with Vertical(id="playlists-section"):
            yield SidebarSection("Playlists")
            yield SidebarItem("  (No playlists)", id="playlists-empty")

    def on_sidebar_item_selected(self, event: SidebarItem.Selected) -> None:
        """Handle item selection."""
        self.current_section = event.section
