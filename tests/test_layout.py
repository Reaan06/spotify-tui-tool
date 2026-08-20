"""Tests for LayoutManager component."""

import asyncio
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.layout import LayoutManager


class _LayoutTestApp(App):
    def compose(self) -> ComposeResult:
        yield LayoutManager()


class TestLayoutManager(unittest.TestCase):
    """Test LayoutManager can be instantiated and composed."""

    def test_import(self):
        from spotify_tui_tool.ui.layout import LayoutManager
        self.assertTrue(callable(LayoutManager))

    def test_instantiate(self):
        widget = LayoutManager()
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, LayoutManager)

    def test_compose_returns_widgets(self):
        async def _test():
            app = _LayoutTestApp()
            async with app.run_test():
                container = app.query_one("#main-container")
                self.assertIsNotNone(container)
        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
