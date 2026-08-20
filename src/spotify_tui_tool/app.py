"""Spotify TUI App — main Textual application.

Phase 5 of the MVP.  Combines NowPlaying widget, search input, and
transport controls into a full-screen TUI.

Keybindings (vim-style):
    Space       Play/Pause
    n / l       Next track
    p / h       Previous track
    j / k       Volume down/up
    /           Focus search input
    Enter       Play URI (when search focused)
    q / Ctrl+C  Quit
"""

from __future__ import annotations

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.timer import Timer
from textual.widgets import Footer, Header, Input, Label, Static

from spotify_tui_tool.exceptions import (
    InvalidURIError,
    PlaybackError,
    PlayerctlNotFoundError,
    SpotifyNotRunningError,
)
from spotify_tui_tool.now_playing import NowPlaying
from spotify_tui_tool.playerctl import PlayerController
from spotify_tui_tool.search import SearchService


# ------------------------------------------------------------------
# Custom widgets
# ------------------------------------------------------------------

class NowPlayingPanel(Static):
    """Displays current track metadata and playback status."""

    DEFAULT_CSS = """
    NowPlayingPanel {
        height: 7;
        padding: 0 1;
        background: $surface;
        border: solid $primary;
    }
    """

    def update_display(self, info) -> None:
        """Update the panel with a TrackInfo object."""
        if not info or (not info.artist and not info.title):
            self.update("[dim]No track playing[/dim]")
            return

        status_icon = {
            "PLAYING": "▶",
            "PAUSED": "⏸",
            "STOPPED": "⏹",
        }.get(info.status.value, "?")

        # Format duration
        if info.duration_ms > 0:
            duration_s = info.duration_ms // 1000
            position_s = info.position_ms // 1000
            dur_min, dur_sec = divmod(duration_s, 60)
            pos_min, pos_sec = divmod(position_s, 60)
            time_str = f"{pos_min}:{pos_sec:02d}/{dur_min}:{dur_sec:02d}"
        else:
            time_str = "--:--/--:--"

        # Progress bar (0-20 chars)
        if info.duration_ms > 0:
            progress = min(info.position_ms / info.duration_ms, 1.0)
            bar_len = 20
            filled = int(progress * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)
        else:
            bar = "░" * 20

        volume_pct = int(info.volume * 100)

        lines = [
            f" {status_icon} [bold]{info.artist}[/bold] — [italic]{info.title}[/italic]",
            f"   Album: {info.album or '[dim]N/A[/dim]'}",
            f"   {bar} {time_str}  Vol: {volume_pct}%",
        ]
        self.update("\n".join(lines))


class StatusBar(Static):
    """Bottom status bar for notifications and errors."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        background: $surface;
        color: $text;
    }
    """

    def show_message(self, text: str, is_error: bool = False) -> None:
        if is_error:
            self.update(f"[bold red]Error:[/bold red] {text}")
        else:
            self.update(text)


# ------------------------------------------------------------------
# Main App
# ------------------------------------------------------------------

class SpotifyTuiApp(App):
    """Textual app for controlling SpotX-patched Spotify via playerctl."""

    TITLE = "Spotify TUI"
    CSS = """
    #now-playing {
        height: 7;
    }
    #search-container {
        height: 3;
        padding: 0 1;
    }
    #search-input {
        width: 100%;
    }
    #status-bar {
        height: 1;
    }
    """

    BINDINGS = [
        Binding("space", "play_pause", "Play/Pause", show=True),
        Binding("n", "next_track", "Next", show=True),
        Binding("p", "previous_track", "Previous", show=True),
        Binding("k", "volume_up", "Vol +", show=True),
        Binding("j", "volume_down", "Vol -", show=True),
        Binding("slash", "focus_search", "Search", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]

    def __init__(self, player_name: str = "spotify") -> None:
        super().__init__()
        self._player = PlayerController(player_name=player_name)
        self._search_service = SearchService(player=self._player)
        self._now_playing = NowPlaying(player=self._player, poll_interval=1.0)
        self._poll_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield NowPlayingPanel(id="now-playing")
            with Horizontal(id="search-container"):
                yield Label("URI: ")
                yield Input(placeholder="spotify:track:... or open.spotify.com/...", id="search-input")
            yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Start polling when the app mounts."""
        self._poll_timer = self.set_interval(
            self._now_playing.poll_interval,
            self._poll_metadata,
        )
        self._poll_metadata()  # Initial poll
        self.query_one(StatusBar).show_message("Ready. Press / to search, Space to play/pause.")

    def _poll_metadata(self) -> None:
        """Poll playerctl for current track metadata."""
        info = self._now_playing.poll_once()
        self.query_one(NowPlayingPanel).update_display(info)

    # ------------------------------------------------------------------
    # Actions (keybindings)
    # ------------------------------------------------------------------

    def action_play_pause(self) -> None:
        try:
            self._player.play_pause()
            self.query_one(StatusBar).show_message("Toggled play/pause")
        except SpotifyNotRunningError:
            self.query_one(StatusBar).show_message("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self.query_one(StatusBar).show_message(str(e), is_error=True)

    def action_next_track(self) -> None:
        try:
            self._player.next()
            self.query_one(StatusBar).show_message("Next track")
        except SpotifyNotRunningError:
            self.query_one(StatusBar).show_message("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self.query_one(StatusBar).show_message(str(e), is_error=True)

    def action_previous_track(self) -> None:
        try:
            self._player.previous()
            self.query_one(StatusBar).show_message("Previous track")
        except SpotifyNotRunningError:
            self.query_one(StatusBar).show_message("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self.query_one(StatusBar).show_message(str(e), is_error=True)

    def action_volume_up(self) -> None:
        try:
            current = self._player.get_volume()
            new_vol = min(current + 0.1, 1.0)
            self._player.set_volume(new_vol)
            self.query_one(StatusBar).show_message(f"Volume: {int(new_vol * 100)}%")
        except SpotifyNotRunningError:
            self.query_one(StatusBar).show_message("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self.query_one(StatusBar).show_message(str(e), is_error=True)

    def action_volume_down(self) -> None:
        try:
            current = self._player.get_volume()
            new_vol = max(current - 0.1, 0.0)
            self._player.set_volume(new_vol)
            self.query_one(StatusBar).show_message(f"Volume: {int(new_vol * 100)}%")
        except SpotifyNotRunningError:
            self.query_one(StatusBar).show_message("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self.query_one(StatusBar).show_message(str(e), is_error=True)

    def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    # ------------------------------------------------------------------
    # Search input handling
    # ------------------------------------------------------------------

    @on(Input.Submitted, "#search-input")
    def on_search_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter in the search input — play the URI."""
        uri = event.value.strip()
        if not uri:
            return

        try:
            self._search_service.open_uri(uri)
            self.query_one(StatusBar).show_message(f"Playing: {uri}")
            event.input.value = ""
        except InvalidURIError:
            self.query_one(StatusBar).show_message(
                f"Invalid URI: {uri} (expected spotify:type:id or open.spotify.com URL)",
                is_error=True,
            )
        except SpotifyNotRunningError:
            self.query_one(StatusBar).show_message("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self.query_one(StatusBar).show_message(str(e), is_error=True)


def main() -> None:
    """Entry point for the CLI."""
    app = SpotifyTuiApp()
    app.run()


if __name__ == "__main__":
    main()
