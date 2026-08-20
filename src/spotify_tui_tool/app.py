"""Spotify TUI App — main Textual application.

Integrates the 3-panel UI layout with Sidebar, ContentArea, and Playbar.
Uses SpotifyClient for all data access and polls playerctl every 1000ms.

Keybindings:
    Space       Play/Pause
    n           Next track
    p           Previous track
    +/-         Volume up/down
    </>         Seek backward/forward
    F           Like/Unlike
    /           Search
    1-6         Switch views (home/library/playlists/search/queue/settings)
    j/k         Sidebar navigation (up/down)
    h/l         Sidebar/Content focus toggle
    Esc         Back to home
    q           Quit
    ?           Help
"""

from __future__ import annotations

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.timer import Timer
from textual.widgets import Footer, Header, Input

from spotify_tui_tool.config import Config
from spotify_tui_tool.exceptions import (
    InvalidURIError,
    PlaybackError,
    PlayerctlNotFoundError,
    SpotifyNotRunningError,
)
from spotify_tui_tool.models import PlaybackStatus
from spotify_tui_tool.playerctl import PlayerController
from spotify_tui_tool.search import SearchService
from spotify_tui_tool.spotify_client import SpotifyClient
from spotify_tui_tool.state import AppState
from spotify_tui_tool.ui.content import ContentArea
from spotify_tui_tool.ui.layout import LayoutManager
from spotify_tui_tool.ui.playbar import Playbar
from spotify_tui_tool.ui.sidebar import Sidebar
from spotify_tui_tool.ui.views.home import HomeView
from spotify_tui_tool.ui.views.queue import QueueView
from spotify_tui_tool.ui.views.settings import SettingsView


# ------------------------------------------------------------------
# Main App
# ------------------------------------------------------------------

