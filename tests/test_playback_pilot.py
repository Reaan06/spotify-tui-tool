"""Offline playback pilots for stale context and truthful controls."""

import asyncio
import unittest
from unittest.mock import MagicMock

from spotify_tui_tool.exceptions import SpotifyNotRunningError
from spotify_tui_tool.models import PlaybackState, PlaybackStatus, TrackInfo
from spotify_tui_tool.spotify_client import SpotifyClient
from spotify_tui_tool.ui.playbar import Playbar


META = "Artist|Title|Album|180000000|0.5|spotify:track:track-id"


class TestPlaybackPilot(unittest.TestCase):
    def test_poll_failure_keeps_last_track_and_marks_it_stale(self):
        player = MagicMock()
        player.run.side_effect = lambda command, *args: {
            "metadata": META,
            "position": "12",
            "status": "Playing",
        }[command]
        client = SpotifyClient(player=player)
        first = client.poll()

        player.run.side_effect = SpotifyNotRunningError()
        first_miss = client.poll()
        stale = client.poll()

        self.assertEqual(first.title, "Title")
        self.assertEqual(first_miss.title, "Title")
        self.assertEqual(first_miss.playback_state, PlaybackState.FRESH)
        self.assertEqual(stale.title, "Title")
        self.assertEqual(stale.playback_state, PlaybackState.STALE)
        self.assertEqual(client.get_current_track().playback_state, PlaybackState.STALE)

    def test_no_player_and_stopped_player_are_distinct(self):
        unavailable_player = MagicMock()
        unavailable_player.run.side_effect = SpotifyNotRunningError()
        unavailable = SpotifyClient(player=unavailable_player).poll()

        stopped_player = MagicMock()
        stopped_player.run.side_effect = lambda command, *args: {
            "metadata": "||||",
            "position": "",
            "status": "Stopped",
        }[command]
        stopped = SpotifyClient(player=stopped_player).poll()

        self.assertEqual(unavailable.playback_state, PlaybackState.UNAVAILABLE)
        self.assertEqual(stopped.playback_state, PlaybackState.STOPPED)

    def test_stopped_player_stays_stopped_for_one_missed_poll(self):
        player = MagicMock()
        player.run.side_effect = lambda command, *args: {
            "metadata": "||||",
            "position": "",
            "status": "Stopped",
        }[command]
        client = SpotifyClient(player=player)
        stopped = client.poll()

        player.run.side_effect = SpotifyNotRunningError()
        first_miss = client.poll()
        second_miss = client.poll()

        self.assertEqual(stopped.playback_state, PlaybackState.STOPPED)
        self.assertEqual(first_miss.playback_state, PlaybackState.STOPPED)
        self.assertEqual(second_miss.playback_state, PlaybackState.STALE)

    def test_playbar_keeps_context_and_only_shows_supported_controls(self):
        async def scenario():
            from textual.app import App, ComposeResult

            class PilotApp(App):
                def compose(self) -> ComposeResult:
                    yield Playbar()

            async with PilotApp().run_test() as pilot:
                playbar = pilot.app.query_one(Playbar)
                playbar.update_track(
                    TrackInfo(
                        artist="Artist",
                        title="Title",
                        playback_state=PlaybackState.STALE,
                        status=PlaybackStatus.PLAYING,
                    ),
                    playing=True,
                )
                rendered = str(playbar.query_one("#controls-area").render())
                self.assertIn("Vol:", rendered)
                self.assertNotIn("shuffle", rendered.lower())
                self.assertNotIn("repeat", rendered.lower())

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
