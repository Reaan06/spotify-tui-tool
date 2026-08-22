"""OAuth2 PKCE authentication for the Spotify Web API.

Flow:
1. Generate code_verifier + code_challenge (S256)
2. Start a local HTTP server on 127.0.0.1:8888
3. Open the browser for user authorization
4. Capture the callback with the auth code
5. Exchange code for tokens (access + refresh)
6. Store tokens in ~/.config/spotify-tui-tool/tokens.json
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import secrets
import time
import base64
from dataclasses import dataclass
from enum import Enum
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlencode, urlparse, parse_qs

import requests

CLIENT_ID = "d8a5ed958d274c2e8ee717e6a4b0971d"
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPES = (
    "user-read-private user-library-read playlist-read-private "
    "playlist-read-collaborative"
)

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"

TOKEN_DIR = Path.home() / ".config" / "spotify-tui-tool"
TOKEN_FILE = TOKEN_DIR / "tokens.json"


class AuthState(str, Enum):
    """Observable authentication lifecycle states."""

    UNAUTHENTICATED = "unauthenticated"
    RESTORING = "restoring"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    INVALID_EXPIRED = "invalid/expired"


# The longer name is useful to callers that model the lifecycle explicitly.
AuthLifecycle = AuthState

AUTH_COPY = {
    AuthState.UNAUTHENTICATED: "Not signed in. Press Enter to log in.",
    AuthState.RESTORING: "Restoring Spotify session…",
    AuthState.AUTHENTICATING: "Waiting for Spotify login…",
    AuthState.INVALID_EXPIRED: (
        "Spotify session is invalid or expired. Press Enter to log in or r to retry."
    ),
}


def auth_message(state: AuthState | str, username: str = "") -> str:
    """Return the exact user-facing copy for an authentication state."""
    resolved = state if isinstance(state, AuthState) else AuthState(state)
    if resolved is AuthState.AUTHENTICATED:
        return f"Signed in as {username}." if username else "Signed in."
    return AUTH_COPY[resolved]


@dataclass(frozen=True)
class AuthResult:
    """Result returned by a synchronous auth operation run in a worker."""

    state: AuthState
    user: Optional[dict[str, Any]] = None
    tokens: Optional[dict[str, Any]] = None
    api: Any = None
    reason: str = ""

    @property
    def message(self) -> str:
        user = self.user or {}
        return auth_message(self.state, user.get("display_name") or user.get("id", ""))


def _generate_pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for PKCE."""
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _build_auth_url(code_challenge: str, state: str | None = None) -> str:
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "code_challenge_method": "S256",
        "code_challenge": code_challenge,
        "show_dialog": "true",
    }
    if state:
        params["state"] = state
    return f"{AUTH_URL}?{urlencode(params)}"


