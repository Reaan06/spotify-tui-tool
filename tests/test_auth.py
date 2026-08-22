"""Tests for auth module — token storage and refresh logic."""

import json
import io
import stat
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from spotify_tui_tool import auth
from spotify_tui_tool.auth import (
    _generate_pkce_pair,
    _build_auth_url,
    is_token_expired,
    load_tokens,
    save_tokens,
)


class TestPKCE(unittest.TestCase):

    def test_verifier_length(self):
        verifier, challenge = _generate_pkce_pair()
        self.assertIsInstance(verifier, str)
        self.assertGreater(len(verifier), 0)

    def test_challenge_is_base64url(self):
        _, challenge = _generate_pkce_pair()
        self.assertRegex(challenge, r"^[A-Za-z0-9\-_]+$")

    def test_verifier_and_challenge_are_different(self):
        v, c = _generate_pkce_pair()
        self.assertNotEqual(v, c)

    def test_challenge_matches_sha256(self):
        import base64, hashlib
        verifier, challenge = _generate_pkce_pair()
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        self.assertEqual(challenge, expected)


class TestAuthURL(unittest.TestCase):

    def test_contains_required_params(self):
        url = _build_auth_url("test_challenge")
        self.assertIn("client_id=", url)
        self.assertIn("code_challenge=test_challenge", url)
        self.assertIn("code_challenge_method=S256", url)
        self.assertIn("response_type=code", url)
        self.assertIn("redirect_uri=", url)
        self.assertIn("scope=", url)

    def test_uses_spotify_accounts_domain(self):
        url = _build_auth_url("ch")
        self.assertTrue(url.startswith("https://accounts.spotify.com/authorize?"))


class TestTokenExpiry(unittest.TestCase):

    def test_expired_when_past(self):
        token_data = {
            "expires_in": 3600,
            "obtained_at": time.time() - 7200,
        }
        self.assertTrue(is_token_expired(token_data))

    def test_not_expired_when_fresh(self):
        token_data = {
            "expires_in": 3600,
            "obtained_at": time.time(),
        }
        self.assertFalse(is_token_expired(token_data))

    def test_near_expiry_with_buffer(self):
        token_data = {
            "expires_in": 3600,
            "obtained_at": time.time() - 3550,  # 50s before expiry
        }
        # 3600 - 60 buffer = 3540s, we're at 3550 -> expired
        self.assertTrue(is_token_expired(token_data))


class TestTokenStorage(unittest.TestCase):

    def setUp(self):
        self._original_file = auth.TOKEN_FILE
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._tmp = Path(self._tmp_dir.name) / "tokens.json"
        auth.TOKEN_FILE = self._tmp

    def tearDown(self):
        auth.TOKEN_FILE = self._original_file
        self._tmp_dir.cleanup()

    def test_save_and_load(self):
        data = {"access_token": "abc", "refresh_token": "xyz", "expires_in": 3600, "obtained_at": 1.0}
        save_tokens(data)
        loaded = load_tokens()
        self.assertEqual(loaded["access_token"], "abc")
        self.assertEqual(loaded["refresh_token"], "xyz")

    def test_load_returns_none_when_missing(self):
        auth.TOKEN_FILE = self._tmp.parent / "nonexistent.json"
        self.assertIsNone(load_tokens())

    def test_load_returns_none_on_corrupt(self):
        self._tmp.write_text("not json {{{")
        self.assertIsNone(load_tokens())

    def test_save_creates_parent_dir(self):
        nested = self._tmp.parent / "sub" / "tokens.json"
        auth.TOKEN_FILE = nested
        save_tokens({"access_token": "x", "obtained_at": 0, "expires_in": 0})
        self.assertTrue(nested.exists())

    def test_save_restricts_directory_and_file_permissions(self):
        save_tokens({"access_token": "x"})
        self.assertEqual(stat.S_IMODE(self._tmp.parent.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(self._tmp.stat().st_mode), 0o600)


class TestGetValidToken(unittest.TestCase):

    def setUp(self):
        self._original_file = auth.TOKEN_FILE
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._tmp = Path(self._tmp_dir.name) / "tokens.json"
        auth.TOKEN_FILE = self._tmp

    def tearDown(self):
        auth.TOKEN_FILE = self._original_file
        self._tmp_dir.cleanup()

    def test_returns_none_when_no_tokens(self):
        auth.TOKEN_FILE = self._tmp.parent / "nonexistent.json"
        self.assertIsNone(auth.get_valid_token())

    def test_returns_token_when_valid(self):
        data = {
            "access_token": "valid_token",
            "refresh_token": "ref",
            "expires_in": 3600,
            "obtained_at": time.time(),
        }
        save_tokens(data)
        self.assertEqual(auth.get_valid_token(), "valid_token")

    @patch.object(auth, "refresh_access_token")
    def test_refreshes_when_expired(self, mock_refresh):
        mock_refresh.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_ref",
            "expires_in": 3600,
            "obtained_at": time.time(),
        }
        data = {
            "access_token": "old_token",
            "refresh_token": "old_ref",
            "expires_in": 3600,
            "obtained_at": time.time() - 7200,
        }
        save_tokens(data)
        token = auth.get_valid_token()
        self.assertEqual(token, "new_token")
        mock_refresh.assert_called_once_with("old_ref")

    def test_expired_token_without_refresh_token_returns_none(self):
        save_tokens({
            "access_token": "old_token",
            "expires_in": 3600,
            "obtained_at": time.time() - 7200,
        })
        with patch.object(auth, "refresh_access_token") as mock_refresh:
            self.assertIsNone(auth.get_valid_token())
        mock_refresh.assert_not_called()


