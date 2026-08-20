"""Tests for QueueView component."""

import asyncio
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.views.queue import QueueView


class _QueueTestApp(App):
    def compose(self) -> ComposeResult:
        yield QueueView()


class TestQueueView(unittest.TestCase):
    """Test QueueView can be instantiated and composed."""

    def test_import(self):
        from spotify_tui_tool.ui.views.queue import QueueView
        self.assertTrue(callable(QueueView))

    def test_instantiate(self):
        widget = QueueView()
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, QueueView)

    def test_compose_returns_widgets(self):
        async def _test():
            app = _QueueTestApp()
            async with app.run_test():
                children = list(app.query(QueueView).first().children)
                self.assertGreater(len(children), 0)
        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
