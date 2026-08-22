"""Tests for SpotifyClient — the unified service layer.

Strict TDD: tests written FIRST (RED).  PlayerController is injected as a
mock so no real playerctl calls are made.
"""

import unittest
from unittest.mock import MagicMock, patch

from spotify_tui_tool.exceptions import PlaybackError, SpotifyNotRunningError
from spotify_tui_tool.models import PlaybackStatus, TrackInfo
from spotify_tui_tool.spotify_client import SpotifyClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FULL_META = (
    "Pink Floyd|Speak To Me - 2011 Remastered Version|"
    "The Dark Side Of The Moon (2011 Remastered Version)|"
    "64333000|0.600000|"
    "https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6"
)

EMPTY_META = "||||"


def make_mock_player(metadata=FULL_META, position="45.123", status="Playing"):
    """Create a MagicMock PlayerController with routed run() responses."""
    mock = MagicMock()

    def run_side_effect(*args, **kwargs):
        cmd = args[0]
        if cmd == "metadata":
            return metadata
        elif cmd == "position":
            return position
        elif cmd == "status":
            return status
        elif cmd == "volume":
            return "0.600000"
        return ""

    mock.run.side_effect = run_side_effect

    from spotify_tui_tool.models import PlaybackStatus as _PS
    _status_map = {"Playing": _PS.PLAYING, "Paused": _PS.PAUSED, "Stopped": _PS.STOPPED}
    mock.get_volume.return_value = 0.6
    mock.get_status.return_value = _status_map.get(status, _PS.PLAYING)
    return mock


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestSpotifyClientConstruction(unittest.TestCase):

    def test_creates_default_player_if_none(self):
        """SpotifyClient() with no args creates a real PlayerController."""
        client = SpotifyClient()
        self.assertIsNotNone(client.player)

    def test_accepts_injected_player(self):
        """SpotifyClient(player=...) uses the injected player."""
        mock_player = make_mock_player()
        client = SpotifyClient(player=mock_player)
        self.assertIs(client.player, mock_player)

    def test_default_poll_interval(self):
        """Default poll interval is 1.0s (forwarded to NowPlaying)."""
        client = SpotifyClient()
        self.assertEqual(client.now_playing.poll_interval, 1.0)

    def test_custom_poll_interval(self):
        """Custom poll interval is forwarded to NowPlaying."""
        client = SpotifyClient(poll_interval=2.0)
        self.assertEqual(client.now_playing.poll_interval, 2.0)


# ---------------------------------------------------------------------------
# Playback controls
# ---------------------------------------------------------------------------

class TestPlaybackControls(unittest.TestCase):

    def _client(self):
        return SpotifyClient(player=make_mock_player())

    def test_play_pause(self):
        """play_pause delegates to player.play_pause."""
        client = self._client()
        client.play_pause()
        client.player.play_pause.assert_called_once()

    def test_next_track(self):
        """next_track delegates to player.next."""
        client = self._client()
        client.next_track()
        client.player.next.assert_called_once()

    def test_previous_track(self):
        """previous_track delegates to player.previous."""
        client = self._client()
        client.previous_track()
        client.player.previous.assert_called_once()

    def test_get_volume(self):
        """get_volume returns the player's volume."""
        client = self._client()
        vol = client.get_volume()
        self.assertEqual(vol, 0.6)

    def test_set_volume(self):
        """set_volume delegates to player.set_volume."""
        client = self._client()
        client.set_volume(0.8)
        client.player.set_volume.assert_called_once_with(0.8)


# ---------------------------------------------------------------------------
# Data access — poll
# ---------------------------------------------------------------------------

