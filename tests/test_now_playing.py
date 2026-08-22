"""
Tests for NowPlaying — metadata parsing, polling logic, and state management.

Strict TDD: tests written FIRST (RED).  PlayerController is injected as a
mock; pure functions are tested with concrete string inputs.

Test runner: python3 -m unittest
"""
import unittest
from unittest.mock import MagicMock

from spotify_tui_tool.now_playing import (
    NowPlaying,
    parse_position,
    parse_volume,
    parse_duration,
    extract_track_id,
    build_track_info,
)
from spotify_tui_tool.models import PlaybackState, TrackInfo, PlaybackStatus
from spotify_tui_tool.exceptions import SpotifyNotRunningError


# ---------------------------------------------------------------------------
# Sample data — mimics real playerctl --format output
# ---------------------------------------------------------------------------

FULL_META = (
    "Pink Floyd|Speak To Me - 2011 Remastered Version|"
    "The Dark Side Of The Moon (2011 Remastered Version)|"
    "64333000|0.600000|"
    "https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6"
)

PARTIAL_META = (
    "Daft Punk|One More Time||"
    "32000000|0.500000|"
)

EMPTY_META = "||||"  # all fields empty (player stopped)

TRACK_ID = "6rqhFgbbKwnb9MLmUQDhG6"


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
        return ""

    mock.run.side_effect = run_side_effect
    return mock


# ---------------------------------------------------------------------------
# Pure parsing functions
# ---------------------------------------------------------------------------

class TestParsePosition(unittest.TestCase):

    def test_seconds_to_ms(self):
        self.assertEqual(parse_position("45.123"), 45123)

    def test_whole_number(self):
        self.assertEqual(parse_position("30"), 30000)

    def test_empty_returns_zero(self):
        self.assertEqual(parse_position(""), 0)

    def test_invalid_returns_zero(self):
        self.assertEqual(parse_position("not-a-number"), 0)


class TestParseVolume(unittest.TestCase):

    def test_float_string(self):
        self.assertEqual(parse_volume("0.600000"), 0.6)

    def test_one(self):
        self.assertEqual(parse_volume("1.000000"), 1.0)

    def test_empty_returns_zero(self):
        self.assertEqual(parse_volume(""), 0.0)

    def test_invalid_returns_zero(self):
        self.assertEqual(parse_volume("loud"), 0.0)


class TestParseDuration(unittest.TestCase):

    def test_microseconds_to_ms(self):
        """mpris:length is in microseconds; 64333000 µs → 64333 ms."""
        self.assertEqual(parse_duration("64333000"), 64333)

    def test_empty_returns_zero(self):
        self.assertEqual(parse_duration(""), 0)

    def test_invalid_returns_zero(self):
        self.assertEqual(parse_duration("unknown"), 0)


class TestExtractTrackId(unittest.TestCase):

    def test_from_url(self):
        url = "https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6"
        self.assertEqual(extract_track_id(url), TRACK_ID)

    def test_from_mpris_path(self):
        path = "/com/spotify/track/6rqhFgbbKwnb9MLmUQDhG6"
        self.assertEqual(extract_track_id(path), TRACK_ID)

    def test_no_match(self):
        self.assertEqual(extract_track_id("not-a-url"), "")

    def test_empty(self):
        self.assertEqual(extract_track_id(""), "")


