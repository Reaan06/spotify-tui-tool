"""Tests for HomeView component."""

import asyncio
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.views.home import HomeView


class _HomeTestApp(App):
    def compose(self) -> ComposeResult:
        yield HomeView()


class TestHomeView(unittest.TestCase):
    """Test HomeView can be instantiated and composed."""

    def test_import(self):
        from spotify_tui_tool.ui.views.home import HomeView
        self.assertTrue(callable(HomeView))

    def test_instantiate(self):
        widget = HomeView()
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, HomeView)

    def test_compose_returns_widgets(self):
        async def _test():
            app = _HomeTestApp()
            async with app.run_test():
                children = list(app.query(HomeView).first().children)
                self.assertGreater(len(children), 0)
        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
