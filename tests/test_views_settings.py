"""Tests for SettingsView component."""

import asyncio
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.views.settings import SettingsView


class _SettingsTestApp(App):
    def compose(self) -> ComposeResult:
        yield SettingsView()


class TestSettingsView(unittest.TestCase):
    """Test SettingsView can be instantiated and composed."""

    def test_import(self):
        from spotify_tui_tool.ui.views.settings import SettingsView
        self.assertTrue(callable(SettingsView))

    def test_instantiate(self):
        widget = SettingsView()
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, SettingsView)

    def test_compose_returns_widgets(self):
        async def _test():
            app = _SettingsTestApp()
            async with app.run_test():
                children = list(app.query(SettingsView).first().children)
                self.assertGreater(len(children), 0)
        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
