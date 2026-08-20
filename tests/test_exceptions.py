"""
Tests for the exception hierarchy used across all modules.

Written FIRST (RED) before exceptions.py exists.
"""
import unittest

from spotify_tui_tool.exceptions import (
    PlayerctlNotFoundError,
    SpotifyNotRunningError,
    InvalidURIError,
    PlaybackError,
)


class TestPlayerctlNotFoundError(unittest.TestCase):
    """Raised when the playerctl binary is missing from PATH."""

    def test_message(self):
        """The error message must be exactly 'playerctl not found'."""
        err = PlayerctlNotFoundError()
        self.assertEqual(str(err), "playerctl not found")

    def test_is_exception(self):
        """Must be catchable as a plain Exception."""
        try:
            raise PlayerctlNotFoundError()
        except Exception:
            pass  # expected


class TestSpotifyNotRunningError(unittest.TestCase):
    """Raised when no MPRIS player (Spotify) is running."""

    def test_message(self):
        """The error message must be non-empty and descriptive."""
        err = SpotifyNotRunningError()
        self.assertIn("No player", str(err))

    def test_is_exception(self):
        try:
            raise SpotifyNotRunningError()
        except Exception:
            pass


class TestInvalidURIError(unittest.TestCase):
    """Raised when a Spotify URI fails validation."""

    def test_message_with_uri(self):
        """The error should include the invalid input in its message."""
        err = InvalidURIError("not-a-uri")
        self.assertIn("not-a-uri", str(err))

    def test_is_exception(self):
        try:
            raise InvalidURIError("bad")
        except Exception:
            pass


class TestPlaybackError(unittest.TestCase):
    """Raised when a playerctl command returns a non-zero exit code."""

    def test_message_with_stderr(self):
        """The error should expose the playerctl stderr text."""
        err = PlaybackError("Failed to open URI")
        self.assertIn("Failed to open URI", str(err))

    def test_has_stderr_attribute(self):
        """PlaybackError should expose a .stderr attribute for diagnostics."""
        err = PlaybackError("Failed to open URI")
        self.assertEqual(err.stderr, "Failed to open URI")

    def test_is_exception(self):
        try:
            raise PlaybackError("oops")
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
