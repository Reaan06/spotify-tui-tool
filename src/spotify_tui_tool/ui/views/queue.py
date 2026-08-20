"""Queue view — current play queue.

Phase 1 of spotatui integration.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class QueueView(Widget):
    """Current queue display."""

    DEFAULT_CSS = """
    QueueView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("[bold]Queue[/bold]")
        yield Static("")
        yield Static("[dim]Queue is empty[/dim]")
