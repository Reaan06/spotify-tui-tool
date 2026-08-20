"""Tests for HelpView component."""

import asyncio
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.views.help import HelpView


class _HelpTestApp(App):
    def compose(self) -> ComposeResult:
        yield HelpView()


class TestHelpView(unittest.TestCase):
    """Test HelpView can be instantiated and composed."""

    def test_import(self):
        from spotify_tui_tool.ui.views.help import HelpView
        self.assertTrue(callable(HelpView))

    def test_instantiate(self):
        widget = HelpView()
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, HelpView)

    def test_compose_returns_widgets(self):
        async def _test():
            app = _HelpTestApp()
            async with app.run_test():
                children = list(app.query(HelpView).first().children)
                self.assertGreater(len(children), 0)
        asyncio.run(_test())

    def test_keybindings_defined(self):
        keys = [kb[0] for kb in HelpView.KEYBINDINGS]
        self.assertIn("Space", keys)
        self.assertIn("q", keys)
        self.assertIn("?", keys)
        self.assertIn("/", keys)

    def test_keybindings_have_three_fields(self):
        for kb in HelpView.KEYBINDINGS:
            self.assertEqual(len(kb), 3, f"Keybinding {kb} should have 3 fields")


if __name__ == "__main__":
    unittest.main()
