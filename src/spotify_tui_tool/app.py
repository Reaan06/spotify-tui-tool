"""Spotify TUI App — main Textual application.

Integrates the 3-panel UI layout with Sidebar, ContentArea, and Playbar.
Uses SpotifyClient for all data access and polls playerctl every 1000ms.

Keybindings:
    Space       Play/Pause
    n           Next track
    p           Previous track
    +/-         Volume up/down
    </>         Seek backward/forward
    /           Search
    1-4         Switch browse views (home/library/playlists/search)
    6-7         Switch settings/login views
    j/k         Sidebar navigation (up/down)
    h/l         Sidebar/Content focus toggle
    Esc         Back to home
    q           Quit
    ?           Help
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.timer import Timer
from textual.widgets import Footer, Header, Input

from spotify_tui_tool.auth import AuthManager, AuthResult, AuthState
from spotify_tui_tool.config import Config
from spotify_tui_tool.exceptions import (
    InvalidURIError,
    PlaybackError,
    PlayerctlNotFoundError,
    SpotifyNotRunningError,
    playback_error_message,
)
from spotify_tui_tool.models import BrowseRow, PlaybackState, PlaybackStatus
from spotify_tui_tool.playerctl import PlayerController
from spotify_tui_tool.search import SearchService
from spotify_tui_tool.spotify_client import SpotifyClient
from spotify_tui_tool.state import AppState
from spotify_tui_tool.ui.content import ContentArea
from spotify_tui_tool.ui.layout import LayoutManager
from spotify_tui_tool.ui.playbar import Playbar
from spotify_tui_tool.ui.sidebar import Sidebar, SidebarItem
from spotify_tui_tool.ui.views.home import HomeView
from spotify_tui_tool.ui.views.library import LibraryView
from spotify_tui_tool.ui.views.login import LoginView
from spotify_tui_tool.ui.views.playlists import PlaylistsView
from spotify_tui_tool.ui.views.search import SearchView
from spotify_tui_tool.ui.views.settings import SettingsView
from spotify_tui_tool.ui.rows import (
    BrowseRowActivated,
    rows_from_library,
    rows_from_playlists,
    rows_from_search,
)
from spotify_tui_tool.web_api import SpotifyWebAPI


@dataclass(frozen=True)
class BrowseRequest:
    """Identity carried with an off-thread browse request."""

    surface: str
    generation: int
    view_id: str
    query: str = ""


@dataclass(frozen=True)
class BrowseResult:
    """Worker result accepted only when its request is still current."""

    request: BrowseRequest
    rows: tuple[BrowseRow, ...] = ()
    error: str = ""


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
        Binding("plus", "volume_up", "Vol +", show=False),
        Binding("equal", "volume_up", "Vol +", show=True),
        Binding("minus", "volume_down", "Vol -", show=True),
        Binding("less_than", "seek_backward", "Seek -", show=True),
        Binding("greater_than", "seek_forward", "Seek +", show=True),
        Binding("slash", "focus_search", "Search", show=True),
        Binding("enter", "activate", "Activate", show=False),
        Binding("1", "view_home", "Home", show=True),
        Binding("2", "view_library", "Library", show=True),
        Binding("3", "view_playlists", "Playlists", show=True),
        Binding("4", "view_search", "Search View", show=True),
        Binding("6", "view_settings", "Settings", show=False),
        Binding("7", "view_login", "Login", show=False),
        Binding("j", "sidebar_down", "Down", show=False),
        Binding("k", "sidebar_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("up", "move_up", "Up", show=False),
        Binding("h", "focus_sidebar", "Sidebar", show=False),
        Binding("l", "focus_content", "Content", show=False),
        Binding("left", "focus_left", "Left", show=False),
        Binding("right", "focus_right", "Right", show=False),
        Binding("escape", "back", "Back", show=True, priority=True),
        Binding("q", "quit_or_back", "Quit", show=True, priority=True),
        Binding("r", "retry_auth", "Retry", show=False),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("question", "help", "Help", show=True),
    ]

    def __init__(
        self,
        player_name: str = "spotify",
        *,
        web_api: SpotifyWebAPI | None = None,
        auth_manager: AuthManager | None = None,
    ) -> None:
        super().__init__()
        self._client = SpotifyClient(
            player=PlayerController(player_name=player_name),
            poll_interval=1.0,
        )
        self._search_service = SearchService(player=self._client.player)
        self._poll_timer: Timer | None = None
        self._state = AppState()
        self._config = Config.load()
        self._web_api = web_api or SpotifyWebAPI()
        self._auth = auth_manager or AuthManager(api_factory=self._api_for_token)
        self._auth_generation = 0
        self._view_serial = 0
        self._active_view_id = "home:0"
        self._is_logged_in = False
        self._username = ""

    def _api_for_token(self, access_token: str) -> SpotifyWebAPI:
        """Build an API client for auth validation without touching the UI thread."""
        if self._web_api is not None:
            self._web_api._session.headers["Authorization"] = f"Bearer {access_token}"
            return self._web_api
        return SpotifyWebAPI(access_token=access_token)

    def compose(self) -> ComposeResult:
        yield Header()
        yield LayoutManager()
        yield Footer()

    def on_mount(self) -> None:
        """Keep shell composition synchronous and restore auth in a worker."""
        self._set_focus_region("sidebar")
        self._poll_timer = self.set_interval(1.0, self._schedule_poll)
        self._begin_auth_restore()

    def _schedule_poll(self) -> None:
        """Poll playerctl off the Textual event loop."""
        self.run_worker(
            self._poll_worker,
            thread=True,
            exclusive=True,
            name="spotify-playback-poll",
        )

    def _poll_worker(self) -> None:
        self._publish_from_worker(self._poll_metadata, self._client.poll())

    def _check_auth(self) -> None:
        """Compatibility entry point; restoration is always off the UI thread."""
        self._begin_auth_restore()

    def _begin_auth_restore(self) -> None:
        self._auth_generation += 1
        generation = self._auth_generation
        self._state.set_auth_state(AuthState.RESTORING.value)
        self._update_login_ui()
        self.run_worker(
            lambda: self._auth_worker(generation, self._auth.restore),
            thread=True,
            exclusive=True,
            name="spotify-auth-restore",
        )

    def _auth_worker(self, generation: int, operation) -> None:
        result = operation()
        self._publish_from_worker(self._accept_auth_result, generation, result)

    def _accept_auth_result(self, generation: int, result: AuthResult) -> None:
        if generation != self._auth_generation:
            return
        self._is_logged_in = result.state is AuthState.AUTHENTICATED
        self._username = (result.user or {}).get(
            "display_name", (result.user or {}).get("id", "")
        )
        self._state.set_auth_state(
            result.state.value,
            user=result.user,
            reason=result.reason,
        )
        if result.api is not None:
            self._web_api = result.api
        self._update_login_ui()
        if self._is_logged_in:
            self._load_web_api_data()

    def _publish_from_worker(self, callback, *args: Any) -> None:
        """Publish a worker result on the Textual thread when attached."""
        try:
            self.call_from_thread(callback, *args)
        except (RuntimeError, AttributeError):
            # Direct unit tests can exercise worker functions without a live App.
            return

    def _update_login_ui(self) -> None:
        """Update mounted authentication surfaces without blocking."""
        try:
            sidebar = self.query_one(Sidebar)
            sidebar.update_login_status(self._is_logged_in, self._username)
        except Exception:
            pass
        try:
            login = self.query_one(LoginView)
            login.set_auth_state(
                AuthState(self._state.auth_state),
                username=self._username,
                reason=self._state.auth_reason,
            )
        except Exception:
            pass

    def _load_web_api_data(self) -> None:
        """Schedule the active read-only browse surface for loading."""
        if not self._is_logged_in:
            return
        current_view = self.query_one(ContentArea).current_view
        if current_view in {"library", "playlists", "search"}:
            self._begin_browse_load(current_view)

    def _browse_view(self, surface: str):
        view_types = {
            "library": LibraryView,
            "playlists": PlaylistsView,
            "search": SearchView,
        }
        view_type = view_types.get(surface)
        if view_type is None:
            return None
        try:
            return self.query_one(view_type)
        except Exception:
            return None

    def _begin_browse_load(self, surface: str, query: str = "") -> None:
        """Start one read-only request with a generation/view identity guard."""
        if not self._is_logged_in or surface not in {"library", "playlists", "search"}:
            return
        try:
            content = self.query_one(ContentArea)
        except Exception:
            return
        if content.current_view != surface:
            return
        view = self._browse_view(surface)
        if view is None:
            return
        view.set_authenticated(True)
        view_id = self._active_view_id
        generation = self._state.begin_browse(surface, view_id)
        view.set_loading()
        request = BrowseRequest(surface, generation, view_id, query)
        self.run_worker(
            lambda: self._browse_worker(request),
            thread=True,
            exclusive=True,
            name=f"spotify-browse-{surface}",
        )

    def _browse_worker(self, request: BrowseRequest) -> BrowseResult:
        """Perform API work off the Textual event loop."""
        try:
            if request.surface == "library":
                payload = self._web_api.get_liked_songs(limit=50, offset=0)
                rows = rows_from_library(payload)
            elif request.surface == "playlists":
                payload = self._web_api.get_playlists(limit=50, offset=0)
                rows = rows_from_playlists(payload)
            else:
                payload = self._web_api.search(
                    request.query,
                    types="track,album,artist",
                    limit=20,
                    offset=0,
                )
                rows = rows_from_search(payload)
            result = BrowseResult(request, tuple(rows))
        except Exception as exc:
            result = BrowseResult(request, error=str(exc))
        self._publish_from_worker(self._accept_browse_result, result)
        return result

    def _accept_browse_result(self, result: BrowseResult) -> None:
        """Apply only results for the newest request and active view instance."""
        request = result.request
        try:
            content = self.query_one(ContentArea)
        except Exception:
            return
        if (
            content.current_view != request.surface
            or self._active_view_id != request.view_id
        ):
            return
        view = self._browse_view(request.surface)
        if view is None:
            return
        if result.error:
            if self._state.reject_browse_result(
                request.surface,
                request.generation,
                request.view_id,
                result.error,
            ):
                view.set_error(result.error)
            return
        if self._state.accept_browse_result(
            request.surface,
            request.generation,
            request.view_id,
            list(result.rows),
        ):
            view.set_rows(list(result.rows))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _show_status(self, text: str, is_error: bool = False) -> None:
        """Update the playbar or log a status message."""
        try:
            playbar = self.query_one(Playbar)
            playbar.set_status(f"[red]{text}[/red]" if is_error else text)
        except Exception:
            pass

    def _poll_metadata(self, info=None) -> None:
        """Poll playerctl for current track metadata and update all views."""
        if info is None:
            info = self._client.poll()
        is_playing = info.status == PlaybackStatus.PLAYING
        self._state.set_track(info)
        self._state.set_playing(is_playing)
        self._state.set_volume(info.volume)

        # Update playbar
        try:
            playbar = self.query_one(Playbar)
            playbar.update_track(info, is_playing)
            playbar.volume = info.volume
            if info.playback_state is PlaybackState.STALE:
                playbar.set_status("Playback stale: showing last known track.")
            elif info.playback_state is PlaybackState.UNAVAILABLE:
                playbar.set_status(info.playback_message or "Playback unavailable.")
            elif info.playback_state is PlaybackState.STOPPED:
                playbar.set_status("Playback stopped.")
        except Exception:
            pass

        # Update home view
        try:
            home = self.query_one(HomeView)
            home.update_track(info, is_playing)
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
        except (PlayerctlNotFoundError, SpotifyNotRunningError, PlaybackError) as e:
            self._show_status(playback_error_message(e), is_error=True)

    def action_next_track(self) -> None:
        try:
            self._client.next_track()
            self._show_status("Next track")
        except (PlayerctlNotFoundError, SpotifyNotRunningError, PlaybackError) as e:
            self._show_status(playback_error_message(e), is_error=True)

    def action_previous_track(self) -> None:
        try:
            self._client.previous_track()
            self._show_status("Previous track")
        except (PlayerctlNotFoundError, SpotifyNotRunningError, PlaybackError) as e:
            self._show_status(playback_error_message(e), is_error=True)

    def action_volume_up(self) -> None:
        try:
            current = self._client.get_volume()
            new_vol = min(current + 0.1, 1.0)
            self._client.set_volume(new_vol)
            self._show_status(f"Volume: {int(new_vol * 100)}%")
        except (PlayerctlNotFoundError, SpotifyNotRunningError, PlaybackError) as e:
            self._show_status(playback_error_message(e), is_error=True)

    def action_volume_down(self) -> None:
        try:
            current = self._client.get_volume()
            new_vol = max(current - 0.1, 0.0)
            self._client.set_volume(new_vol)
            self._show_status(f"Volume: {int(new_vol * 100)}%")
        except (PlayerctlNotFoundError, SpotifyNotRunningError, PlaybackError) as e:
            self._show_status(playback_error_message(e), is_error=True)

    def action_seek_forward(self) -> None:
        try:
            self._client.seek(self._config.seek_milliseconds)
            self._show_status(f"Seek +{self._config.seek_milliseconds}ms")
        except (PlayerctlNotFoundError, SpotifyNotRunningError, PlaybackError) as e:
            self._show_status(playback_error_message(e), is_error=True)

    def action_seek_backward(self) -> None:
        try:
            self._client.seek(-self._config.seek_milliseconds)
            self._show_status(f"Seek -{self._config.seek_milliseconds}ms")
        except (PlayerctlNotFoundError, SpotifyNotRunningError, PlaybackError) as e:
            self._show_status(playback_error_message(e), is_error=True)

    # ------------------------------------------------------------------
    # View switching
    # ------------------------------------------------------------------

    async def action_view_home(self) -> None:
        await self._switch_view("home")

    async def action_view_library(self) -> None:
        await self._switch_view("library")

    async def action_view_playlists(self) -> None:
        await self._switch_view("playlists")

    async def action_view_search(self) -> None:
        await self._switch_view("search")

    async def action_view_settings(self) -> None:
        await self._switch_view("settings")

    async def action_view_login(self) -> None:
        await self._switch_view("login")

    async def action_help(self) -> None:
        await self._switch_view("help", transient=True)

    async def action_back(self) -> None:
        target = self._state.pop_transient()
        if target is None:
            return
        await self._switch_view(target, remember=False)

    async def _switch_view(
        self,
        view: str,
        *,
        transient: bool = False,
        remember: bool = True,
        focus_region: str = "content",
    ) -> None:
        content = self.query_one(ContentArea)
        current = content.current_view
        if current == view:
            return
        if transient:
            self._state.push_transient(view, current)
        elif remember:
            self._state.view_history.clear()
            self._state.transient_view = None
        self._state.set_view(view)
        await content.switch_view(view)
        self._view_serial += 1
        self._active_view_id = f"{view}:{self._view_serial}"
        self._set_focus_region(focus_region)
        if view in {"library", "playlists", "search"} and self._is_logged_in:
            self._begin_browse_load(view)

    async def action_quit_or_back(self) -> None:
        if self._state.view_history:
            await self.action_back()
            return
        self.exit()

    async def action_activate(self) -> None:
        if self._state.focus_region == "sidebar":
            self.query_one(Sidebar).activate_selection()
        elif self._state.focus_region == "content":
            content = self.query_one(ContentArea)
            if content.current_view == "login":
                self.query_one(LoginView).request_login()
            else:
                selection = content.activate_focused()
                if isinstance(selection, BrowseRow):
                    self._activate_row(selection)
                else:
                    self._show_status(f"Selected {selection}")

    def _activate_row(self, row: BrowseRow) -> None:
        result = self._client.activate_row(row)
        self._show_status(result.message, is_error=not result.success)

    @on(BrowseRowActivated)
    def on_browse_row_activated(self, event: BrowseRowActivated) -> None:
        """Use the same stored-identity path for keyboard and double-click."""
        self._activate_row(event.row)

    def action_retry_auth(self) -> None:
        """Retry auth validation or the active browse surface explicitly."""
        if self._state.auth_state != AuthState.AUTHENTICATED.value:
            self._begin_auth_restore()
            return
        try:
            current_view = self.query_one(ContentArea).current_view
        except Exception:
            return
        if current_view in {"library", "playlists", "search"}:
            self._begin_browse_load(current_view)

    # ------------------------------------------------------------------
    # Sidebar navigation
    # ------------------------------------------------------------------

    def action_sidebar_down(self) -> None:
        self.action_move_down()

    def action_sidebar_up(self) -> None:
        self.action_move_up()

    def action_move_down(self) -> None:
        if self._state.focus_region == "sidebar":
            sidebar = self.query_one(Sidebar)
            sidebar.move_selection(1)
            self._state.set_sidebar_selection(sidebar.current_section, sidebar.selected_index)
        elif self._state.focus_region == "content":
            self.query_one(ContentArea).move_selection(1)

    def action_move_up(self) -> None:
        if self._state.focus_region == "sidebar":
            sidebar = self.query_one(Sidebar)
            sidebar.move_selection(-1)
            self._state.set_sidebar_selection(sidebar.current_section, sidebar.selected_index)
        elif self._state.focus_region == "content":
            self.query_one(ContentArea).move_selection(-1)

    def action_focus_sidebar(self) -> None:
        self._set_focus_region("sidebar")

    def action_focus_content(self) -> None:
        self._set_focus_region("content")

    def action_focus_left(self) -> None:
        regions = ["sidebar", "content", "playbar"]
        index = regions.index(self._state.focus_region)
        self._set_focus_region(regions[max(0, index - 1)])

    def action_focus_right(self) -> None:
        regions = ["sidebar", "content", "playbar"]
        index = regions.index(self._state.focus_region)
        self._set_focus_region(regions[min(len(regions) - 1, index + 1)])

    def _set_focus_region(self, region: str) -> None:
        targets = {
            "sidebar": Sidebar,
            "content": ContentArea,
            "playbar": Playbar,
        }
        target_cls = targets.get(region)
        if target_cls is None:
            return
        target = self.query_one(target_cls)
        target.focus()
        self._state.set_focus_region(region)
        for name, cls in targets.items():
            widget = self.query_one(cls)
            if name == region:
                widget.add_class("focus-region")
            else:
                widget.remove_class("focus-region")

    async def action_focus_search(self) -> None:
        await self._switch_view("search", transient=True)
        input_widget = self.query_one("#search-input", Input)
        input_widget.focus()
        self._state.set_focus_region("content")

    @on(SidebarItem.Selected)
    def on_sidebar_item_selected(self, event: SidebarItem.Selected) -> None:
        self._state.set_sidebar_selection(event.section, self.query_one(Sidebar).selected_index)
        self._set_focus_region("sidebar")
        if event.view:
            self.run_worker(self._switch_view(event.view, focus_region="sidebar"))

    @on(Input.Changed, "#search-input")
    def on_search_input_changed(self, event: Input.Changed) -> None:
        """Keep q available for closing the transient search surface."""
        if event.value == "q" and self._state.transient_view == "search":
            event.input.value = ""
            self.run_worker(self.action_back())

    # ------------------------------------------------------------------
    # Search input handling
    # ------------------------------------------------------------------

    @on(Input.Submitted, "#search-input")
    def on_search_submitted(self, event: Input.Submitted) -> None:
        """Schedule a read-only search without blocking Textual input."""
        query = event.value.strip()
        if not query:
            return

        if not self._is_logged_in:
            self._show_status("Login to search Spotify", is_error=True)
            return
        self._state.search_query = query
        self._begin_browse_load("search", query)
        self._show_status(f"Searching Spotify for: {query}")

    # ------------------------------------------------------------------
    # Login handling
    # ------------------------------------------------------------------

    @on(LoginView.LoginRequested)
    def on_login_requested(self, event: LoginView.LoginRequested) -> None:
        """Handle login by running OAuth and validation in a worker thread."""
        self._auth_generation += 1
        generation = self._auth_generation
        self._state.set_auth_state(AuthState.AUTHENTICATING.value)
        self._update_login_ui()
        self._show_status("Starting Spotify login…")
        self.run_worker(
            lambda: self._auth_worker(generation, self._auth.login),
            thread=True,
            exclusive=True,
            name="spotify-auth-login",
        )

    # ------------------------------------------------------------------
    # Search result selection
    # ------------------------------------------------------------------

    @on(SearchView.ResultSelected)
    def on_search_result_selected(self, event: SearchView.ResultSelected) -> None:
        """Keep browse selection separate from the later playback slice."""
        if event.uri:
            self._show_status("Browse selection retained; playback is separate.")


def main() -> None:
    """Entry point for the CLI."""
    app = SpotifyTuiApp()
    app.run()


if __name__ == "__main__":
    main()
