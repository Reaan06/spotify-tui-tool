"""
Tests for SearchService — URI validation, parsing, opening, and history.

Strict TDD: tests written FIRST (RED).  PlayerController is injected as a
mock so no real playerctl calls are made.

Test runner: python3 -m unittest
"""
import unittest
from unittest.mock import MagicMock

from spotify_tui_tool.search import SearchService
from spotify_tui_tool.models import ParsedURI
from spotify_tui_tool.exceptions import InvalidURIError, PlaybackError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TRACK_ID = "6rqhFgbbKwnb9MLmUQDhG6"
PLAYLIST_ID = "37i9dQZF1DXcBWIGoYBM5M"
ALBUM_ID = "1Je1IMUlBXcx1Fz0WE7oPT"
ARTIST_ID = "0OdUWJ0sBjDrqHygGUXeCF"


def _mock_player():
    """Return a MagicMock standing in for PlayerController."""
    return MagicMock()


def _make_uri(index: int) -> str:
    """Generate a unique 22-char-ID track URI for index 0–9999."""
    # 'a' × 18 + 4-digit zero-padded index → exactly 22 chars, all alphanumeric
    id_str = "a" * 18 + f"{index:04d}"
    return f"spotify:track:{id_str}"


# ---------------------------------------------------------------------------
# URI Validation
# ---------------------------------------------------------------------------

class TestUriValidation(unittest.TestCase):
    """validate_uri must accept valid URIs and reject malformed ones."""

    def setUp(self):
        self.service = SearchService(player=_mock_player())

    # -- valid URIs --------------------------------------------------------

    def test_valid_track_uri(self):
        """A well-formed track URI must return a ParsedURI."""
        result = self.service.validate_uri(f"spotify:track:{TRACK_ID}")
        self.assertIsNotNone(result)
        self.assertEqual(result.type, "track")
        self.assertEqual(result.id, TRACK_ID)
        self.assertEqual(result.uri, f"spotify:track:{TRACK_ID}")

    def test_valid_playlist_uri(self):
        """A well-formed playlist URI must return a ParsedURI."""
        result = self.service.validate_uri(f"spotify:playlist:{PLAYLIST_ID}")
        self.assertIsNotNone(result)
        self.assertEqual(result.type, "playlist")
        self.assertEqual(result.id, PLAYLIST_ID)

    def test_valid_album_uri(self):
        """A well-formed album URI must return a ParsedURI."""
        result = self.service.validate_uri(f"spotify:album:{ALBUM_ID}")
        self.assertIsNotNone(result)
        self.assertEqual(result.type, "album")
        self.assertEqual(result.id, ALBUM_ID)

    def test_valid_artist_uri(self):
        """A well-formed artist URI must return a ParsedURI."""
        result = self.service.validate_uri(f"spotify:artist:{ARTIST_ID}")
        self.assertIsNotNone(result)
        self.assertEqual(result.type, "artist")
        self.assertEqual(result.id, ARTIST_ID)

    def test_valid_show_uri(self):
        """A show URI is also a valid type."""
        show_id = "4oTcMb8VnPns6stnTujq1t"
        result = self.service.validate_uri(f"spotify:show:{show_id}")
        self.assertIsNotNone(result)
        self.assertEqual(result.type, "show")
        self.assertEqual(result.id, show_id)

    # -- invalid URIs ------------------------------------------------------

    def test_invalid_type_prefix(self):
        """An unsupported type (e.g. 'movie') must return None."""
        result = self.service.validate_uri(f"spotify:movie:{TRACK_ID}")
        self.assertIsNone(result)

    def test_id_too_short(self):
        """An ID shorter than 22 chars must return None."""
        result = self.service.validate_uri("spotify:track:6rqhFg")
        self.assertIsNone(result)

    def test_id_too_long(self):
        """An ID longer than 22 chars must return None."""
        result = self.service.validate_uri(f"spotify:track:{TRACK_ID}Extra")
        self.assertIsNone(result)

    def test_empty_input(self):
        """An empty string must return None."""
        self.assertIsNone(self.service.validate_uri(""))

    def test_whitespace_trimmed(self):
        """Leading/trailing whitespace must be trimmed before validation."""
        result = self.service.validate_uri(f"  spotify:track:{TRACK_ID}  ")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, TRACK_ID)

    def test_http_url_converted(self):
        """open.spotify.com URL must be converted to a spotify: URI."""
        url = f"https://open.spotify.com/track/{TRACK_ID}"
        result = self.service.validate_uri(url)
        self.assertIsNotNone(result)
        self.assertEqual(result.type, "track")
        self.assertEqual(result.id, TRACK_ID)
        self.assertEqual(result.uri, f"spotify:track:{TRACK_ID}")

    def test_http_url_playlist_converted(self):
        """Playlist URL conversion must preserve the type."""
        url = f"https://open.spotify.com/playlist/{PLAYLIST_ID}"
        result = self.service.validate_uri(url)
        self.assertIsNotNone(result)
        self.assertEqual(result.type, "playlist")
        self.assertEqual(result.uri, f"spotify:playlist:{PLAYLIST_ID}")


