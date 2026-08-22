"""Tests for SpotifyWebAPI — mocked HTTP responses."""

import unittest
from unittest.mock import MagicMock, patch

import requests

from spotify_tui_tool.auth import SCOPES
from spotify_tui_tool.exceptions import SpotifyRateLimitError
from spotify_tui_tool.web_api import SpotifyWebAPI, BASE_URL


def _mock_response(json_data, status_code=200):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.content = b'{"ok": true}' if json_data else b''
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(response=resp)
    return resp


class TestConstruction(unittest.TestCase):

    def test_creates_session(self):
        api = SpotifyWebAPI(access_token="tok123")
        self.assertEqual(api._session.headers["Authorization"], "Bearer tok123")

    def test_no_auth_header_when_no_token(self):
        api = SpotifyWebAPI()
        self.assertNotIn("Authorization", api._session.headers)

    @patch("spotify_tui_tool.web_api.get_valid_token", return_value="persisted")
    def test_constructor_token_is_not_overwritten_by_persisted_token(self, mock_token):
        api = SpotifyWebAPI(access_token="constructor")
        api._ensure_auth()
        self.assertEqual(api._session.headers["Authorization"], "Bearer constructor")
        mock_token.assert_not_called()

    def test_browse_scopes_are_read_only_and_exact(self):
        self.assertEqual(
            SCOPES,
            "user-read-private user-library-read playlist-read-private "
            "playlist-read-collaborative",
        )


class TestGetCurrentUser(unittest.TestCase):

    @patch.object(SpotifyWebAPI, "_get")
    def test_returns_user(self, mock_get):
        mock_get.return_value = {"id": "user1", "display_name": "Test User"}
        api = SpotifyWebAPI()
        result = api.get_current_user()
        mock_get.assert_called_once_with("/me")
        self.assertEqual(result["id"], "user1")


class TestLikedSongs(unittest.TestCase):

    @patch.object(SpotifyWebAPI, "_get")
    def test_returns_items(self, mock_get):
        mock_get.return_value = {
            "items": [
                {"track": {"id": "t1", "name": "Song A", "artists": [{"name": "Artist"}], "album": {"name": "Album"}, "duration_ms": 200000}},
                {"track": {"id": "t2", "name": "Song B", "artists": [{"name": "Other"}], "album": {"name": "Other Album"}, "duration_ms": 180000}},
            ]
        }
        api = SpotifyWebAPI()
        items = api.get_liked_songs(limit=2)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["track"]["name"], "Song A")


class TestPlaylists(unittest.TestCase):

    @patch.object(SpotifyWebAPI, "_get")
    def test_returns_playlists(self, mock_get):
        mock_get.return_value = {
            "items": [{"id": "p1", "name": "My Playlist"}]
        }
        api = SpotifyWebAPI()
        items = api.get_playlists()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["name"], "My Playlist")

    @patch.object(SpotifyWebAPI, "_get")
    def test_get_playlist(self, mock_get):
        mock_get.return_value = {"id": "p1", "name": "Details", "tracks": {"items": []}}
        api = SpotifyWebAPI()
        result = api.get_playlist("p1")
        mock_get.assert_called_once_with("/playlists/p1")
        self.assertEqual(result["name"], "Details")


class TestSearch(unittest.TestCase):

    @patch.object(SpotifyWebAPI, "_get")
    def test_search_calls_correct_path(self, mock_get):
        mock_get.return_value = {"tracks": {"items": []}}
        api = SpotifyWebAPI()
        api.search("test query", types="track", limit=5)
        mock_get.assert_called_once_with("/search", {
            "q": "test query", "type": "track", "limit": 5, "offset": 0,
        })

    @patch.object(SpotifyWebAPI, "_get")
    def test_search_default_window_is_read_only_first_page(self, mock_get):
        mock_get.return_value = {"tracks": {"items": []}}
        api = SpotifyWebAPI()

        api.search("offline")

        mock_get.assert_called_once_with("/search", {
            "q": "offline",
            "type": "track,album,artist",
            "limit": 20,
            "offset": 0,
        })


