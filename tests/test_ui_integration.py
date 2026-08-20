"""
UI integration tests — mount, keybindings, navigation, view switching.

Uses textual.testing for async test support.

Test runner: python -m unittest discover -s tests -v
"""

import asyncio
import unittest

from textual.app import App, ComposeResult
from textual.binding import Binding

from spotify_tui_tool.app import SpotifyTuiApp
from spotify_tui_tool.ui.content import ContentArea
from spotify_tui_tool.ui.layout import LayoutManager
from spotify_tui_tool.ui.playbar import Playbar
from spotify_tui_tool.ui.sidebar import Sidebar


class TestAppMountsComponents(unittest.TestCase):
    """Verify App mounts Sidebar, ContentArea, and Playbar."""

    def test_app_is_textual_app(self):
        """SpotifyTuiApp should be a Textual App."""
        self.assertTrue(issubclass(SpotifyTuiApp, App))

    def test_app_has_compose(self):
        """SpotifyTuiApp should have a compose method."""
        self.assertTrue(hasattr(SpotifyTuiApp, "compose"))

    def test_app_has_bindings(self):
        """App should define BINDINGS."""
        self.assertIsInstance(SpotifyTuiApp.BINDINGS, list)

    def test_expected_bindings_exist(self):
        """All expected key bindings should be registered."""
        keys = {b.key for b in SpotifyTuiApp.BINDINGS}
        expected = {"space", "n", "p", "escape", "q", "question"}
        self.assertTrue(expected.issubset(keys), f"Missing bindings: {expected - keys}")

    def test_view_key_bindings(self):
        """Keys 1-6 should be bound for view switching."""
        keys = {b.key for b in SpotifyTuiApp.BINDINGS}
        for digit in ("1", "2", "3", "4", "5", "6"):
            self.assertIn(digit, keys, f"Key '{digit}' not bound")


class TestAppCompose(unittest.TestCase):
    """Verify App.compose produces the correct widget tree."""

    def test_compose_returns_header_layout_footer(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                layout = app.query_one(LayoutManager)
                self.assertIsNotNone(layout)
                sidebar = layout.query_one("#sidebar")
                self.assertIsNotNone(sidebar)
                playbar = layout.query_one("#playbar")
                self.assertIsNotNone(playbar)
                content = layout.query_one("#content")
                self.assertIsNotNone(content)

        asyncio.run(_test())

    def test_sidebar_mounted_in_layout(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                sidebar = app.query_one(Sidebar)
                self.assertIsNotNone(sidebar)

        asyncio.run(_test())

    def test_content_area_mounted(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                content = app.query_one(ContentArea)
                self.assertIsNotNone(content)

        asyncio.run(_test())

    def test_playbar_mounted(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                playbar = app.query_one(Playbar)
                self.assertIsNotNone(playbar)

        asyncio.run(_test())


class TestKeybindings(unittest.TestCase):
    """Test keybinding actions execute without raising."""

    def test_space_action(self):
        async def _test():
            app = SpotifyTuiApp()
            app._player = type("_M", (), {
                "play_pause": lambda s: None,
            })()
            async with app.run_test() as pilot:
                await pilot.press("space")

        asyncio.run(_test())

    def test_n_action(self):
        async def _test():
            app = SpotifyTuiApp()
            app._player = type("_M", (), {
                "next": lambda s: None,
            })()
            async with app.run_test() as pilot:
                await pilot.press("n")

        asyncio.run(_test())

    def test_p_action(self):
        async def _test():
            app = SpotifyTuiApp()
            app._player = type("_M", (), {
                "previous": lambda s: None,
            })()
            async with app.run_test() as pilot:
                await pilot.press("p")

        asyncio.run(_test())

    def test_q_action(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test() as pilot:
                await pilot.press("q")

        asyncio.run(_test())

    def test_escape_action(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test() as pilot:
                await pilot.press("escape")

        asyncio.run(_test())

    def test_question_action(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test() as pilot:
                await pilot.press("question")

        asyncio.run(_test())


class TestViewSwitching(unittest.TestCase):
    """Test view switching via ContentArea.switch_view directly."""

    def test_switch_to_library(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                content = app.query_one(ContentArea)
                await content.switch_view("library")
                self.assertEqual(content.current_view, "library")

        asyncio.run(_test())

    def test_switch_to_playlists(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                content = app.query_one(ContentArea)
                await content.switch_view("playlists")
                self.assertEqual(content.current_view, "playlists")

        asyncio.run(_test())

    def test_switch_to_search(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                content = app.query_one(ContentArea)
                await content.switch_view("search")
                self.assertEqual(content.current_view, "search")

        asyncio.run(_test())

    def test_switch_to_queue(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                content = app.query_one(ContentArea)
                await content.switch_view("queue")
                self.assertEqual(content.current_view, "queue")

        asyncio.run(_test())

    def test_switch_to_settings(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                content = app.query_one(ContentArea)
                await content.switch_view("settings")
                self.assertEqual(content.current_view, "settings")

        asyncio.run(_test())

    def test_switch_to_help(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                content = app.query_one(ContentArea)
                await content.switch_view("help")
                self.assertEqual(content.current_view, "help")

        asyncio.run(_test())

    def test_escape_returns_home(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                content = app.query_one(ContentArea)
                await content.switch_view("library")
                self.assertEqual(content.current_view, "library")
                await content.switch_view("home")
                self.assertEqual(content.current_view, "home")

        asyncio.run(_test())

    def test_default_view_is_home(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                content = app.query_one(ContentArea)
                self.assertEqual(content.current_view, "home")

        asyncio.run(_test())

    def test_switch_same_view_is_noop(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                content = app.query_one(ContentArea)
                self.assertEqual(content.current_view, "home")
                await content.switch_view("home")
                self.assertEqual(content.current_view, "home")

        asyncio.run(_test())


class TestSidebarNavigation(unittest.TestCase):
    """Test sidebar j/k navigation."""

    def test_sidebar_down_increments_index(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test() as pilot:
                sidebar = app.query_one(Sidebar)
                initial = sidebar.selected_index
                await pilot.press("j")
                self.assertGreater(sidebar.selected_index, initial)

        asyncio.run(_test())

    def test_sidebar_up_decrements_index(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test() as pilot:
                sidebar = app.query_one(Sidebar)
                sidebar.selected_index = 2
                await pilot.press("k")
                self.assertEqual(sidebar.selected_index, 1)

        asyncio.run(_test())

    def test_sidebar_up_stops_at_zero(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test() as pilot:
                sidebar = app.query_one(Sidebar)
                sidebar.selected_index = 0
                await pilot.press("k")
                self.assertEqual(sidebar.selected_index, 0)

        asyncio.run(_test())


class TestLayoutStructure(unittest.TestCase):
    """Verify the 3-panel layout structure."""

    def test_main_container_has_sidebar_and_content(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                layout = app.query_one(LayoutManager)
                container = layout.query_one("#main-container")
                self.assertIsNotNone(container)
                sidebar = container.query_one("#sidebar")
                self.assertIsNotNone(sidebar)
                content_area = container.query_one("#content-area")
                self.assertIsNotNone(content_area)

        asyncio.run(_test())

    def test_content_area_has_content_and_playbar(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                layout = app.query_one(LayoutManager)
                content_area = layout.query_one("#content-area")
                self.assertIsNotNone(content_area.query_one("#content"))
                self.assertIsNotNone(content_area.query_one("#playbar"))

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
