"""Help view — keybinding reference.

Phase 1 of spotatui integration.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Static


class HelpView(Widget):
    """Help screen with all keybindings."""

    DEFAULT_CSS = """
    HelpView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    """

    KEYBINDINGS = [
        ("Space", "Play/Pause", "Playback"),
        ("n", "Next track", "Playback"),
        ("p", "Previous track", "Playback"),
        ("+", "Volume up", "Playback"),
        ("-", "Volume down", "Playback"),
        ("<", "Seek backward", "Playback"),
        (">", "Seek forward", "Playback"),
        ("F", "Like/Unlike", "Action"),
        ("/", "Search", "Navigation"),
        ("1", "Home view", "Navigation"),
        ("2", "Library view", "Navigation"),
        ("3", "Playlists view", "Navigation"),
        ("4", "Search view", "Navigation"),
        ("5", "Queue view", "Navigation"),
        ("6", "Settings view", "Navigation"),
        ("j", "Move down", "Navigation"),
        ("k", "Move up", "Navigation"),
        ("h", "Move left", "Navigation"),
        ("l", "Move right", "Navigation"),
        ("Esc", "Back", "Navigation"),
        ("q", "Quit", "System"),
        ("?", "Help", "System"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("[bold]Help — Keybindings[/bold]")
        table = DataTable()
        table.add_columns("Key", "Action", "Category")
        for key, action, category in self.KEYBINDINGS:
            table.add_row(key, action, category)
        yield table
