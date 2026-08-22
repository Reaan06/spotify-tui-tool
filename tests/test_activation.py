"""Phase 3 activation contracts: identity reaches the local player only."""

import asyncio
import unittest
from unittest.mock import MagicMock

from spotify_tui_tool.exceptions import (
    PlaybackError,
    PlayerctlNotFoundError,
    SpotifyNotRunningError,
)
from spotify_tui_tool.models import BrowseRow, PlaybackFeedback, PlaybackResult
from spotify_tui_tool.spotify_client import SpotifyClient
from spotify_tui_tool.ui.rows import activation_uri


class TestActivation(unittest.TestCase):
    def test_activation_uses_stored_uri_not_display_labels(self):
        player = MagicMock()
        row = BrowseRow(
            kind="track",
            id="stable-id",
            uri="spotify:track:stable-id",
            title="A different rendered title",
            subtitle="A different artist",
            playable=True,
        )

        result = SpotifyClient(player=player).activate_row(row)

        player.open_uri.assert_called_once_with("spotify:track:stable-id")
        self.assertEqual(result.feedback, PlaybackFeedback.SUCCESS)

    def test_non_playable_row_has_no_fabricated_uri_or_command(self):
        player = MagicMock()
        row = BrowseRow(kind="album", id="album-id", title="Album")

        self.assertIsNone(activation_uri(row))
        result = SpotifyClient(player=player).activate_row(row)

        player.open_uri.assert_not_called()
        self.assertEqual(result.feedback, PlaybackFeedback.NOT_PLAYABLE)
        self.assertEqual(
            result.message,
            "This item cannot be played through the local player.",
        )

    def test_transport_failures_are_distinct_and_retryable(self):
        row = BrowseRow(
            kind="track", id="track-id", uri="spotify:track:track-id", playable=True
        )
        for error, feedback in (
            (PlayerctlNotFoundError(), PlaybackFeedback.UNAVAILABLE),
            (SpotifyNotRunningError(), PlaybackFeedback.UNAVAILABLE),
            (PlaybackError("permission denied"), PlaybackFeedback.FAILED),
        ):
            player = MagicMock()
            player.open_uri.side_effect = error
            result = SpotifyClient(player=player).activate_row(row)
            self.assertEqual(result.feedback, feedback)
            self.assertTrue(result.retryable)
            self.assertNotEqual(result.message, "Playback started via the local player.")


class TestActivationPilot(unittest.TestCase):
    def test_enter_activates_the_selected_stored_row(self):
        async def scenario():
            from textual.coordinate import Coordinate
            from spotify_tui_tool.app import SpotifyTuiApp
            from spotify_tui_tool.ui.views.search import SearchView

            row = BrowseRow(
                kind="track",
                id="track-id",
                uri="spotify:track:stored-uri",
                title="Rendered title",
                playable=True,
            )
            app = SpotifyTuiApp()
            app._client.activate_row = MagicMock(
                return_value=PlaybackResult(PlaybackFeedback.SUCCESS, "ok")
            )
            async with app.run_test(size=(100, 28)) as pilot:
                await app._switch_view("search", remember=False)
                view = app.query_one(SearchView)
                view.set_authenticated(True)
                view.set_rows([row])
                table = app.query_one("#search-results")
                table.focus()
                table.cursor_coordinate = Coordinate(0, 0)
                await pilot.pause()
                await pilot.press("enter")
                await pilot.pause()
                app._client.activate_row.assert_called_once_with(row)

        asyncio.run(scenario())

    def test_double_click_uses_the_same_activation_path(self):
        async def scenario():
            from textual.coordinate import Coordinate
            from spotify_tui_tool.app import SpotifyTuiApp
            from spotify_tui_tool.ui.views.search import SearchView

            row = BrowseRow(
                kind="track", id="track-id", uri="spotify:track:stored-uri", playable=True
            )
            app = SpotifyTuiApp()
            app._client.activate_row = MagicMock(
                return_value=PlaybackResult(
                    PlaybackFeedback.FAILED,
                    "Playback failed: command failed. Try again.",
                    retryable=True,
                )
            )
            async with app.run_test(size=(100, 28)) as pilot:
                app._poll_timer.stop()
                await app._switch_view("search", remember=False)
                view = app.query_one(SearchView)
                view.set_authenticated(True)
                view.set_rows([row])
                table = app.query_one("#search-results")
                table.cursor_coordinate = Coordinate(-1, -1)
                await pilot.click("#search-results", offset=(2, 1))
                await pilot.click("#search-results", offset=(2, 1))
                await pilot.pause()
                app._client.activate_row.assert_called_once_with(row)
                self.assertIn(
                    "Try again", str(app.query_one("#controls-area").render())
                )

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
