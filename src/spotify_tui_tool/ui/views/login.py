"""Explicit authentication lifecycle view."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Static

from spotify_tui_tool.auth import AuthState, auth_message


class LoginView(Widget):
    """Render authentication state without treating token presence as success."""

    DEFAULT_CSS = """
    LoginView {
        height: 100%;
        width: 100%;
        padding: 2 4;
    }

    #login-container {
        height: auto;
        width: 100%;
        align: center middle;
        padding: 2;
    }

    #login-title {
        text-style: bold;
        color: $primary;
        width: 100%;
        text-align: center;
        margin-bottom: 1;
    }

    #login-instructions,
    #login-status {
        width: 100%;
        text-align: center;
        margin-bottom: 2;
    }

    #login-button {
        width: 30;
        max-width: 100%;
        margin: 0 0;
    }
    """

    class LoginRequested(Message):
        """Emitted when the user explicitly starts OAuth."""

    is_logged_in: reactive[bool] = reactive(False)
    username: reactive[str] = reactive("")
    auth_state: reactive[AuthState] = reactive(AuthState.UNAUTHENTICATED)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._login_callbacks = []

    def compose(self) -> ComposeResult:
        with Vertical(id="login-container"):
            yield Static("[bold]Spotify login[/bold]", id="login-title")
            yield Static(
                "Sign in to browse your library, playlists, and search results.",
                id="login-instructions",
            )
            yield Static(auth_message(AuthState.UNAUTHENTICATED), id="login-status")
            yield Button("Login with Spotify", id="login-button")

    def on_mount(self) -> None:
        self._render_auth_state()
        # Textual's Button.press queues a message in newer releases.  Keep the
        # small legacy test hook deterministic while normal mouse/keyboard
        # events continue through ``on_button_pressed``.
        try:
            button = self.query_one("#login-button", Button)
            button.press = lambda: self.request_login()
        except Exception:
            return

    def set_auth_state(
        self,
        state: AuthState | str,
        *,
        username: str = "",
        reason: str = "",
    ) -> None:
        resolved = state if isinstance(state, AuthState) else AuthState(state)
        self.auth_state = resolved
        self.is_logged_in = resolved is AuthState.AUTHENTICATED
        self.username = username if self.is_logged_in else ""
        self._render_auth_state(reason=reason)

    def update_login_status(self, logged_in: bool, username: str = "") -> None:
        """Compatibility adapter for the shell's sidebar/login updates."""
        self.set_auth_state(
            AuthState.AUTHENTICATED if logged_in else AuthState.UNAUTHENTICATED,
            username=username,
        )

    def _render_auth_state(self, *, reason: str = "") -> None:
        try:
            status = self.query_one("#login-status", Static)
            text = auth_message(self.auth_state, self.username)
            if reason and self.auth_state is not AuthState.AUTHENTICATED:
                text = f"{text}\nReason: {reason}"
            status.update(text)
            button = self.query_one("#login-button", Button)
            button.disabled = self.auth_state in {
                AuthState.RESTORING,
                AuthState.AUTHENTICATING,
            }
        except Exception:
            # State can be set by a worker before this view is mounted.
            return

    def request_login(self) -> None:
        message = self.LoginRequested()
        for callback in self._login_callbacks:
            callback(message)
        self.post_message(message)

    def on(self, event_name: str, callback) -> None:
        """Small compatibility hook for the legacy view tests."""
        if event_name in {"LoginView.LoginRequested", "LoginRequested"}:
            self._login_callbacks.append(callback)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-button":
            self.request_login()
