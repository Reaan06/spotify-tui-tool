"""
Tests for the main TUI app — import, instantiation, and key action wiring.

Strict TDD: tests written FIRST (RED).  We test that:
1. The app can be imported
2. The app class exists and is a Textual App
3. Key actions are callable (play_pause, next, previous, volume)
4. Search submission validates URIs before calling playerctl

Test runner: python3 -m unittest
"""
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from spotify_tui_tool.app import SpotifyTuiApp, main
from spotify_tui_tool.exceptions import InvalidURIError, PlaybackError, SpotifyNotRunningError
from spotify_tui_tool.models import BrowseRow, PlaybackState, PlaybackStatus, TrackInfo
from spotify_tui_tool.ui.rows import BrowseRowActivated


class TestAppImport(unittest.TestCase):
    """Verify the app module can be imported and main() exists."""

    def test_import_app_class(self):
        """SpotifyTuiApp should be importable."""
        from spotify_tui_tool.app import SpotifyTuiApp
        self.assertTrue(callable(SpotifyTuiApp))

    def test_import_main(self):
        """main() function should be importable."""
        from spotify_tui_tool.app import main
        self.assertTrue(callable(main))


class TestAppInstantiation(unittest.TestCase):
    """Verify the app can be created with default parameters."""

    def test_create_app(self):
        """SpotifyTuiApp() should create an app instance."""
        app = SpotifyTuiApp()
        self.assertIsNotNone(app)
        self.assertIsInstance(app, SpotifyTuiApp)

    def test_custom_player_name(self):
        """A custom player_name should be passed to PlayerController."""
        app = SpotifyTuiApp(player_name="spotifyd")
        self.assertEqual(app._client._player.player_name, "spotifyd")


class TestAppActions(unittest.TestCase):
    """Test that app actions are wired correctly."""

    def setUp(self):
        self.app = SpotifyTuiApp()

    @patch.object(SpotifyTuiApp, 'query_one')
    def test_play_pause_action(self, mock_query):
        """action_play_pause should call client.play_pause."""
        mock_status = MagicMock()
        mock_query.return_value = mock_status
        self.app._client = MagicMock()
        self.app.action_play_pause()
        self.app._client.play_pause.assert_called_once()

    @patch.object(SpotifyTuiApp, 'query_one')
    def test_next_track_action(self, mock_query):
        """action_next_track should call client.next_track."""
        mock_status = MagicMock()
        mock_query.return_value = mock_status
        self.app._client = MagicMock()
        self.app.action_next_track()
        self.app._client.next_track.assert_called_once()

    @patch.object(SpotifyTuiApp, 'query_one')
    def test_previous_track_action(self, mock_query):
        """action_previous_track should call client.previous_track."""
        mock_status = MagicMock()
        mock_query.return_value = mock_status
        self.app._client = MagicMock()
        self.app.action_previous_track()
        self.app._client.previous_track.assert_called_once()

    @patch.object(SpotifyTuiApp, 'query_one')
    def test_volume_up_action(self, mock_query):
        """action_volume_up should increase volume by 0.1."""
        mock_status = MagicMock()
        mock_query.return_value = mock_status
        self.app._client = MagicMock()
        self.app._client.get_volume.return_value = 0.5
        self.app.action_volume_up()
        self.app._client.set_volume.assert_called_once_with(0.6)

    @patch.object(SpotifyTuiApp, 'query_one')
    def test_volume_down_action(self, mock_query):
        """action_volume_down should decrease volume by 0.1."""
        mock_status = MagicMock()
        mock_query.return_value = mock_status
        self.app._client = MagicMock()
        self.app._client.get_volume.return_value = 0.5
        self.app.action_volume_down()
        self.app._client.set_volume.assert_called_once_with(0.4)

    @patch.object(SpotifyTuiApp, '_show_status')
    def test_play_pause_spotify_not_running(self, mock_status):
        """action_play_pause should show error when Spotify is not running."""
        self.app._client = MagicMock()
        self.app._client.play_pause.side_effect = SpotifyNotRunningError()
        self.app.action_play_pause()
        mock_status.assert_called_with(
            "Playback unavailable: no Spotify MPRIS player is active.",
            is_error=True,
        )


class TestSearchSubmission(unittest.TestCase):
    """Test URI search submission flow."""

    def setUp(self):
        self.app = SpotifyTuiApp()
        self.app._search_service = MagicMock()

    @patch.object(SpotifyTuiApp, 'query_one')
    def test_valid_uri_opens(self, mock_query):
        """A playable stable row should open its stored URI through playerctl."""
        uri = "spotify:track:6rqhFgbbKwnb9MLmUQDhG6"
        row = BrowseRow(
            kind="track",
            id="6rqhFgbbKwnb9MLmUQDhG6",
            uri=uri,
            title="Rendered title",
            subtitle="Rendered artist",
            playable=True,
        )
        self.app._client.player.open_uri = MagicMock()
        self.app.on_browse_row_activated(BrowseRowActivated(row))
        self.app._client.player.open_uri.assert_called_once_with(uri)

    def test_empty_uri_no_op(self):
        """An empty URI should not call open_uri."""
        event = MagicMock()
        event.value = "   "
        self.app.on_search_submitted(event)
        self.app._search_service.open_uri.assert_not_called()

    @patch.object(SpotifyTuiApp, 'query_one')
    def test_invalid_uri_shows_error(self, mock_query):
        """An invalid URI should show an error message."""
        mock_status = MagicMock()
        mock_query.return_value = mock_status
        event = MagicMock()
        event.value = "not-a-uri"
        self.app._search_service.open_uri.side_effect = InvalidURIError("not-a-uri")
        # Should not raise
        self.app.on_search_submitted(event)


class TestAppBoundaries(unittest.TestCase):
    def test_status_text_is_escaped_before_markup_rendering(self):
        app = SpotifyTuiApp()
        playbar = MagicMock()
        with patch.object(app, "query_one", return_value=playbar):
            app._show_status("[bold]untrusted[/bold]", is_error=True)
        playbar.set_status.assert_called_once_with(
            "[bold]untrusted[/bold]", is_error=True
        )

    def test_unmounted_content_lookup_is_safe(self):
        app = SpotifyTuiApp()
        app._is_logged_in = True
        app._load_web_api_data()

    def test_fresh_playback_clears_previous_playbar_status(self):
        async def _test():
            app = SpotifyTuiApp()
            async with app.run_test():
                playbar = app.query_one("#playbar")
                playbar.set_status("Playback unavailable")
                app._poll_metadata(TrackInfo(
                    artist="Artist",
                    title="Title",
                    status=PlaybackStatus.PLAYING,
                    playback_state=PlaybackState.FRESH,
                ))
                self.assertEqual(playbar.status_message, "")

        import asyncio
        asyncio.run(_test())

    def test_transient_search_only_closes_when_input_is_empty(self):
        app = SpotifyTuiApp()
        app._state.push_transient("search", "home")
        content = MagicMock(current_view="search")
        search_input = MagicMock(value="q")
        with patch.object(app, "query_one", side_effect=[content, search_input]), \
             patch.object(app, "exit") as exit_app:
            import asyncio
            asyncio.run(app.action_quit_or_back())
        self.assertEqual(app._state.transient_view, "search")
        exit_app.assert_not_called()
        search_input.value = ""
        app.action_back = AsyncMock()
        with patch.object(app, "query_one", side_effect=[content, search_input]):
            asyncio.run(app.action_quit_or_back())
        app.action_back.assert_awaited_once_with()


if __name__ == "__main__":
    unittest.main()
