"""Unit contracts for the Phase 1 interaction shell."""

import unittest

from spotify_tui_tool.app import SpotifyTuiApp
from spotify_tui_tool.state import AppState
from spotify_tui_tool.ui.content import ContentArea
from spotify_tui_tool.ui.layout import LayoutManager
from spotify_tui_tool.ui.sidebar import SidebarItem
from spotify_tui_tool.ui.views.help import HelpView


class TestShellLayoutContract(unittest.TestCase):
    def test_layout_records_wide_and_compact_contract(self):
        self.assertEqual(LayoutManager.COMPACT_BREAKPOINT, 96)
        self.assertEqual(LayoutManager.WIDE_SIDEBAR_PERCENT, 22)
        self.assertEqual(LayoutManager.COMPACT_SIDEBAR_COLUMNS, 16)
        self.assertEqual(LayoutManager.WIDE_PLAYBAR_ROWS, 5)
        self.assertEqual(LayoutManager.COMPACT_PLAYBAR_ROWS, 4)

    def test_state_tracks_focus_and_transient_history(self):
        state = AppState()

        state.set_focus_region("content")
        state.push_transient("help", "library")

        self.assertEqual(state.focus_region, "content")
        self.assertEqual(state.transient_view, "help")
        self.assertEqual(state.pop_transient(), "library")
        self.assertIsNone(state.transient_view)

    def test_invalid_focus_does_not_destroy_deterministic_state(self):
        state = AppState()
        state.set_focus_region("playbar")
        state.set_focus_region("unknown")

        self.assertEqual(state.focus_region, "playbar")


class TestShellInteractionContract(unittest.TestCase):
    def test_app_exposes_every_shell_binding(self):
        keys = {binding.key for binding in SpotifyTuiApp.BINDINGS}

        self.assertTrue(
            {
                "space", "n", "p", "equal", "plus", "minus",
                "less_than", "greater_than", "slash", "enter",
                "j", "k", "down", "up", "h", "l", "left", "right",
                "escape", "q", "question",
            } <= keys
        )

    def test_sidebar_item_keeps_view_and_selection_metadata(self):
        item = SidebarItem(
            "Liked Songs",
            id="lib-liked",
            section="library",
            view="library",
        )

        item.set_selected(True)

        self.assertEqual(item.item_id, "lib-liked")
        self.assertEqual(item.view, "library")
        self.assertIn("Liked Songs", str(item.render()))
        self.assertIn("▸", str(item.render()))

    def test_help_lists_supported_bindings_without_unsupported_claims(self):
        keys = {key for key, _action, _category in HelpView.KEYBINDINGS}
        help_text = " ".join(
            f"{key} {action} {category}"
            for key, action, category in HelpView.KEYBINDINGS
        ).lower()

        self.assertTrue({"Space", "n", "p", "+", "-", "<", ">", "?", "Esc", "q"} <= keys)
        self.assertNotIn("queue", help_text)
        self.assertNotIn("device", help_text)
        self.assertNotIn("lyrics", help_text)
        self.assertNotIn("stream", help_text)
        self.assertNotIn("like/unlike", help_text)

    def test_content_exposes_scroll_and_activation_hooks(self):
        content = ContentArea()

        self.assertEqual(content.scroll_region("down"), 1)
        self.assertEqual(content.scroll_region("up"), -1)
        self.assertEqual(content.activate_focused(), "content")


if __name__ == "__main__":
    unittest.main()