class TestBuildTrackInfo(unittest.TestCase):

    def test_full_metadata(self):
        """Full format output must produce a fully populated TrackInfo."""
        info = build_track_info(FULL_META, "45.123", "Playing")
        self.assertEqual(info.artist, "Pink Floyd")
        self.assertEqual(info.title, "Speak To Me - 2011 Remastered Version")
        self.assertEqual(info.album, "The Dark Side Of The Moon (2011 Remastered Version)")
        self.assertEqual(info.track_id, TRACK_ID)
        self.assertEqual(info.duration_ms, 64333)
        self.assertEqual(info.position_ms, 45123)
        self.assertAlmostEqual(info.volume, 0.6)
        self.assertEqual(info.status, PlaybackStatus.PLAYING)

    def test_partial_metadata(self):
        """Missing album and url → empty strings, correct other fields."""
        info = build_track_info(PARTIAL_META, "10.5", "Paused")
        self.assertEqual(info.artist, "Daft Punk")
        self.assertEqual(info.title, "One More Time")
        self.assertEqual(info.album, "")
        self.assertEqual(info.track_id, "")
        self.assertEqual(info.duration_ms, 32000)
        self.assertEqual(info.position_ms, 10500)
        self.assertAlmostEqual(info.volume, 0.5)
        self.assertEqual(info.status, PlaybackStatus.PAUSED)

    def test_empty_metadata(self):
        """All-empty format output → TrackInfo with all defaults."""
        info = build_track_info(EMPTY_META, "", "Stopped")
        self.assertEqual(info.artist, "")
        self.assertEqual(info.title, "")
        self.assertEqual(info.album, "")
        self.assertEqual(info.track_id, "")
        self.assertEqual(info.duration_ms, 0)
        self.assertEqual(info.position_ms, 0)
        self.assertEqual(info.volume, 0.0)
        self.assertEqual(info.status, PlaybackStatus.STOPPED)

    def test_stopped_status(self):
        """Status 'Stopped' must map to PlaybackStatus.STOPPED."""
        info = build_track_info(FULL_META, "45.123", "Stopped")
        self.assertEqual(info.status, PlaybackStatus.STOPPED)


# ---------------------------------------------------------------------------
# NowPlaying interval
# ---------------------------------------------------------------------------

class TestNowPlayingInterval(unittest.TestCase):

    def test_default_interval(self):
        """Default poll interval is 1.0 second."""
        widget = NowPlaying(player=make_mock_player())
        self.assertEqual(widget.poll_interval, 1.0)

    def test_custom_interval(self):
        """A custom interval within bounds is accepted."""
        widget = NowPlaying(player=make_mock_player(), poll_interval=2.0)
        self.assertEqual(widget.poll_interval, 2.0)

    def test_interval_clamped_min(self):
        """200 ms must be clamped to 500 ms minimum."""
        widget = NowPlaying(player=make_mock_player(), poll_interval=0.2)
        self.assertEqual(widget.poll_interval, 0.5)


# ---------------------------------------------------------------------------
# poll_once — happy path
# ---------------------------------------------------------------------------

class TestPollOnce(unittest.TestCase):

    def test_poll_returns_track_info(self):
        """poll_once must return a fully populated TrackInfo on success."""
        widget = NowPlaying(player=make_mock_player())
        info = widget.poll_once()
        self.assertEqual(info.artist, "Pink Floyd")
        self.assertEqual(info.title, "Speak To Me - 2011 Remastered Version")
        self.assertEqual(info.track_id, TRACK_ID)
        self.assertEqual(info.status, PlaybackStatus.PLAYING)

    def test_poll_empty_metadata(self):
        """When metadata is empty, TrackInfo has empty fields."""
        widget = NowPlaying(player=make_mock_player(metadata=EMPTY_META, position="", status="Stopped"))
        info = widget.poll_once()
        self.assertEqual(info.artist, "")
        self.assertEqual(info.title, "")
        self.assertEqual(info.status, PlaybackStatus.STOPPED)

    def test_poll_partial_metadata(self):
        """Partial metadata (no album) → TrackInfo with empty album."""
        widget = NowPlaying(player=make_mock_player(metadata=PARTIAL_META, position="10.5", status="Paused"))
        info = widget.poll_once()
        self.assertEqual(info.artist, "Daft Punk")
        self.assertEqual(info.album, "")
        self.assertEqual(info.status, PlaybackStatus.PAUSED)


# ---------------------------------------------------------------------------
# Track change detection
# ---------------------------------------------------------------------------

