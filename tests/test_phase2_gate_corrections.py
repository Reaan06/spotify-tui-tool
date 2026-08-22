"""Regression tests for the bounded Phase 2 gatekeeper corrections."""

import asyncio
import importlib.util
import unittest
from unittest.mock import MagicMock, patch

from textual.app import App, ComposeResult

from spotify_tui_tool.app import SpotifyTuiApp
from spotify_tui_tool.spotify_client import SpotifyClient
from spotify_tui_tool.ui.content import ContentArea
from spotify_tui_tool.web_api import SpotifyWebAPI


class TestQueueCapabilityBoundary(unittest.TestCase):
    """Queue inspection must not be reachable from the Phase 2 shell."""

    def test_queue_route_is_not_registered_or_bound(self):
        binding_keys = {binding.key for binding in SpotifyTuiApp.BINDINGS}

        self.assertNotIn("5", binding_keys)
        self.assertNotIn("queue", ContentArea.VIEW_WIDGETS)
        self.assertFalse(hasattr(SpotifyTuiApp, "action_view_queue"))

    def test_queue_view_module_is_not_available(self):
        module = importlib.util.find_spec("spotify_tui_tool.ui.views.queue")

        self.assertIsNone(module)

    def test_unsupported_queue_switch_is_rejected(self):
        class _ContentTestApp(App):
            def compose(self) -> ComposeResult:
                yield ContentArea()

        async def _test():
            app = _ContentTestApp()
            async with app.run_test():
                content = app.query_one(ContentArea)
                await content.switch_view("queue")
                self.assertEqual(content.current_view, "home")

        asyncio.run(_test())


class TestReadOnlyWebAPIBoundary(unittest.TestCase):
    """The Web API client must expose browsing/authentication only."""

    def test_playback_and_mutation_methods_are_not_exposed(self):
        api = SpotifyWebAPI()
        unsupported = {
            "get_playback_state",
            "get_devices",
            "transfer_playback",
            "start_playback",
            "pause_playback",
            "next_track",
            "previous_track",
            "set_volume",
            "seek",
            "like_track",
            "unlike_track",
            "_put",
            "_post",
            "_delete",
        }

        self.assertEqual(
            {name for name in unsupported if hasattr(api, name)},
            set(),
        )

    @patch.object(SpotifyWebAPI, "_get")
    def test_read_only_browse_surface_remains_available(self, mock_get):
        mock_get.return_value = {"id": "user-1", "display_name": "Offline User"}

        user = SpotifyWebAPI().get_current_user()

        mock_get.assert_called_once_with("/me")
        self.assertEqual(user["id"], "user-1")


class TestPlayerctlPlaybackAuthority(unittest.TestCase):
    """Authenticated browsing must never redirect playback through Web API."""

    def test_authenticated_client_uses_playerctl_for_every_playback_operation(self):
        player = MagicMock()
        player.get_volume.return_value = 0.25
        api = MagicMock()
        client = SpotifyClient(player=player, web_api=api)

        client.play_pause()
        client.next_track()
        client.previous_track()
        volume = client.get_volume()
        client.set_volume(0.4)
        client.seek(123)

        player.play_pause.assert_called_once_with()
        player.next.assert_called_once_with()
        player.previous.assert_called_once_with()
        player.get_volume.assert_called_once_with()
        player.set_volume.assert_called_once_with(0.4)
        player.run.assert_called_once_with("position", "+0.123")
        self.assertEqual(volume, 0.25)
        self.assertEqual(api.mock_calls, [])

    def test_authenticated_client_preserves_player_errors(self):
        player = MagicMock()
        player.play_pause.side_effect = RuntimeError("player unavailable")
        api = MagicMock()
        client = SpotifyClient(player=player, web_api=api)

        with self.assertRaisesRegex(RuntimeError, "player unavailable"):
            client.play_pause()

        self.assertEqual(api.mock_calls, [])


if __name__ == "__main__":
    unittest.main()
