"""Tests for Sidebar component."""

import asyncio
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.sidebar import Sidebar, SidebarItem, SidebarSection


class TestSidebarItem(unittest.TestCase):
    """Test SidebarItem can be instantiated."""

    def test_import(self):
        from spotify_tui_tool.ui.sidebar import SidebarItem
        self.assertTrue(callable(SidebarItem))

    def test_instantiate(self):
        item = SidebarItem("Test Label")
        self.assertIsNotNone(item)
        self.assertEqual(item.label_text, "Test Label")


class TestSidebarSection(unittest.TestCase):
    """Test SidebarSection can be instantiated."""

    def test_import(self):
        from spotify_tui_tool.ui.sidebar import SidebarSection
        self.assertTrue(callable(SidebarSection))

    def test_instantiate(self):
        section = SidebarSection("Section Header")
        self.assertIsNotNone(section)


class _SidebarTestApp(App):
    def compose(self) -> ComposeResult:
        yield Sidebar()


class TestSidebar(unittest.TestCase):
    """Test Sidebar can be instantiated and composed."""

    def test_import(self):
        from spotify_tui_tool.ui.sidebar import Sidebar
        self.assertTrue(callable(Sidebar))

    def test_instantiate(self):
        widget = Sidebar()
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, Sidebar)

    def test_compose_returns_widgets(self):
        async def _test():
            app = _SidebarTestApp()
            async with app.run_test():
                sources = app.query_one("#sources-section")
                library = app.query_one("#library-section")
                playlists = app.query_one("#playlists-section")
                self.assertIsNotNone(sources)
                self.assertIsNotNone(library)
                self.assertIsNotNone(playlists)
        asyncio.run(_test())

    def test_sources_defined(self):
        self.assertEqual(len(Sidebar.SOURCES), 3)
        labels = [s[0] for s in Sidebar.SOURCES]
        self.assertIn("Spotify", labels)
        self.assertIn("Local", labels)
        self.assertIn("Radio", labels)

    def test_library_defined(self):
        self.assertEqual(len(Sidebar.LIBRARY), 3)
        labels = [l[0] for l in Sidebar.LIBRARY]
        self.assertIn("Liked Songs", labels)
        self.assertIn("Albums", labels)
        self.assertIn("Artists", labels)

    def test_selected_index_default(self):
        widget = Sidebar()
        self.assertEqual(widget.selected_index, 0)

    def test_current_section_default(self):
        widget = Sidebar()
        self.assertEqual(widget.current_section, "library")

    def test_get_all_items(self):
        async def _test():
            app = _SidebarTestApp()
            async with app.run_test():
                sidebar = app.query_one(Sidebar)
                items = sidebar.get_all_items()
                self.assertEqual(len(items), 7)
                self.assertIsInstance(items[0], SidebarItem)
        asyncio.run(_test())

    def test_move_selection_down(self):
        async def _test():
            app = _SidebarTestApp()
            async with app.run_test():
                sidebar = app.query_one(Sidebar)
                self.assertEqual(sidebar.selected_index, 0)
                sidebar.move_selection(1)
                self.assertEqual(sidebar.selected_index, 1)
                sidebar.move_selection(1)
                self.assertEqual(sidebar.selected_index, 2)
        asyncio.run(_test())

    def test_move_selection_up(self):
        async def _test():
            app = _SidebarTestApp()
            async with app.run_test():
                sidebar = app.query_one(Sidebar)
                sidebar.move_selection(2)
                self.assertEqual(sidebar.selected_index, 2)
                sidebar.move_selection(-1)
                self.assertEqual(sidebar.selected_index, 1)
        asyncio.run(_test())

    def test_move_selection_bounds(self):
        async def _test():
            app = _SidebarTestApp()
            async with app.run_test():
                sidebar = app.query_one(Sidebar)
                sidebar.move_selection(-5)
                self.assertEqual(sidebar.selected_index, 0)
                sidebar.move_selection(100)
                self.assertEqual(sidebar.selected_index, len(sidebar.get_all_items()) - 1)
        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