def _exchange_code(code: str, code_verifier: str) -> dict:
    resp = requests.post(TOKEN_URL, data={
        "client_id": CLIENT_ID,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
    }, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    data["obtained_at"] = time.time()
    return data


def refresh_access_token(refresh_token: str) -> dict:
    resp = requests.post(TOKEN_URL, data={
        "client_id": CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    data["obtained_at"] = time.time()
    if "refresh_token" not in data:
        data["refresh_token"] = refresh_token
    return data


def save_tokens(token_data: dict) -> None:
    token_dir = TOKEN_FILE.parent
    token_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(token_dir, 0o700)
    with TOKEN_FILE.open("w") as token_file:
        json.dump(token_data, token_file, indent=2)
    os.chmod(TOKEN_FILE, 0o600)


def load_tokens() -> Optional[dict]:
    if not TOKEN_FILE.exists():
        return None
    try:
        return json.loads(TOKEN_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def is_token_expired(token_data: dict) -> bool:
    expires_in = token_data.get("expires_in", 0)
    obtained_at = token_data.get("obtained_at", 0)
    return time.time() > obtained_at + expires_in - 60


def get_valid_token() -> Optional[str]:
    """Return a valid access token, refreshing if necessary."""
    tokens = load_tokens()
    if tokens is None:
        return None
    if is_token_expired(tokens):
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            return None
        tokens = refresh_access_token(refresh_token)
        save_tokens(tokens)
    return tokens.get("access_token")


class AuthManager:
    """Coordinate authentication lifecycle transitions.

    The manager is synchronous by design: callers run it in a worker thread
    and publish the returned ``AuthResult`` on the Textual thread.  Persisted
    token presence is only an input to restoration; ``/me`` validation is the
    point at which a session becomes authenticated.
    """

    def __init__(
        self,
        *,
        token_loader: Callable[[], Optional[dict[str, Any]]] = load_tokens,
        token_saver: Callable[[dict[str, Any]], None] = save_tokens,
        api_factory: Optional[Callable[..., Any]] = None,
        authenticate_fn: Optional[Callable[[], dict[str, Any]]] = None,
    ) -> None:
        self._token_loader = token_loader
        self._token_saver = token_saver
        self._api_factory = api_factory or self._default_api_factory
        self._authenticate_fn = authenticate_fn
        self.state = AuthState.UNAUTHENTICATED
        self.user: Optional[dict[str, Any]] = None
        self.tokens: Optional[dict[str, Any]] = None
        self.api: Any = None
        self.reason = ""

    @staticmethod
    def _default_api_factory(access_token: str) -> Any:
        # Import lazily to avoid the auth <-> web_api import cycle.
        from spotify_tui_tool.web_api import SpotifyWebAPI

        return SpotifyWebAPI(access_token=access_token)

    def _result(
        self,
        state: AuthState,
        *,
        user: Optional[dict[str, Any]] = None,
        tokens: Optional[dict[str, Any]] = None,
        api: Any = None,
        reason: str = "",
    ) -> AuthResult:
        self.state = state
        self.user = user
        self.tokens = tokens
        self.api = api
        self.reason = reason
        return AuthResult(state, user, tokens, api, reason)

    def restore(self) -> AuthResult:
        """Load persisted credentials and validate them with ``/me``."""
        self.state = AuthState.RESTORING
        try:
            tokens = self._token_loader()
        except Exception as exc:
            return self._result(
                AuthState.INVALID_EXPIRED,
                reason=str(exc),
            )

        access_token = (tokens or {}).get("access_token")
        if not access_token:
            return self._result(AuthState.UNAUTHENTICATED)

        try:
            api = self._api_factory(access_token)
            user = api.get_current_user()
        except Exception as exc:
            return self._result(
                AuthState.INVALID_EXPIRED,
                tokens=tokens,
                reason=str(exc),
            )
        return self._result(
            AuthState.AUTHENTICATED,
            user=user,
            tokens=tokens,
            api=api,
        )

    def retry_restore(self) -> AuthResult:
        """Retry restoration once when the user explicitly requests it."""
        return self.restore()

    def login(self) -> AuthResult:
        """Run OAuth, then validate the resulting session with ``/me``."""
        self.state = AuthState.AUTHENTICATING
        authenticate_fn = self._authenticate_fn or authenticate
        try:
            tokens = authenticate_fn()
            access_token = (tokens or {}).get("access_token")
            if not access_token:
                raise RuntimeError("Spotify login did not return an access token")
            api = self._api_factory(access_token)
            user = api.get_current_user()
            # The built-in authenticate function already persists tokens.  A
            # test or alternate OAuth provider may not, so persist here too.
            self._token_saver(tokens)
        except Exception as exc:
            return self._result(
                AuthState.UNAUTHENTICATED,
                reason=str(exc),
            )
        return self._result(
            AuthState.AUTHENTICATED,
            user=user,
            tokens=tokens,
            api=api,
        )


class _CallbackHandler(BaseHTTPRequestHandler):
    """Minimal handler that captures the ?code= query param."""

    auth_code: Optional[str] = None
    callback_error: Optional[str] = None
    expected_state: Optional[str] = None

    @classmethod
    def reset(cls, expected_state: str) -> None:
        cls.auth_code = None
        cls.callback_error = None
        cls.expected_state = expected_state

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        qs = parse_qs(parsed.query)
        state = qs.get("state", [None])[0]
        if state != _CallbackHandler.expected_state:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h1>Authentication failed: invalid state.</h1>")
            return
        code = qs.get("code", [None])[0]
        if code:
            _CallbackHandler.auth_code = code
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authentication successful! You can close this tab.</h1>")
        else:
            error = qs.get("error", ["unknown"])[0]
            _CallbackHandler.callback_error = error
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            safe_error = html.escape(error)
            self.wfile.write(f"<h1>Authentication failed: {safe_error}</h1>".encode())
        # Shut down after receiving callback
        import threading
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    def log_message(self, format, *args):
        pass  # Silence request logs


def authenticate() -> dict:
    """Run the full OAuth2 PKCE flow and return token data.

    Returns:
        dict with access_token, refresh_token, expires_in, obtained_at

    Raises:
        RuntimeError: if the auth code cannot be obtained or exchanged
    """
    code_verifier, code_challenge = _generate_pkce_pair()
    oauth_state = secrets.token_urlsafe(32)
    auth_url = _build_auth_url(code_challenge, oauth_state)

    _CallbackHandler.reset(oauth_state)
    try:
        server = HTTPServer(("127.0.0.1", 8888), _CallbackHandler)
    except OSError as exc:
        raise RuntimeError(
            "Unable to start Spotify OAuth callback server on 127.0.0.1:8888"
        ) from exc
    server.timeout = 1

    import webbrowser
    try:
        webbrowser.open(auth_url)
        deadline = time.monotonic() + 120
        while (
            _CallbackHandler.auth_code is None
            and _CallbackHandler.callback_error is None
            and time.monotonic() < deadline
        ):
            server.handle_request()
    finally:
        server.server_close()

    if _CallbackHandler.callback_error:
        raise RuntimeError(
            f"Spotify authorization failed: {_CallbackHandler.callback_error}"
        )
    code = _CallbackHandler.auth_code
    if code is None:
        raise RuntimeError("Failed to obtain authorization code from callback")

    token_data = _exchange_code(code, code_verifier)
    save_tokens(token_data)
    return token_data
