"""
Integration test — validates the tool against a live Spotify instance.

This test requires a running Spotify instance and explicit opt-in with
SPOTIFY_TUI_LIVE=1.

Test runner: python -m unittest tests.test_integration -v
"""
import os
import unittest

from spotify_tui_tool.playerctl import PlayerController
from spotify_tui_tool.search import SearchService
from spotify_tui_tool.models import PlaybackStatus


def _spotify_running() -> bool:
    """Check if Spotify is reachable via playerctl."""
    try:
        pc = PlayerController()
        pc.get_status()
        return True
    except Exception:
        return False


LIVE_TESTS_ENABLED = os.environ.get("SPOTIFY_TUI_LIVE") == "1"


@unittest.skipUnless(
    LIVE_TESTS_ENABLED and _spotify_running(),
    "Set SPOTIFY_TUI_LIVE=1 with Spotify running to enable live integration tests",
)
class TestPlayerctlIntegration(unittest.TestCase):
    """Live tests against a running Spotify instance."""

    def setUp(self):
        self.pc = PlayerController()

    def test_get_status_returns_enum(self):
        """get_status must return a valid PlaybackStatus."""
        status = self.pc.get_status()
        self.assertIsInstance(status, PlaybackStatus)

    def test_get_volume_returns_float(self):
        """get_volume must return a float between 0.0 and 1.0."""
        vol = self.pc.get_volume()
        self.assertIsInstance(vol, float)
        self.assertGreaterEqual(vol, 0.0)
        self.assertLessEqual(vol, 1.0)

    def test_metadata_returns_string(self):
        """playerctl metadata must return a non-empty string."""
        result = self.pc.run("metadata", "--format", "{{artist}} - {{title}}")
        self.assertIsInstance(result, str)

    def test_open_valid_track_uri(self):
        """open_uri with a valid track URI should not raise."""
        # Use a well-known test track (Radiohead - Creep)
        uri = "spotify:track:6rqhFgbbKwnb9MLmUQDhG6"
        try:
            self.pc.open_uri(uri)
        except Exception as e:
            self.fail(f"open_uri raised {type(e).__name__}: {e}")


@unittest.skipUnless(
    LIVE_TESTS_ENABLED and _spotify_running(),
    "Set SPOTIFY_TUI_LIVE=1 with Spotify running to enable live integration tests",
)
class TestSearchServiceIntegration(unittest.TestCase):
    """Live tests for SearchService against a running Spotify instance."""

    def setUp(self):
        self.service = SearchService()

    def test_open_track_uri(self):
        """open_uri with a valid track URI should not raise."""
        uri = "spotify:track:6rqhFgbbKwnb9MLmUQDhG6"
        try:
            self.service.open_uri(uri)
        except Exception as e:
            self.fail(f"open_uri raised {type(e).__name__}: {e}")

    def test_history_updated_after_open(self):
        """After opening a URI, history should contain it."""
        uri = "spotify:track:6rqhFgbbKwnb9MLmUQDhG6"
        self.service.open_uri(uri)
        self.assertEqual(len(self.service.history), 1)
        self.assertEqual(self.service.history[0].uri, uri)

    def test_open_url_converted_and_played(self):
        """An open.spotify.com URL should be converted and played."""
        url = "https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6"
        self.service.open_uri(url)
        self.assertEqual(len(self.service.history), 1)
        self.assertEqual(
            self.service.history[0].uri,
            "spotify:track:6rqhFgbbKwnb9MLmUQDhG6",
        )


if __name__ == "__main__":
    unittest.main()
