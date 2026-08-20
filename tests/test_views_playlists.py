"""Tests for PlaylistsView component."""

import asyncio
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.views.playlists import PlaylistsView


class _PlaylistsTestApp(App):
    def compose(self) -> ComposeResult:
        yield PlaylistsView()


class TestPlaylistsView(unittest.TestCase):
    """Test PlaylistsView can be instantiated and composed."""

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


if __name__ == "__main__":
    unittest.main()
