"""Textual pilots for the Phase 1 shell at compact and wide sizes."""

import asyncio
import unittest

from textual.events import MouseScrollDown

from spotify_tui_tool.app import SpotifyTuiApp
from spotify_tui_tool.ui.content import ContentArea
from spotify_tui_tool.ui.layout import LayoutManager
from spotify_tui_tool.ui.playbar import Playbar
from spotify_tui_tool.ui.sidebar import Sidebar


class TestShellPilot(unittest.TestCase):
    def test_wide_mount_keeps_all_regions_persistent(self):
        async def scenario():
            app = SpotifyTuiApp()
            async with app.run_test(size=(120, 30)):
                layout = app.query_one(LayoutManager)
                self.assertFalse(layout.is_compact)
                self.assertIsInstance(app.query_one(Sidebar), Sidebar)
                self.assertIsInstance(app.query_one(ContentArea), ContentArea)
                self.assertIsInstance(app.query_one(Playbar), Playbar)
                self.assertGreater(app.query_one("#sidebar").region.width, 16)

        asyncio.run(scenario())

    def test_compact_mount_degrades_sidebar_without_losing_regions(self):
        async def scenario():
            app = SpotifyTuiApp()
            async with app.run_test(size=(80, 24)):
                layout = app.query_one(LayoutManager)
                self.assertTrue(layout.is_compact)
                self.assertEqual(app.query_one("#sidebar").region.width, 16)
                self.assertIsNotNone(app.query_one("#content"))
                self.assertIsNotNone(app.query_one("#playbar"))

        asyncio.run(scenario())

    def test_directional_focus_navigation_and_visible_selection(self):
        async def scenario():
            app = SpotifyTuiApp()
            async with app.run_test(size=(100, 28)) as pilot:
                sidebar = app.query_one(Sidebar)
                self.assertEqual(app._state.focus_region, "sidebar")
                initial = sidebar.selected_index

                await pilot.press("j")
                self.assertEqual(sidebar.selected_index, initial + 1)
                await pilot.press("l")
                self.assertEqual(app._state.focus_region, "content")
                await pilot.press("right")
                self.assertEqual(app._state.focus_region, "playbar")
                await pilot.press("left")
                self.assertEqual(app._state.focus_region, "content")
                await pilot.press("h")
                self.assertEqual(app._state.focus_region, "sidebar")
                self.assertIn("▸", str(sidebar.get_selected_item().render()))

        asyncio.run(scenario())

    def test_transient_help_search_and_q_escape_semantics(self):
        async def scenario():
            app = SpotifyTuiApp()
            async with app.run_test(size=(100, 28)) as pilot:
                content = app.query_one(ContentArea)

                app._state.api_pending = True
                await pilot.press("question")
                self.assertEqual(content.current_view, "help")
                self.assertEqual(app._state.transient_view, "help")
                await pilot.press("escape")
                self.assertEqual(content.current_view, "home")

                await pilot.press("slash")
                self.assertEqual(content.current_view, "search")
                self.assertEqual(app._state.transient_view, "search")
                await pilot.press("q")
                self.assertEqual(content.current_view, "home")
                self.assertFalse(app.return_value)

        asyncio.run(scenario())

    def test_mouse_sidebar_activation_and_content_scroll_are_local(self):
        async def scenario():
            app = SpotifyTuiApp()
            async with app.run_test(size=(110, 30)) as pilot:
                sidebar = app.query_one(Sidebar)
                content = app.query_one(ContentArea)
                await pilot.click("#lib-liked", offset=(2, 0))
                await pilot.pause()
                self.assertEqual(content.current_view, "library")
                self.assertEqual(app._state.focus_region, "sidebar")

                before = content.scroll_requests
                x, y = content.region.x + 2, content.region.y + 2
                app.screen._forward_event(
                    MouseScrollDown(
                        None, x, y, 0, 1, 0, False, False, False,
                        screen_x=x, screen_y=y,
                    )
                )
                await pilot.pause()
                self.assertEqual(content.scroll_requests, before + 1)
                self.assertEqual(app._state.focus_region, "content")

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
