"""
Tests for data models: TrackInfo, ParsedURI, PlaybackStatus.

These tests are written FIRST (RED) before any production code exists.
They define the contracts for every dataclass and enum field the rest of
the system will depend on.
"""
import unittest

from spotify_tui_tool.models import TrackInfo, ParsedURI, PlaybackStatus


class TestTrackInfo(unittest.TestCase):
    """TrackInfo is a dataclass describing the current playback state."""

    def test_full_metadata(self):
        """A TrackInfo with all fields populated should expose every field."""
        ti = TrackInfo(
            artist="Radiohead",
            title="Creep",
            album="Pablo Honey",
            track_id="6rqhFgbbKwnb9MLmUQDhG6",
            duration_ms=238000,
            position_ms=45000,
            volume=0.6,
            status=PlaybackStatus.PLAYING,
        )
        self.assertEqual(ti.artist, "Radiohead")
        self.assertEqual(ti.title, "Creep")
        self.assertEqual(ti.album, "Pablo Honey")
        self.assertEqual(ti.track_id, "6rqhFgbbKwnb9MLmUQDhG6")
        self.assertEqual(ti.duration_ms, 238000)
        self.assertEqual(ti.position_ms, 45000)
        self.assertEqual(ti.volume, 0.6)
        self.assertEqual(ti.status, PlaybackStatus.PLAYING)

    def test_empty_metadata(self):
        """With no arguments, all text fields default to '' and numerics to 0."""
        ti = TrackInfo()
        self.assertEqual(ti.artist, "")
        self.assertEqual(ti.title, "")
        self.assertEqual(ti.album, "")
        self.assertEqual(ti.track_id, "")
        self.assertEqual(ti.duration_ms, 0)
        self.assertEqual(ti.position_ms, 0)
        self.assertEqual(ti.volume, 0.0)
        self.assertEqual(ti.status, PlaybackStatus.STOPPED)

    def test_partial_metadata(self):
        """Only a subset of fields set should leave the rest at defaults."""
        ti = TrackInfo(
            artist="Daft Punk",
            title="One More Time",
            duration_ms=320000,
            position_ms=100000,
            status=PlaybackStatus.PAUSED,
        )
        self.assertEqual(ti.artist, "Daft Punk")
        self.assertEqual(ti.title, "One More Time")
        self.assertEqual(ti.album, "")       # default
        self.assertEqual(ti.track_id, "")    # default
        self.assertEqual(ti.duration_ms, 320000)
        self.assertEqual(ti.position_ms, 100000)
        self.assertEqual(ti.volume, 0.0)      # default
        self.assertEqual(ti.status, PlaybackStatus.PAUSED)


class TestParsedURI(unittest.TestCase):
    """ParsedURI is a dataclass representing a validated Spotify URI."""

    def test_track_uri(self):
        """A track URI should parse into type, id, and full uri fields."""
        pu = ParsedURI(
            type="track",
            id="6rqhFgbbKwnb9MLmUQDhG6",
            uri="spotify:track:6rqhFgbbKwnb9MLmUQDhG6",
        )
        self.assertEqual(pu.type, "track")
        self.assertEqual(pu.id, "6rqhFgbbKwnb9MLmUQDhG6")
        self.assertEqual(pu.uri, "spotify:track:6rqhFgbbKwnb9MLmUQDhG6")

    def test_playlist_uri(self):
        """A playlist URI should parse into a playlist type."""
        uri = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
        pu = ParsedURI(
            type="playlist",
            id="37i9dQZF1DXcBWIGoYBM5M",
            uri=uri,
        )
        self.assertEqual(pu.type, "playlist")
        self.assertEqual(pu.id, "37i9dQZF1DXcBWIGoYBM5M")
        self.assertEqual(pu.uri, uri)


class TestPlaybackStatus(unittest.TestCase):
    """PlaybackStatus is an enum mirroring playerctl --status output."""

    def test_enum_values(self):
        """The enum must expose exactly PLAYING, PAUSED, and STOPPED."""
        self.assertEqual(PlaybackStatus.PLAYING.value, "PLAYING")
        self.assertEqual(PlaybackStatus.PAUSED.value, "PAUSED")
        self.assertEqual(PlaybackStatus.STOPPED.value, "STOPPED")

    def test_from_playerctl_playing(self):
        """playerctl returns 'Playing' → PlaybackStatus.PLAYING."""
        self.assertEqual(PlaybackStatus.from_playerctl("Playing"), PlaybackStatus.PLAYING)

    def test_from_playerctl_paused(self):
        """playerctl returns 'Paused' → PlaybackStatus.PAUSED."""
        self.assertEqual(PlaybackStatus.from_playerctl("Paused"), PlaybackStatus.PAUSED)

    def test_from_playerctl_stopped(self):
        """playerctl returns 'Stopped' → PlaybackStatus.STOPPED."""
        self.assertEqual(PlaybackStatus.from_playerctl("Stopped"), PlaybackStatus.STOPPED)

    def test_from_playerctl_unknown(self):
        """An unrecognised status string should raise ValueError."""
        with self.assertRaises(ValueError):
            PlaybackStatus.from_playerctl("Unknown")


if __name__ == "__main__":
    unittest.main()