class TestRefreshAccessToken(unittest.TestCase):

    @patch.object(auth.requests, "post")
    def test_returns_new_tokens(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "refreshed",
            "expires_in": 3600,
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = auth.refresh_access_token("my_refresh_token")
        self.assertEqual(result["access_token"], "refreshed")
        self.assertIn("obtained_at", result)
        self.assertEqual(result["refresh_token"], "my_refresh_token")

    @patch.object(auth.requests, "post")
    def test_keeps_refresh_token_when_new_one_present(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "refreshed",
            "refresh_token": "brand_new_refresh",
            "expires_in": 3600,
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = auth.refresh_access_token("old_refresh")
        self.assertEqual(result["refresh_token"], "brand_new_refresh")


class TestOAuthCallback(unittest.TestCase):

    def test_callback_rejects_state_from_another_attempt(self):
        handler = auth._CallbackHandler.__new__(auth._CallbackHandler)
        handler.path = "/callback?code=stolen&state=wrong"
        handler.send_response = MagicMock()
        handler.end_headers = MagicMock()
        handler.wfile = io.BytesIO()
        auth._CallbackHandler.reset("expected")

        handler.do_GET()

        self.assertIsNone(auth._CallbackHandler.auth_code)
        handler.send_response.assert_called_once_with(400)

    @patch("webbrowser.open")
    @patch.object(auth, "save_tokens")
    @patch.object(auth, "_exchange_code", return_value={"access_token": "new"})
    @patch.object(auth, "HTTPServer")
    def test_authenticate_resets_and_validates_attempt_state(
        self, mock_server, mock_exchange, mock_save, mock_open
    ):
        server = MagicMock()

        def receive_callback():
            auth._CallbackHandler.auth_code = "code"

        server.handle_request.side_effect = receive_callback
        mock_server.return_value = server

        result = auth.authenticate()

        self.assertEqual(result["access_token"], "new")
        opened_url = mock_open.call_args.args[0]
        self.assertIn("state=", opened_url)
        self.assertEqual(auth._CallbackHandler.auth_code, "code")
        mock_exchange.assert_called_once()
        server.server_close.assert_called_once_with()

    @patch.object(auth, "HTTPServer", side_effect=OSError("address in use"))
    def test_authenticate_reports_callback_bind_failure(self, mock_server):
        with self.assertRaisesRegex(RuntimeError, "Unable to start Spotify OAuth callback server"):
            auth.authenticate()


if __name__ == "__main__":
    unittest.main()
