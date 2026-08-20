"""Settings view — configuration and preferences.

Phase 1 of spotatui integration.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class SettingsView(Widget):
    """Settings and configuration screen."""

    DEFAULT_CSS = """
    SettingsView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("[bold]Settings[/bold]")
        yield Static("")
        yield Static("[bold]Layout[/bold]")
        yield Static("  Sidebar: 20% width, left position")
        yield Static("  Playbar: 6 rows, bottom position")
        yield Static("")
        yield Static("[bold]Behavior[/bold]")
        yield Static("  Tick rate: 1000ms")
        yield Static("  Volume increment: 10%")
        yield Static("  Seek: 5000ms")
        yield Static("")
        yield Static("[bold]Theme[/bold]")
        yield Static("  Current: dark")
        yield Static("")
        yield Static("[bold]Keybindings[/bold]")
        yield Static("  Press ? for full keybinding reference")