class TestParseUri(unittest.TestCase):
    """parse_uri raises InvalidURIError for bad input."""

    def setUp(self):
        self.service = SearchService(player=_mock_player())

    def test_parse_valid(self):
        """parse_uri of a valid URI returns a ParsedURI."""
        result = self.service.parse_uri(f"spotify:track:{TRACK_ID}")
        self.assertEqual(result.type, "track")
        self.assertEqual(result.id, TRACK_ID)

    def test_parse_invalid_raises(self):
        """parse_uri of an invalid URI raises InvalidURIError."""
        with self.assertRaises(InvalidURIError):
            self.service.parse_uri("not-a-uri")


# ---------------------------------------------------------------------------
# URI Opening
# ---------------------------------------------------------------------------

class TestOpenUri(unittest.TestCase):
    """open_uri must validate, call playerctl, and handle failures."""

    def test_open_valid_track(self):
        """A valid URI must reach playerctl open with the canonical URI."""
        mock_player = _mock_player()
        service = SearchService(player=mock_player)
        service.open_uri(f"spotify:track:{TRACK_ID}")
        mock_player.open_uri.assert_called_once_with(f"spotify:track:{TRACK_ID}")

    def test_open_valid_playlist(self):
        """A playlist URI must also reach playerctl open."""
        mock_player = _mock_player()
        service = SearchService(player=mock_player)
        pid = "37i9dQZF1DXcBWIGoYBM5M"
        service.open_uri(f"spotify:playlist:{pid}")
        mock_player.open_uri.assert_called_once_with(f"spotify:playlist:{pid}")

    def test_open_from_url(self):
        """A URL must be converted then passed to playerctl as a URI."""
        mock_player = _mock_player()
        service = SearchService(player=mock_player)
        service.open_uri(f"https://open.spotify.com/track/{TRACK_ID}")
        mock_player.open_uri.assert_called_once_with(f"spotify:track:{TRACK_ID}")

    def test_open_invalid_raises_no_call(self):
        """An invalid URI must raise InvalidURIError with zero playerctl calls."""
        mock_player = _mock_player()
        service = SearchService(player=mock_player)
        with self.assertRaises(InvalidURIError):
            service.open_uri("not-a-uri")
        mock_player.open_uri.assert_not_called()

    def test_open_failure_raises_playback_error(self):
        """If playerctl open fails, PlaybackError must propagate."""
        mock_player = _mock_player()
        mock_player.open_uri.side_effect = PlaybackError(
            "Could not open URI", "Could not open URI"
        )
        service = SearchService(player=mock_player)
        with self.assertRaises(PlaybackError) as ctx:
            service.open_uri(f"spotify:track:{TRACK_ID}")
        self.assertIn("Could not open URI", str(ctx.exception))
        # history should NOT be updated on failure
        self.assertEqual(len(service.history), 0)


# ---------------------------------------------------------------------------
# Search History
# ---------------------------------------------------------------------------

class TestHistory(unittest.TestCase):
    """History keeps last 10 opened URIs, most-recent-first, de-duplicated."""

    def test_history_add(self):
        """After one open, history[0] is that URI."""
        mock_player = _mock_player()
        service = SearchService(player=mock_player)
        uri = f"spotify:track:{TRACK_ID}"
        service.open_uri(uri)
        self.assertEqual(len(service.history), 1)
        self.assertEqual(service.history[0].uri, uri)

    def test_history_cap(self):
        """After 11 opens, history must hold exactly 10, oldest removed."""
        mock_player = _mock_player()
        service = SearchService(player=mock_player)
        for i in range(11):
            service.open_uri(_make_uri(i))
        self.assertEqual(len(service.history), 10)
        # Position 0 is the most recent (11th open, index 10)
        self.assertEqual(service.history[0].uri, _make_uri(10))

    def test_history_dedup(self):
        """Re-opening a URI moves it to position 0 without duplicating."""
        mock_player = _mock_player()
        service = SearchService(player=mock_player)
        first = f"spotify:track:{'A' * 22}"
        second = f"spotify:track:{'B' * 22}"
        service.open_uri(first)
        service.open_uri(second)
        service.open_uri(first)  # reopen first
        self.assertEqual(len(service.history), 2)
        self.assertEqual(service.history[0].uri, first)
        self.assertEqual(service.history[1].uri, second)
        # No duplicates
        uris = [h.uri for h in service.history]
        self.assertEqual(len(set(uris)), len(uris))


if __name__ == "__main__":
    unittest.main()
