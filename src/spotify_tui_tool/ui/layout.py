"""Layout manager — 3-panel layout structure.

Phase 1 of spotatui integration.  Manages the main 3-panel layout:
Sidebar (left), Content (center), Playbar (bottom).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Resize
from textual.widget import Widget

from spotify_tui_tool.ui.content import ContentArea
from spotify_tui_tool.ui.playbar import Playbar
from spotify_tui_tool.ui.sidebar import Sidebar


class LayoutManager(Widget):
    """Manages the 3-panel layout: Sidebar, Content, Playbar."""

    COMPACT_BREAKPOINT = 96
    WIDE_SIDEBAR_PERCENT = 22
    COMPACT_SIDEBAR_COLUMNS = 16
    WIDE_PLAYBAR_ROWS = 5
    COMPACT_PLAYBAR_ROWS = 4

    can_focus = False

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.is_compact = False

    DEFAULT_CSS = """
    LayoutManager {
        height: 100%;
        width: 100%;
    }

    #main-container {
        height: 100%;
        width: 100%;
    }

    #sidebar {
        width: 22%;
        min-width: 16;
        box-sizing: border-box;
        background: $surface;
        border-right: solid $primary;
    }

    #content-area {
        width: 78%;
        min-width: 1fr;
    }

    #content {
        height: 1fr;
    }

    #playbar {
        height: 5;
        background: $surface;
        border-top: solid $primary;
    }

    .compact #sidebar {
        width: 16;
        min-width: 16;
        max-width: 16;
    }

    .compact #content-area {
        width: 1fr;
    }

    .compact #playbar {
        height: 4;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-container"):
            yield Sidebar(id="sidebar")
            with Vertical(id="content-area"):
                yield ContentArea(id="content")
                yield Playbar(id="playbar")

    def on_mount(self) -> None:
        self._set_responsive(self.app.size.width)

    def on_resize(self, event: Resize) -> None:
        self._set_responsive(event.size.width)

    def _set_responsive(self, width: int) -> None:
        compact = width <= self.COMPACT_BREAKPOINT
        self.is_compact = compact
        if compact:
            self.add_class("compact")
        else:
            self.remove_class("compact")
        try:
            sidebar = self.query_one(Sidebar)
            sidebar.styles.width = 16 if compact else "22%"
            sidebar.styles.min_width = 16 if compact else 16
            sidebar.styles.max_width = 16 if compact else None
            content = self.query_one("#content-area")
            content.styles.width = "1fr" if compact else "78%"
            playbar = self.query_one("#playbar")
            playbar.styles.height = 4 if compact else 5
            sidebar.set_compact(compact)
        except Exception:
            pass
