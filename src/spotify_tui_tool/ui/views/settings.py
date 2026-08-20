"""Settings view — configuration and preferences.

Displays the current config values.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from spotify_tui_tool.config import Config


class SettingsView(Widget):
    """Settings and configuration screen."""

    DEFAULT_CSS = """
    SettingsView {
        height: 100%;
        width: 100%;
        padding: 1 2;
    }
    """

    config_data: reactive[Config | None] = reactive(None)

    def compose(self) -> ComposeResult:
        yield Static("[bold]Settings[/bold]", id="settings-title")
        yield Static("", id="settings-body")

    def on_mount(self) -> None:
        self._refresh()

    def watch_config_data(self, config: Config | None) -> None:
        self._refresh()

    def _refresh(self) -> None:
        try:
            body = self.query_one("#settings-body", Static)
        except Exception:
            return
        cfg = self.config_data
        if cfg is None:
            cfg = Config()
        body.update(
            f"[bold]Layout[/bold]\n"
            f"  Sidebar: {cfg.sidebar_width_percent}% width, {cfg.sidebar_position} position\n"
            f"  Playbar: {cfg.playbar_height_rows} rows, bottom position\n"
            f"\n"
            f"[bold]Behavior[/bold]\n"
            f"  Tick rate: {cfg.tick_rate_ms}ms\n"
            f"  Volume increment: {cfg.volume_increment}%\n"
            f"  Seek: {cfg.seek_milliseconds}ms\n"
            f"\n"
            f"[bold]Theme[/bold]\n"
            f"  Current: {cfg.theme}\n"
            f"\n"
            f"[bold]Keybindings[/bold]\n"
            f"  Press [bold]?[/bold] for full keybinding reference"
        )

    def update_config(self, config: Config) -> None:
        """Update with new config data from the app."""
        self.config_data = config
