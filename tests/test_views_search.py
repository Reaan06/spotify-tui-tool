"""Tests for SearchView component."""

import asyncio
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.views.search import SearchView


class _SearchTestApp(App):
    def compose(self) -> ComposeResult:
        yield SearchView()


class TestSearchView(unittest.TestCase):
    """Test SearchView can be instantiated and composed."""

    def test_import(self):
        from spotify_tui_tool.ui.views.search import SearchView
        self.assertTrue(callable(SearchView))

    def test_instantiate(self):
        widget = SearchView()
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, SearchView)

    def test_compose_returns_widgets(self):
        async def _test():
            app = _SearchTestApp()
            async with app.run_test():
                search_input = app.query_one("#search-input")
                self.assertIsNotNone(search_input)
        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
