"""Tests for ContentArea component."""

import asyncio
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.content import ContentArea


class _ContentTestApp(App):
    def compose(self) -> ComposeResult:
        yield ContentArea()


class TestContentArea(unittest.TestCase):
    """Test ContentArea can be instantiated and composed."""

    def test_import(self):
        from spotify_tui_tool.ui.content import ContentArea
        self.assertTrue(callable(ContentArea))

    def test_instantiate(self):
        widget = ContentArea()
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, ContentArea)

    def test_compose_returns_widgets(self):
        async def _test():
            app = _ContentTestApp()
            async with app.run_test():
                view = app.query_one("#current-view")
                self.assertIsNotNone(view)
        asyncio.run(_test())

    def test_default_view(self):
        widget = ContentArea()
        self.assertEqual(widget.current_view, "home")

    def test_view_content_keys(self):
        expected = {
            "home",
            "library",
            "playlists",
            "search",
            "settings",
            "help",
            "login",
        }
        self.assertEqual(set(ContentArea.VIEW_WIDGETS.keys()), expected)

    def test_switch_view(self):
        async def _test():
            app = _ContentTestApp()
            async with app.run_test():
                widget = app.query_one(ContentArea)
                await widget.switch_view("search")
                self.assertEqual(widget.current_view, "search")
        asyncio.run(_test())

    def test_switch_view_same_noop(self):
        async def _test():
            widget = ContentArea()
            await widget.switch_view("home")
            self.assertEqual(widget.current_view, "home")
        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