class TestPoll(unittest.TestCase):

    def test_poll_returns_track_info(self):
        """poll() returns a populated TrackInfo on success."""
        client = SpotifyClient(player=make_mock_player())
        info = client.poll()
        self.assertEqual(info.artist, "Pink Floyd")
        self.assertEqual(info.title, "Speak To Me - 2011 Remastered Version")
        self.assertEqual(info.album, "The Dark Side Of The Moon (2011 Remastered Version)")
        self.assertEqual(info.status, PlaybackStatus.PLAYING)

    def test_poll_empty_metadata(self):
        """poll() with empty metadata returns empty TrackInfo fields."""
        client = SpotifyClient(
            player=make_mock_player(metadata=EMPTY_META, position="", status="Stopped")
        )
        info = client.poll()
        self.assertEqual(info.artist, "")
        self.assertEqual(info.title, "")
        self.assertEqual(info.status, PlaybackStatus.STOPPED)

    def test_poll_failure_returns_last_known(self):
        """On failure, poll() returns the last known TrackInfo."""
        mock = make_mock_player()
        client = SpotifyClient(player=mock)
        first = client.poll()
        self.assertEqual(first.artist, "Pink Floyd")

        # Now fail
        mock.run.side_effect = SpotifyNotRunningError()
        result = client.poll()
        self.assertEqual(result.artist, "Pink Floyd")
        self.assertEqual(result.title, "Speak To Me - 2011 Remastered Version")


# ---------------------------------------------------------------------------
# get_current_track
# ---------------------------------------------------------------------------

class TestGetCurrentTrack(unittest.TestCase):

    def test_returns_empty_if_never_polled(self):
        """Before any poll, get_current_track returns an empty TrackInfo."""
        client = SpotifyClient(player=make_mock_player())
        info = client.get_current_track()
        self.assertEqual(info.artist, "")
        self.assertEqual(info.title, "")

    def test_returns_last_polled_track(self):
        """After a poll, get_current_track returns that track."""
        client = SpotifyClient(player=make_mock_player())
        client.poll()
        info = client.get_current_track()
        self.assertEqual(info.artist, "Pink Floyd")
        self.assertEqual(info.title, "Speak To Me - 2011 Remastered Version")


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------

class TestGetStatus(unittest.TestCase):

    def test_returns_playback_status(self):
        """get_status returns PlaybackStatus from playerctl."""
        client = SpotifyClient(player=make_mock_player())
        status = client.get_status()
        self.assertEqual(status, PlaybackStatus.PLAYING)


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

class TestStubs(unittest.TestCase):

    def test_liked_songs_returns_empty(self):
        """get_liked_songs returns empty list (stub)."""
        client = SpotifyClient(player=make_mock_player())
        self.assertEqual(client.get_liked_songs(), [])

    def test_playlists_returns_empty(self):
        """get_playlists returns empty list (stub)."""
        client = SpotifyClient(player=make_mock_player())
        self.assertEqual(client.get_playlists(), [])

    def test_search_returns_empty(self):
        """search returns empty list (stub)."""
        client = SpotifyClient(player=make_mock_player())
        self.assertEqual(client.search("test query"), [])


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------

class TestErrorPropagation(unittest.TestCase):

    def test_play_pause_propagates_error(self):
        """SpotifyNotRunningError from play_pause propagates."""
        mock = make_mock_player()
        mock.play_pause.side_effect = SpotifyNotRunningError()
        client = SpotifyClient(player=mock)
        with self.assertRaises(SpotifyNotRunningError):
            client.play_pause()

    def test_next_track_propagates_error(self):
        """PlaybackError from next_track propagates."""
        mock = make_mock_player()
        mock.next.side_effect = PlaybackError("failed", "stderr")
        client = SpotifyClient(player=mock)
        with self.assertRaises(PlaybackError):
            client.next_track()

    def test_seek_propagates_error(self):
        """PlaybackError from seek propagates."""
        mock = make_mock_player()
        mock.run.side_effect = PlaybackError("seek failed", "stderr")
        client = SpotifyClient(player=mock)
        with self.assertRaises(PlaybackError):
            client.seek(5000)

    def test_seek_converts_milliseconds_to_signed_seconds(self):
        mock = make_mock_player()
        client = SpotifyClient(player=mock)
        client.seek(5000)
        mock.run.assert_called_once_with("position", "+5")
        mock.reset_mock()
        client.seek(-2500)
        mock.run.assert_called_once_with("position", "-2.5")


if __name__ == "__main__":
    unittest.main()