class SpotifyTuiApp(App):
    """Textual app for controlling SpotX-patched Spotify via playerctl."""

    TITLE = "Spotify TUI"

    BINDINGS = [
        Binding("space", "play_pause", "Play/Pause", show=True),
        Binding("n", "next_track", "Next", show=True),
        Binding("p", "previous_track", "Previous", show=True),
        Binding("equal", "volume_up", "Vol +", show=True),
        Binding("minus", "volume_down", "Vol -", show=True),
        Binding("less_than", "seek_backward", "Seek -", show=True),
        Binding("greater_than", "seek_forward", "Seek +", show=True),
        Binding("f", "like", "Like", show=True),
        Binding("slash", "focus_search", "Search", show=True),
        Binding("1", "view_home", "Home", show=True),
        Binding("2", "view_library", "Library", show=True),
        Binding("3", "view_playlists", "Playlists", show=True),
        Binding("4", "view_search", "Search View", show=True),
        Binding("5", "view_queue", "Queue", show=True),
        Binding("6", "view_settings", "Settings", show=True),
        Binding("j", "sidebar_down", "Down", show=False),
        Binding("k", "sidebar_up", "Up", show=False),
        Binding("h", "focus_sidebar", "Sidebar", show=False),
        Binding("l", "focus_content", "Content", show=False),
        Binding("escape", "back", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("question", "help", "Help", show=True),
    ]

    def __init__(self, player_name: str = "spotify") -> None:
        super().__init__()
        self._client = SpotifyClient(
            player=PlayerController(player_name=player_name),
            poll_interval=1.0,
        )
        self._search_service = SearchService(player=self._client.player)
        self._poll_timer: Timer | None = None
        self._state = AppState()
        self._config = Config.load()

    def compose(self) -> ComposeResult:
        yield Header()
        yield LayoutManager()
        yield Footer()

    def on_mount(self) -> None:
        """Mount UI components into layout slots and start polling."""
        layout = self.query_one(LayoutManager)
        sidebar = Sidebar()
        playbar = Playbar()
        content = ContentArea()

        layout.query_one("#sidebar").mount(sidebar)
        layout.query_one("#playbar").mount(playbar)
        layout.query_one("#content").mount(content)

        self._poll_timer = self.set_interval(1.0, self._poll_metadata)
        self._poll_metadata()
        self._show_status("Ready. Press / to search, ? for help.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _show_status(self, text: str, is_error: bool = False) -> None:
        """Update the playbar or log a status message."""
        try:
            playbar = self.query_one(Playbar)
            if is_error:
                playbar.query_one("#controls-area").update(f"[red]{text}[/red]")
            else:
                playbar.query_one("#controls-area").update(text)
        except Exception:
            pass

    def _poll_metadata(self) -> None:
        """Poll playerctl for current track metadata and update all views."""
        info = self._client.poll()
        is_playing = info.status == PlaybackStatus.PLAYING

        # Update playbar
        try:
            playbar = self.query_one(Playbar)
            playbar.update_track(info, is_playing)
            playbar.volume = info.volume
        except Exception:
            pass

        # Update home view
        try:
            home = self.query_one(HomeView)
            home.update_track(info, is_playing)
        except Exception:
            pass

        # Update queue view
        try:
            queue = self.query_one(QueueView)
            queue.update_queue(self._client.get_queue())
        except Exception:
            pass

        # Update settings view
        try:
            settings = self.query_one(SettingsView)
            settings.update_config(self._config)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Transport actions
    # ------------------------------------------------------------------

    def action_play_pause(self) -> None:
        try:
            self._client.play_pause()
            self._show_status("Toggled play/pause")
        except SpotifyNotRunningError:
            self._show_status("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self._show_status(str(e), is_error=True)

    def action_next_track(self) -> None:
        try:
            self._client.next_track()
            self._show_status("Next track")
        except SpotifyNotRunningError:
            self._show_status("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self._show_status(str(e), is_error=True)

    def action_previous_track(self) -> None:
        try:
            self._client.previous_track()
            self._show_status("Previous track")
        except SpotifyNotRunningError:
            self._show_status("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self._show_status(str(e), is_error=True)

    def action_volume_up(self) -> None:
        try:
            current = self._client.get_volume()
            new_vol = min(current + 0.1, 1.0)
            self._client.set_volume(new_vol)
            self._show_status(f"Volume: {int(new_vol * 100)}%")
        except SpotifyNotRunningError:
            self._show_status("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self._show_status(str(e), is_error=True)

    def action_volume_down(self) -> None:
        try:
            current = self._client.get_volume()
            new_vol = max(current - 0.1, 0.0)
            self._client.set_volume(new_vol)
            self._show_status(f"Volume: {int(new_vol * 100)}%")
        except SpotifyNotRunningError:
            self._show_status("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self._show_status(str(e), is_error=True)

    def action_seek_forward(self) -> None:
        try:
            self._client.seek(self._config.seek_milliseconds)
            self._show_status(f"Seek +{self._config.seek_milliseconds}ms")
        except SpotifyNotRunningError:
            self._show_status("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self._show_status(str(e), is_error=True)

    def action_seek_backward(self) -> None:
        try:
            self._client.seek(-self._config.seek_milliseconds)
            self._show_status(f"Seek -{self._config.seek_milliseconds}ms")
        except SpotifyNotRunningError:
            self._show_status("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self._show_status(str(e), is_error=True)

    def action_like(self) -> None:
        self._show_status("Like/Unlike — not yet implemented")

    # ------------------------------------------------------------------
    # View switching
    # ------------------------------------------------------------------

    def action_view_home(self) -> None:
        self._switch_view("home")

    def action_view_library(self) -> None:
        self._switch_view("library")

    def action_view_playlists(self) -> None:
        self._switch_view("playlists")

    def action_view_search(self) -> None:
        self._switch_view("search")

    def action_view_queue(self) -> None:
        self._switch_view("queue")

    def action_view_settings(self) -> None:
        self._switch_view("settings")

    async def action_help(self) -> None:
        await self._switch_view("help")

    async def action_back(self) -> None:
        await self._switch_view("home")

    async def _switch_view(self, view: str) -> None:
        self._state.set_view(view)
        try:
            content = self.query_one(ContentArea)
            await content.switch_view(view)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Sidebar navigation
    # ------------------------------------------------------------------

    def action_sidebar_down(self) -> None:
        try:
            sidebar = self.query_one(Sidebar)
            sidebar.move_selection(1)
        except Exception:
            pass

    def action_sidebar_up(self) -> None:
        try:
            sidebar = self.query_one(Sidebar)
            sidebar.move_selection(-1)
        except Exception:
            pass

    def action_focus_sidebar(self) -> None:
        try:
            sidebar = self.query_one(Sidebar)
            sidebar.focus()
        except Exception:
            pass

    def action_focus_content(self) -> None:
        try:
            content = self.query_one(ContentArea)
            content.focus()
        except Exception:
            pass

    async def action_focus_search(self) -> None:
        try:
            await self._switch_view("search")
            input_widget = self.query_one("#search-input", Input)
            input_widget.focus()
        except Exception:
            pass

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
            self._show_status(f"Playing: {uri}")
            event.input.value = ""
        except InvalidURIError:
            self._show_status(
                f"Invalid URI: {uri} (expected spotify:type:id or open.spotify.com URL)",
                is_error=True,
            )
        except SpotifyNotRunningError:
            self._show_status("Spotify is not running", is_error=True)
        except PlaybackError as e:
            self._show_status(str(e), is_error=True)


def main() -> None:
    """Entry point for the CLI."""
    app = SpotifyTuiApp()
    app.run()


if __name__ == "__main__":
    main()
