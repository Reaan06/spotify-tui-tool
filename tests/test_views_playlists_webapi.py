"""Tests for PlaylistsView with WebAPI integration."""

import asyncio
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.views.playlists import PlaylistsView


class _PlaylistsTestApp(App):
    def compose(self) -> ComposeResult:
        yield PlaylistsView()


class TestPlaylistsViewWebAPI(unittest.TestCase):
    """Test PlaylistsView with WebAPI data."""

    def test_import(self):
        from spotify_tui_tool.ui.views.playlists import PlaylistsView
        self.assertTrue(callable(PlaylistsView))

    def test_instantiate(self):
        widget = PlaylistsView()
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, PlaylistsView)

    def test_compose_returns_widgets(self):
        async def _test():
            app = _PlaylistsTestApp()
            async with app.run_test():
                children = list(app.query(PlaylistsView).first().children)
                self.assertGreater(len(children), 0)
        asyncio.run(_test())

    def test_default_not_authenticated(self):
        async def _test():
            app = _PlaylistsTestApp()
            async with app.run_test():
                view = app.query_one(PlaylistsView)
                self.assertFalse(view.is_authenticated)
        asyncio.run(_test())

    def test_set_authenticated_shows_table(self):
        async def _test():
            app = _PlaylistsTestApp()
            async with app.run_test():
                view = app.query_one(PlaylistsView)
                view.set_authenticated(True)
                table = app.query_one("#playlists-table")
                self.assertTrue(table.display)
                message = app.query_one("#playlists-message")
                self.assertFalse(message.display)
        asyncio.run(_test())

    def test_set_unauthenticated_shows_message(self):
        async def _test():
            app = _PlaylistsTestApp()
            async with app.run_test():
                view = app.query_one(PlaylistsView)
                view.set_authenticated(True)
                view.set_authenticated(False)
                table = app.query_one("#playlists-table")
                self.assertFalse(table.display)
                message = app.query_one("#playlists-message")
                self.assertTrue(message.display)
        asyncio.run(_test())

    def test_update_playlists_populates_table(self):
        async def _test():
            app = _PlaylistsTestApp()
            async with app.run_test():
                view = app.query_one(PlaylistsView)
                view.set_authenticated(True)
                playlists = [
                    {
                        "name": "My Playlist",
                        "tracks": {"total": 25},
                        "description": "A test playlist",
                    }
                ]
                view.update_playlists(playlists)
                table = app.query_one("#playlists-table")
                self.assertEqual(table.row_count, 1)
        asyncio.run(_test())

    def test_update_playlists_multiple(self):
        async def _test():
            app = _PlaylistsTestApp()
            async with app.run_test():
                view = app.query_one(PlaylistsView)
                view.set_authenticated(True)
                playlists = [
                    {
                        "name": "Playlist A",
                        "tracks": {"total": 10},
                        "description": "First",
                    },
                    {
                        "name": "Playlist B",
                        "tracks": {"total": 20},
                        "description": "Second",
                    },
                ]
                view.update_playlists(playlists)
                table = app.query_one("#playlists-table")
                self.assertEqual(table.row_count, 2)
        asyncio.run(_test())

    def test_update_playlists_empty(self):
        async def _test():
            app = _PlaylistsTestApp()
            async with app.run_test():
                view = app.query_one(PlaylistsView)
                view.set_authenticated(True)
                view.update_playlists([])
                table = app.query_one("#playlists-table")
                self.assertEqual(table.row_count, 0)
        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