class TestTrackChange(unittest.TestCase):
    """A track-change flag must be set only when artist+title differ."""

    def test_first_poll_no_change(self):
        """The initial poll should not fire a track-change event."""
        widget = NowPlaying(player=make_mock_player())
        widget.poll_once()
        self.assertFalse(widget.track_changed)

    def test_same_track_no_change(self):
        """Polling the same track twice → no change on the second poll."""
        widget = NowPlaying(player=make_mock_player())
        widget.poll_once()
        widget.poll_once()
        self.assertFalse(widget.track_changed)

    def test_different_track_change(self):
        """A different artist+title must set the track-change flag."""
        mock = make_mock_player()
        widget = NowPlaying(player=mock)
        widget.poll_once()  # initial: Pink Floyd

        # Switch to a different track
        mock.run.side_effect = None
        other_meta = (
            "Daft Punk|One More Time||"
            "32000000|0.500000|"
        )
        mock.run.side_effect = (
            lambda *a: other_meta if a[0] == "metadata"
            else ("10.0" if a[0] == "position" else "Playing")
        )
        widget.poll_once()
        self.assertTrue(widget.track_changed)

    def test_same_artist_different_position_no_change(self):
        """Position update while artist+title stays same → no change."""
        mock = make_mock_player(position="45.123")
        widget = NowPlaying(player=mock)
        widget.poll_once()

        # Same metadata, different position
        mock.run.side_effect = None
        mock.run.side_effect = (
            lambda *a: FULL_META if a[0] == "metadata"
            else ("99.0" if a[0] == "position" else "Playing")
        )
        widget.poll_once()
        self.assertFalse(widget.track_changed)


# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------

class TestGracefulDegradation(unittest.TestCase):

    def test_failure_retains_last_known(self):
        """One miss stays fresh; the second miss marks retained context stale."""
        mock = make_mock_player()
        widget = NowPlaying(player=mock)
        first = widget.poll_once()
        self.assertEqual(first.artist, "Pink Floyd")

        # Now make all calls fail
        mock.run.side_effect = SpotifyNotRunningError()
        first_miss = widget.poll_once()
        self.assertEqual(first_miss.artist, "Pink Floyd")
        self.assertEqual(first_miss.title, "Speak To Me - 2011 Remastered Version")
        self.assertEqual(first_miss.playback_state, PlaybackState.FRESH)

        second_miss = widget.poll_once()
        self.assertEqual(second_miss.artist, "Pink Floyd")
        self.assertEqual(second_miss.title, "Speak To Me - 2011 Remastered Version")
        self.assertEqual(second_miss.playback_state, PlaybackState.STALE)

    def test_failure_resets_on_recovery(self):
        """After recovery, failure count resets to 0."""
        mock = make_mock_player()
        widget = NowPlaying(player=mock)
        widget.poll_once()

        mock.run.side_effect = SpotifyNotRunningError()
        widget.poll_once()
        self.assertEqual(widget._failure_count, 1)

        # Recover
        mock.run.side_effect = None
        mock.run.side_effect = (
            lambda *a: FULL_META if a[0] == "metadata"
            else ("45.123" if a[0] == "position" else "Playing")
        )
        widget.poll_once()
        self.assertEqual(widget._failure_count, 0)


# ---------------------------------------------------------------------------
# Extended outage
# ---------------------------------------------------------------------------

class TestExtendedOutage(unittest.TestCase):

    def test_connection_lost_after_five_failures(self):
        """After 5 consecutive failures, connection_lost must be True."""
        mock = MagicMock()
        mock.run.side_effect = SpotifyNotRunningError()
        widget = NowPlaying(player=mock)

        for _ in range(4):
            widget.poll_once()
        self.assertFalse(widget.connection_lost)

        widget.poll_once()  # 5th failure
        self.assertTrue(widget.connection_lost)

    def test_recovery_clears_connection_lost(self):
        """A successful poll after outage must clear connection_lost."""
        mock = MagicMock()
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 5:  # first 5 polls fail (1 call each)
                raise SpotifyNotRunningError()
            cmd = args[0]
            if cmd == "metadata":
                return FULL_META
            elif cmd == "position":
                return "45.123"
            elif cmd == "status":
                return "Playing"
            return ""

        mock.run.side_effect = side_effect
        widget = NowPlaying(player=mock)

        # 5 failed polls → connection lost
        for _ in range(5):
            widget.poll_once()
        self.assertTrue(widget.connection_lost)

        # Recovery poll
        widget.poll_once()
        self.assertFalse(widget.connection_lost)
        self.assertEqual(widget._failure_count, 0)


if __name__ == "__main__":
    unittest.main()
