"""Strict-TDD tests for the Phase 2 authentication and browse contracts."""

import unittest
from unittest.mock import Mock

from spotify_tui_tool.app import BrowseRequest, SpotifyTuiApp
from spotify_tui_tool.auth import AuthManager, AuthResult, AuthState, auth_message
from spotify_tui_tool.models import BrowseRow
from spotify_tui_tool.state import AppState, BrowseStatus
from spotify_tui_tool.ui.views.search import SearchView
from spotify_tui_tool.ui.states import browse_state_text


class TestAuthenticationLifecycle(unittest.TestCase):
    def test_username_falls_back_to_id_when_display_name_is_empty(self):
        result = AuthResult(
            AuthState.AUTHENTICATED,
            user={"id": "ada", "display_name": None},
        )
        self.assertEqual(result.message, "Signed in as ada.")

    def test_auth_copy_is_explicit_for_each_lifecycle_state(self):
        self.assertEqual(
            auth_message(AuthState.UNAUTHENTICATED),
            "Not signed in. Press Enter to log in.",
        )
        self.assertEqual(
            auth_message(AuthState.RESTORING),
            "Restoring Spotify session…",
        )
        self.assertEqual(
            auth_message(AuthState.AUTHENTICATING),
            "Waiting for Spotify login…",
        )
        self.assertEqual(
            auth_message(AuthState.AUTHENTICATED, "Ada"),
            "Signed in as Ada.",
        )
        self.assertEqual(
            auth_message(AuthState.INVALID_EXPIRED),
            "Spotify session is invalid or expired. Press Enter to log in or r to retry.",
        )

    def test_restore_validates_persisted_credentials_before_success(self):
        api = Mock()
        api.get_current_user.return_value = {"id": "ada", "display_name": "Ada"}
        manager = AuthManager(
            token_loader=lambda: {"access_token": "persisted"},
            api_factory=lambda access_token: api,
        )

        result = manager.restore()

        self.assertEqual(result.state, AuthState.AUTHENTICATED)
        self.assertEqual(result.user["id"], "ada")
        api.get_current_user.assert_called_once_with()

    def test_restore_rejection_is_actionable_invalid_state(self):
        api = Mock()
        api.get_current_user.side_effect = RuntimeError("expired")
        manager = AuthManager(
            token_loader=lambda: {"access_token": "rejected"},
            api_factory=lambda access_token: api,
        )

        result = manager.restore()

        self.assertEqual(result.state, AuthState.INVALID_EXPIRED)
        self.assertIn("invalid or expired", result.message)

    def test_missing_credentials_are_not_treated_as_authenticated(self):
        api_factory = Mock()
        manager = AuthManager(token_loader=lambda: None, api_factory=api_factory)

        result = manager.restore()

        self.assertEqual(result.state, AuthState.UNAUTHENTICATED)
        api_factory.assert_not_called()


class TestBrowseStateTransitions(unittest.TestCase):
    def test_browse_error_markup_is_literal(self):
        text = browse_state_text(
            BrowseStatus.ERROR,
            surface="library",
            message="[red]untrusted[/red]",
        )
        self.assertIn(r"\[red]untrusted\[/red]", text)

    def test_loading_success_and_empty_are_distinct(self):
        state = AppState()
        generation = state.begin_browse("library", "library-view")
        self.assertEqual(state.browse_status("library"), BrowseStatus.LOADING)

        state.accept_browse_result(
            "library",
            generation,
            "library-view",
            [BrowseRow("track", "t1", "spotify:track:t1", "Song", "Artist", True)],
        )
        self.assertEqual(state.browse_status("library"), BrowseStatus.SUCCESS)
        self.assertEqual(len(state.browse_rows("library")), 1)

        empty_generation = state.begin_browse("library", "library-view")
        state.accept_browse_result("library", empty_generation, "library-view", [])
        self.assertEqual(state.browse_status("library"), BrowseStatus.EMPTY)

    def test_failed_refresh_retains_rows_as_stale_and_retryable(self):
        state = AppState()
        row = BrowseRow("track", "t1", "spotify:track:t1", "Song", "Artist", True)
        generation = state.begin_browse("library", "library-view")
        state.accept_browse_result("library", generation, "library-view", [row])

        refresh_generation = state.begin_browse("library", "library-view")
        state.reject_browse_result(
            "library", refresh_generation, "library-view", "Spotify is offline"
        )

        self.assertEqual(state.browse_status("library"), BrowseStatus.STALE)
        self.assertEqual(state.browse_rows("library"), [row])
        self.assertTrue(state.browse_retryable("library"))
        self.assertIn("offline", state.browse_message("library"))

    def test_late_generation_or_view_result_is_discarded(self):
        state = AppState()
        first = state.begin_browse("search", "search-view-1")
        second = state.begin_browse("search", "search-view-2")
        row = BrowseRow("track", "new", "spotify:track:new", "New", "Artist", True)

        self.assertFalse(
            state.accept_browse_result("search", first, "search-view-1", [row])
        )
        self.assertFalse(
            state.accept_browse_result("search", second, "search-view-1", [row])
        )
        self.assertTrue(
            state.accept_browse_result("search", second, "search-view-2", [row])
        )

    def test_worker_result_carries_generation_and_view_identity(self):
        api = Mock()
        api.get_liked_songs.return_value = [{
            "track": {
                "id": "t1",
                "uri": "spotify:track:t1",
                "name": "Song",
                "artists": [{"name": "Artist"}],
            }
        }]
        app = SpotifyTuiApp(web_api=api)
        request = BrowseRequest("library", 4, "library:2")

        result = app._browse_worker(request)

        self.assertEqual(result.request.generation, 4)
        self.assertEqual(result.request.view_id, "library:2")
        self.assertEqual(result.rows[0].uri, "spotify:track:t1")
        api.get_liked_songs.assert_called_once_with(limit=50, offset=0)

    def test_browse_result_does_not_start_web_api_playback(self):
        app = SpotifyTuiApp()
        app._web_api = Mock()

        app.on_search_result_selected(SearchView.ResultSelected("spotify:track:t1"))

        app._web_api.start_playback.assert_not_called()


if __name__ == "__main__":
    unittest.main()
