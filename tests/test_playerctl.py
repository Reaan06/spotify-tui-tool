"""
Tests for PlayerController — the playerctl subprocess wrapper.

Strict TDD: these tests are written FIRST (RED).  They mock
``subprocess.run`` so no real playerctl/Spototify calls are made, and they
verify the exact argument arrays passed to playerctl plus error mapping.

Test runner: python3 -m unittest
"""
import subprocess
import unittest
from unittest.mock import patch, MagicMock

from spotify_tui_tool.playerctl import PlayerController
from spotify_tui_tool.models import PlaybackStatus
from spotify_tui_tool.exceptions import (
    PlayerctlNotFoundError,
    SpotifyNotRunningError,
    PlaybackError,
)


def _ok(stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    """Helper: a successful CompletedProcess."""
    return subprocess.CompletedProcess(
        args=[], returncode=0, stdout=stdout, stderr=stderr
    )


def _fail(stderr: str = "error", returncode: int = 1) -> subprocess.CompletedProcess:
    """Helper: a failed CompletedProcess."""
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout="", stderr=stderr
    )


class TestPlaybackCommands(unittest.TestCase):
    """Transport controls: play, pause, play-pause, next, previous."""

    def _patch(self):
        """Return a (mock, patcher) helper so each test patches independently."""
        patcher = patch("spotify_tui_tool.playerctl.subprocess.run")
        mock = patcher.start()
        mock.return_value = _ok()
        self.addCleanup(patcher.stop)
        return mock

    def test_play(self):
        """play() must execute 'playerctl --player=spotify play'."""
        mock = self._patch()
        PlayerController().play()
        self.assertEqual(
            mock.call_args.args[0],
            ["playerctl", "--player=spotify", "play"],
        )

    def test_pause(self):
        """pause() must execute 'playerctl --player=spotify pause'."""
        mock = self._patch()
        PlayerController().pause()
        self.assertEqual(
            mock.call_args.args[0],
            ["playerctl", "--player=spotify", "pause"],
        )

    def test_play_pause(self):
        """play_pause() must execute 'playerctl --player=spotify play-pause'."""
        mock = self._patch()
        PlayerController().play_pause()
        self.assertEqual(
            mock.call_args.args[0],
            ["playerctl", "--player=spotify", "play-pause"],
        )

    def test_next(self):
        """next() must execute 'playerctl --player=spotify next'."""
        mock = self._patch()
        PlayerController().next()
        self.assertEqual(
            mock.call_args.args[0],
            ["playerctl", "--player=spotify", "next"],
        )

    def test_previous(self):
        """previous() must execute 'playerctl --player=spotify previous'."""
        mock = self._patch()
        PlayerController().previous()
        self.assertEqual(
            mock.call_args.args[0],
            ["playerctl", "--player=spotify", "previous"],
        )

    def test_custom_player_name(self):
        """A custom player name must appear in every command."""
        mock = self._patch()
        PlayerController(player_name="spotifyd").play()
        self.assertEqual(
            mock.call_args.args[0],
            ["playerctl", "--player=spotifyd", "play"],
        )


class TestErrorHandling(unittest.TestCase):
    """playerctl missing, Spotify not running, command failures."""

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_playerctl_not_installed(self, mock_run):
        """FileNotFoundError from subprocess → PlayerctlNotFoundError."""
        mock_run.side_effect = FileNotFoundError("[Errno 2] No such file: 'playerctl'")
        with self.assertRaises(PlayerctlNotFoundError) as ctx:
            PlayerController().play()
        self.assertEqual(str(ctx.exception), "playerctl not found")

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_spotify_not_running(self, mock_run):
        """'No players found' on stderr → SpotifyNotRunningError."""
        mock_run.return_value = _fail(stderr="No players found")
        with self.assertRaises(SpotifyNotRunningError):
            PlayerController().play()

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_playback_error(self, mock_run):
        """Other non-zero exit → PlaybackError with stderr text."""
        mock_run.return_value = _fail(stderr="Run command failed")
        with self.assertRaises(PlaybackError) as ctx:
            PlayerController().play()
        self.assertIn("Run command failed", str(ctx.exception))
        self.assertEqual(ctx.exception.stderr, "Run command failed")

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_open_uri_invalid_raises(self, mock_run):
        """open_uri with invalid URI should raise PlaybackError on failure."""
        mock_run.return_value = _fail(stderr="Could not open URI")
        with self.assertRaises(PlaybackError):
            PlayerController().open_uri("spotify:track:invalid")


