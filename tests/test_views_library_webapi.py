"""Tests for LibraryView with WebAPI integration."""

import asyncio
import unittest
from unittest.mock import MagicMock, patch

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.views.library import LibraryView


class _LibraryTestApp(App):
    def compose(self) -> ComposeResult:
        yield LibraryView()


class TestLibraryViewWebAPI(unittest.TestCase):
    """Test LibraryView with WebAPI data."""

    def test_import(self):
        from spotify_tui_tool.ui.views.library import LibraryView
        self.assertTrue(callable(LibraryView))

    def test_instantiate(self):
        widget = LibraryView()
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, LibraryView)

    def test_compose_returns_widgets(self):
        async def _test():
            app = _LibraryTestApp()
            async with app.run_test():
                children = list(app.query(LibraryView).first().children)
                self.assertGreater(len(children), 0)
        asyncio.run(_test())

    def test_default_not_authenticated(self):
        async def _test():
            app = _LibraryTestApp()
            async with app.run_test():
                view = app.query_one(LibraryView)
                self.assertFalse(view.is_authenticated)
        asyncio.run(_test())

    def test_set_authenticated_shows_table(self):
        async def _test():
            app = _LibraryTestApp()
            async with app.run_test():
                view = app.query_one(LibraryView)
                view.set_authenticated(True)
                table = app.query_one("#liked-songs-table")
                self.assertTrue(table.display)
                message = app.query_one("#library-message")
                self.assertFalse(message.display)
        asyncio.run(_test())

    def test_set_unauthenticated_shows_message(self):
        async def _test():
            app = _LibraryTestApp()
            async with app.run_test():
                view = app.query_one(LibraryView)
                view.set_authenticated(True)
                view.set_authenticated(False)
                table = app.query_one("#liked-songs-table")
                self.assertFalse(table.display)
                message = app.query_one("#library-message")
                self.assertTrue(message.display)
        asyncio.run(_test())

    def test_update_liked_songs_populates_table(self):
        async def _test():
            app = _LibraryTestApp()
            async with app.run_test():
                view = app.query_one(LibraryView)
                view.set_authenticated(True)
                songs = [
                    {
                        "track": {
                            "name": "Test Song",
                            "artists": [{"name": "Test Artist"}],
                            "album": {"name": "Test Album"},
                            "duration_ms": 200000,
                        }
                    }
                ]
                view.update_liked_songs(songs)
                table = app.query_one("#liked-songs-table")
                self.assertEqual(table.row_count, 1)
        asyncio.run(_test())

    def test_update_liked_songs_multiple_tracks(self):
        async def _test():
            app = _LibraryTestApp()
            async with app.run_test():
                view = app.query_one(LibraryView)
                view.set_authenticated(True)
                songs = [
                    {
                        "track": {
                            "name": "Song A",
                            "artists": [{"name": "Artist A"}],
                            "album": {"name": "Album A"},
                            "duration_ms": 180000,
                        }
                    },
                    {
                        "track": {
                            "name": "Song B",
                            "artists": [{"name": "Artist B"}],
                            "album": {"name": "Album B"},
                            "duration_ms": 240000,
                        }
                    },
                ]
                view.update_liked_songs(songs)
                table = app.query_one("#liked-songs-table")
                self.assertEqual(table.row_count, 2)
        asyncio.run(_test())

    def test_update_liked_songs_empty(self):
        async def _test():
            app = _LibraryTestApp()
            async with app.run_test():
                view = app.query_one(LibraryView)
                view.set_authenticated(True)
                view.update_liked_songs([])
                table = app.query_one("#liked-songs-table")
                self.assertEqual(table.row_count, 0)
        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
