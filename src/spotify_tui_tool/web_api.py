"""Read-only Spotify Web API client.

Thin wrapper around ``requests`` that handles auth headers, token refresh,
and converts JSON responses into plain dicts or dataclass instances.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from spotify_tui_tool.auth import (
    SCOPES,
    get_valid_token,
    load_tokens,
    refresh_access_token,
    save_tokens,
)

BASE_URL = "https://api.spotify.com/v1"
READ_ONLY_SCOPES = SCOPES
BROWSE_WINDOWS = {
    "current_user": (1, 0),
    "library": (50, 0),
    "playlists": (50, 0),
    "search": (20, 0),
}


class SpotifyWebAPI:
    """Authenticated client for the Spotify Web API."""

    def __init__(self, access_token: Optional[str] = None) -> None:
        self._session = requests.Session()
        if access_token:
            self._session.headers["Authorization"] = f"Bearer {access_token}"

    def _ensure_auth(self) -> None:
        token = get_valid_token()
        if token:
            self._session.headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        self._ensure_auth()
        resp = self._session.get(f"{BASE_URL}{path}", params=params, timeout=10)
        if resp.status_code == 401:
            tokens = load_tokens()
            if tokens:
                new = refresh_access_token(tokens["refresh_token"])
                save_tokens(new)
                self._session.headers["Authorization"] = f"Bearer {new['access_token']}"
                resp = self._session.get(f"{BASE_URL}{path}", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # User profile
    # ------------------------------------------------------------------

    def get_current_user(self) -> Dict[str, Any]:
        return self._get("/me")

    def validate_session(self) -> Dict[str, Any]:
        """Validate that the current access token can call the Web API."""
        return self.get_current_user()

    # ------------------------------------------------------------------
    # Library
    # ------------------------------------------------------------------

    def get_liked_songs(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        data = self._get("/me/tracks", {"limit": limit, "offset": offset})
        return data.get("items", [])

    # ------------------------------------------------------------------
    # Playlists
    # ------------------------------------------------------------------

    def get_playlists(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        data = self._get("/me/playlists", {"limit": limit, "offset": offset})
        return data.get("items", [])

    def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        return self._get(f"/playlists/{playlist_id}")

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, types: str = "track,album,artist",
               limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        return self._get("/search", {
            "q": query, "type": types, "limit": limit, "offset": offset,
        })

    # ------------------------------------------------------------------
    # Top items
    # ------------------------------------------------------------------

    def get_top_tracks(self, limit: int = 20, time_range: str = "medium_term") -> List[Dict[str, Any]]:
        data = self._get("/me/top/tracks", {"limit": limit, "time_range": time_range})
        return data.get("items", [])

    # ------------------------------------------------------------------
    # Artists / Albums
    # ------------------------------------------------------------------

    def get_artist(self, artist_id: str) -> Dict[str, Any]:
        return self._get(f"/artists/{artist_id}")

    def get_album(self, album_id: str) -> Dict[str, Any]:
        return self._get(f"/albums/{album_id}")