class TestVolumeControl(unittest.TestCase):
    """get_volume returns float; set_volume validates range."""

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_get_volume(self, mock_run):
        """get_volume must return a float, not a string."""
        mock_run.return_value = _ok(stdout="0.600000")
        vol = PlayerController().get_volume()
        self.assertEqual(vol, 0.6)
        self.assertIsInstance(vol, float)

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_set_volume(self, mock_run):
        """set_volume(0.8) must call 'playerctl --player=spotify volume 0.8'."""
        mock_run.return_value = _ok()
        PlayerController().set_volume(0.8)
        self.assertEqual(
            mock_run.call_args.args[0],
            ["playerctl", "--player=spotify", "volume", "0.8"],
        )

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_reject_volume_below_zero(self, mock_run):
        """set_volume(-0.1) must raise ValueError, no playerctl call."""
        mock_run.return_value = _ok()
        with self.assertRaises(ValueError) as ctx:
            PlayerController().set_volume(-0.1)
        self.assertIn("Volume must be between 0.0 and 1.0", str(ctx.exception))
        mock_run.assert_not_called()

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_reject_volume_above_one(self, mock_run):
        """set_volume(1.5) must raise ValueError, no playerctl call."""
        mock_run.return_value = _ok()
        with self.assertRaises(ValueError) as ctx:
            PlayerController().set_volume(1.5)
        self.assertIn("Volume must be between 0.0 and 1.0", str(ctx.exception))
        mock_run.assert_not_called()

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_set_volume_boundary_zero(self, mock_run):
        """set_volume(0.0) is valid and must reach playerctl."""
        mock_run.return_value = _ok()
        PlayerController().set_volume(0.0)
        self.assertEqual(
            mock_run.call_args.args[0],
            ["playerctl", "--player=spotify", "volume", "0.0"],
        )

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_set_volume_boundary_one(self, mock_run):
        """set_volume(1.0) is valid and must reach playerctl."""
        mock_run.return_value = _ok()
        PlayerController().set_volume(1.0)
        self.assertEqual(
            mock_run.call_args.args[0],
            ["playerctl", "--player=spotify", "volume", "1.0"],
        )


class TestPlaybackStatus(unittest.TestCase):
    """get_status maps playerctl output to PlaybackStatus enum."""

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_status_playing(self, mock_run):
        mock_run.return_value = _ok(stdout="Playing")
        self.assertEqual(
            PlayerController().get_status(), PlaybackStatus.PLAYING
        )

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_status_paused(self, mock_run):
        mock_run.return_value = _ok(stdout="Paused")
        self.assertEqual(
            PlayerController().get_status(), PlaybackStatus.PAUSED
        )

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_status_stopped(self, mock_run):
        mock_run.return_value = _ok(stdout="Stopped")
        self.assertEqual(
            PlayerController().get_status(), PlaybackStatus.STOPPED
        )


class TestOpenUri(unittest.TestCase):
    """open_uri must pass the URI to playerctl open."""

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_open_valid_uri(self, mock_run):
        mock_run.return_value = _ok()
        PlayerController().open_uri("spotify:track:6rqhFgbbKwnb9MLmUQDhG6")
        self.assertEqual(
            mock_run.call_args.args[0],
            ["playerctl", "--player=spotify", "open", "spotify:track:6rqhFgbbKwnb9MLmUQDhG6"],
        )

    @patch("spotify_tui_tool.playerctl.subprocess.run")
    def test_open_playlist(self, mock_run):
        mock_run.return_value = _ok()
        PlayerController().open_uri("spotify:playlist:37i9dQZF1DXcBWIGoYBM5M")
        self.assertEqual(
            mock_run.call_args.args[0],
            ["playerctl", "--player=spotify", "open", "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"],
        )


if __name__ == "__main__":
    unittest.main()