class TestTopTracks(unittest.TestCase):

    @patch.object(SpotifyWebAPI, "_get")
    def test_returns_top_tracks(self, mock_get):
        mock_get.return_value = {"items": [{"id": "top1", "name": "Hit"}]}
        api = SpotifyWebAPI()
        items = api.get_top_tracks(limit=5, time_range="short_term")
        mock_get.assert_called_once_with("/me/top/tracks", {
            "limit": 5, "time_range": "short_term",
        })
        self.assertEqual(len(items), 1)


class TestArtistAlbum(unittest.TestCase):

    @patch.object(SpotifyWebAPI, "_get")
    def test_get_artist(self, mock_get):
        mock_get.return_value = {"id": "a1", "name": "Artist Name"}
        api = SpotifyWebAPI()
        result = api.get_artist("a1")
        mock_get.assert_called_once_with("/artists/a1")
        self.assertEqual(result["name"], "Artist Name")

    @patch.object(SpotifyWebAPI, "_get")
    def test_get_album(self, mock_get):
        mock_get.return_value = {"id": "al1", "name": "Album Name"}
        api = SpotifyWebAPI()
        result = api.get_album("al1")
        mock_get.assert_called_once_with("/albums/al1")
        self.assertEqual(result["name"], "Album Name")


class TestAutoRefresh(unittest.TestCase):

    @patch.object(SpotifyWebAPI, "_ensure_auth")
    def test_get_retries_on_401(self, mock_ensure):
        api = SpotifyWebAPI()
        resp_401 = _mock_response(None, 401)
        resp_401.raise_for_status.side_effect = requests.HTTPError(response=resp_401)
        resp_ok = _mock_response({"id": "ok"})

        with patch.object(api._session, "get", side_effect=[resp_401, resp_ok]):
            with patch("spotify_tui_tool.web_api.load_tokens") as mock_load, \
                 patch("spotify_tui_tool.web_api.refresh_access_token") as mock_refresh, \
                 patch("spotify_tui_tool.web_api.save_tokens"):
                mock_load.return_value = {"refresh_token": "ref1"}
                mock_refresh.return_value = {
                    "access_token": "new_tok", "refresh_token": "ref1",
                    "expires_in": 3600, "obtained_at": 0,
                }
                result = api._get("/me")
                self.assertEqual(result["id"], "ok")
                self.assertEqual(api._session.headers["Authorization"], "Bearer new_tok")
                mock_refresh.assert_called_once_with("ref1")

    @patch.object(SpotifyWebAPI, "_ensure_auth")
    def test_401_without_refresh_token_is_not_a_key_error(self, mock_ensure):
        api = SpotifyWebAPI()
        response = _mock_response(None, 401)
        with patch.object(api._session, "get", return_value=response), \
             patch("spotify_tui_tool.web_api.load_tokens", return_value={}), \
             self.assertRaises(requests.HTTPError):
            api._get("/me")

    @patch.object(SpotifyWebAPI, "_ensure_auth")
    def test_get_retries_once_after_rate_limit(self, mock_ensure):
        api = SpotifyWebAPI()
        resp_429 = _mock_response(None, 429)
        resp_429.headers = {"Retry-After": "0"}
        resp_ok = _mock_response({"id": "ok"})
        with patch.object(api._session, "get", side_effect=[resp_429, resp_ok]), \
             patch("spotify_tui_tool.web_api.time.sleep") as mock_sleep:
            self.assertEqual(api._get("/me")["id"], "ok")
        mock_sleep.assert_not_called()

    @patch.object(SpotifyWebAPI, "_ensure_auth")
    def test_rate_limit_failure_is_bounded_and_specific(self, mock_ensure):
        api = SpotifyWebAPI()
        resp_429 = _mock_response(None, 429)
        resp_429.headers = {"Retry-After": "0"}
        with patch.object(api._session, "get", side_effect=[resp_429, resp_429]) as mock_get:
            with self.assertRaises(SpotifyRateLimitError) as context:
                api._get("/me")
        self.assertIn("rate limit", str(context.exception).lower())
        self.assertEqual(mock_get.call_count, 2)


if __name__ == "__main__":
    unittest.main()
