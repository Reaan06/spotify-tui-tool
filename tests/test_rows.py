"""Strict-TDD tests for stable identity-preserving browse rows."""

import unittest

from spotify_tui_tool.ui.rows import (
    BrowseRow,
    rows_from_library,
    rows_from_playlists,
    rows_from_search,
)
from spotify_tui_tool.ui.views.search import SearchView


class TestBrowseRows(unittest.TestCase):
    def test_browse_cells_escape_markup(self):
        view = SearchView()
        row = BrowseRow(
            "track",
            "t1",
            title="[red]title[/red]",
            subtitle="[bold]artist[/bold]",
            detail="[link=https://invalid]album[/link]",
            auxiliary="[green]duration[/green]",
        )
        self.assertEqual(
            view._row_cells(row),
            (
                r"\[red]title\[/red]",
                r"\[bold]artist\[/bold]",
                r"\[link=https://invalid]album\[/link]",
                r"\[green]duration\[/green]",
            ),
        )

    def test_duplicate_labels_keep_distinct_identity_and_uri(self):
        payload = {
            "tracks": {
                "items": [
                    {
                        "id": "first",
                        "uri": "spotify:track:first",
                        "name": "Same Song",
                        "artists": [{"name": "Same Artist"}],
                    },
                    {
                        "id": "second",
                        "uri": "spotify:track:second",
                        "name": "Same Song",
                        "artists": [{"name": "Same Artist"}],
                    },
                ]
            }
        }

        rows = rows_from_search(payload)

        self.assertEqual([row.key for row in rows], ["track:first", "track:second"])
        self.assertEqual([row.uri for row in rows], [
            "spotify:track:first",
            "spotify:track:second",
        ])
        self.assertEqual(rows[0].title, rows[1].title)

    def test_library_rows_preserve_track_identity_through_refresh(self):
        original = rows_from_library([
            {
                "track": {
                    "id": "t1",
                    "uri": "spotify:track:t1",
                    "name": "Original title",
                    "artists": [{"name": "Artist"}],
                }
            }
        ])[0]
        refreshed = rows_from_library([
            {
                "track": {
                    "id": "t1",
                    "uri": "spotify:track:t1",
                    "name": "Updated title",
                    "artists": [{"name": "Artist"}],
                }
            }
        ])[0]

        self.assertEqual(original.key, refreshed.key)
        self.assertEqual(refreshed.id, "t1")
        self.assertEqual(refreshed.uri, "spotify:track:t1")

    def test_search_and_playlist_rows_mark_non_tracks_non_playable(self):
        rows = rows_from_search({
            "albums": {"items": [{
                "id": "album-1",
                "uri": "spotify:album:album-1",
                "name": "Album",
                "artists": [{"name": "Artist"}],
                "total_tracks": 9,
            }]},
            "artists": {"items": [{
                "id": "artist-1",
                "name": "Artist",
                "genres": ["indie"],
            }]},
        })
        playlists = rows_from_playlists([{
            "id": "playlist-1",
            "uri": "spotify:playlist:playlist-1",
            "name": "Road Trip",
            "tracks": {"total": 12},
        }])

        self.assertEqual(rows[0].kind, "album")
        self.assertFalse(rows[0].playable)
        self.assertEqual(rows[1].kind, "artist")
        self.assertFalse(rows[1].playable)
        self.assertFalse(playlists[0].playable)
        self.assertEqual(playlists[0].key, "playlist:playlist-1")

    def test_browse_row_key_does_not_depend_on_rendered_text(self):
        row = BrowseRow(
            kind="track",
            id="stable-id",
            uri="spotify:track:stable-id",
            title="A title that can change",
            subtitle="An artist",
            playable=True,
        )

        self.assertEqual(row.key, "track:stable-id")
        self.assertNotEqual(row.key, row.title)

    def test_explicit_null_nested_api_fields_are_safe(self):
        rows = rows_from_search({
            "tracks": {"items": [{
                "id": "t1", "name": "Track", "album": None,
                "artists": None,
            }]},
            "albums": None,
            "artists": {"items": [{"id": "a1", "name": "Artist", "genres": None}]},
        })
        playlist = rows_from_playlists([{"id": "p1", "name": "Playlist", "tracks": None}])
        self.assertEqual(len(rows), 2)
        self.assertEqual(playlist[0].detail, "0")

    def test_malformed_collection_entries_are_skipped(self):
        self.assertEqual(rows_from_library([None]), [])
        self.assertEqual(rows_from_search({"tracks": {"items": None}}), [])

    def test_duplicate_identity_fallback_always_terminates(self):
        rows = rows_from_search({
            "tracks": {"items": [
                {"id": "index-1", "name": "First"},
                {"id": "index-1", "name": "Second"},
            ]}
        })
        self.assertEqual([row.id for row in rows], ["index-1", "index-1-2"])


if __name__ == "__main__":
    unittest.main()
