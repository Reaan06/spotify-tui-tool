"""Layout manager — 3-panel layout structure.

Phase 1 of spotatui integration.  Manages the main 3-panel layout:
Sidebar (left), Content (center), Playbar (bottom).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static


class LayoutManager(Widget):
    """Manages the 3-panel layout: Sidebar, Content, Playbar."""

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
        width: 20%;
        background: $surface;
        border-right: solid $primary;
    }

    #content-area {
        width: 80%;
    }

    #content {
        height: 1fr;
    }

    #playbar {
        height: 6;
        background: $surface;
        border-top: solid $primary;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-container"):
            yield Vertical(id="sidebar")
            with Vertical(id="content-area"):
                yield Widget(id="content")
                yield Static(id="playbar")
