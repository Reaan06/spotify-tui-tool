"""Tests for LibraryView component."""

import asyncio
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.views.library import LibraryView


class _LibraryTestApp(App):
    def compose(self) -> ComposeResult:
        yield LibraryView()


class TestLibraryView(unittest.TestCase):
    """Test LibraryView can be instantiated and composed."""

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


if __name__ == "__main__":
    unittest.main()
