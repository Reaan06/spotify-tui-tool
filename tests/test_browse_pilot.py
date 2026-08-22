"""Offline Textual pilots for Phase 2 browse states and row refreshes."""

import asyncio
from threading import Event, Lock
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.app import SpotifyTuiApp
from spotify_tui_tool.auth import AuthManager, AuthState
from spotify_tui_tool.models import BrowseRow
from spotify_tui_tool.ui.views.library import LibraryView
from spotify_tui_tool.ui.views.login import LoginView
from spotify_tui_tool.ui.views.search import SearchView


class _LibraryPilotApp(App):
    def compose(self) -> ComposeResult:
        yield LibraryView()


class _LoginPilotApp(App):
    def compose(self) -> ComposeResult:
        yield LoginView()


class _SearchPilotApp(App):
    def compose(self) -> ComposeResult:
        yield SearchView()


class TestBrowsePilot(unittest.TestCase):
    def test_login_pilot_shows_explicit_unauthenticated_copy(self):
        async def _test():
            app = _LoginPilotApp()
            async with app.run_test():
                status = app.query_one("#login-status")
                self.assertIn("Not signed in", str(status.render()))
                self.assertIn("Press Enter", str(status.render()))

        asyncio.run(_test())

    def test_library_pilot_renders_loading_success_and_empty_states(self):
        async def _test():
            app = _LibraryPilotApp()
            async with app.run_test(size=(80, 24)):
                view = app.query_one(LibraryView)
                view.set_authenticated(True)
                view.set_loading()
                self.assertIn("Loading", str(app.query_one("#library-state").render()))

                view.set_rows([
                    BrowseRow(
                        "track",
                        "t1",
                        "spotify:track:t1",
                        "Song",
                        "Artist",
                        True,
                    )
                ])
                self.assertEqual(app.query_one("#liked-songs-table").row_count, 1)
                self.assertEqual(view.row_for_key("track:t1").uri, "spotify:track:t1")

                view.set_rows([])
                self.assertIn("No liked songs", str(app.query_one("#library-state").render()))

        asyncio.run(_test())

    def test_failed_refresh_keeps_visible_rows_and_marks_stale(self):
        async def _test():
            app = _LibraryPilotApp()
            async with app.run_test(size=(80, 24)):
                view = app.query_one(LibraryView)
                view.set_authenticated(True)
                row = BrowseRow("track", "t1", "spotify:track:t1", "Song", "Artist", True)
                view.set_rows([row])
                view.set_error("Network unavailable")

                self.assertEqual(app.query_one("#liked-songs-table").row_count, 1)
                self.assertEqual(view.surface_state.value, "stale")
                state_text = str(app.query_one("#library-state").render())
                self.assertIn("stale", state_text.lower())
                self.assertIn("retry", state_text.lower())

        asyncio.run(_test())

    def test_search_pilot_keeps_duplicate_identity_after_refresh(self):
        async def _test():
            app = _SearchPilotApp()
            async with app.run_test(size=(100, 28)):
                view = app.query_one(SearchView)
                view.set_authenticated(True)
                rows = [
                    BrowseRow("track", "one", "spotify:track:one", "Same", "Artist", True),
                    BrowseRow("track", "two", "spotify:track:two", "Same", "Artist", True),
                ]
                view.set_rows(rows)
                view.set_rows(list(reversed(rows)))

                self.assertEqual(view.row_for_key("track:one").uri, "spotify:track:one")
                self.assertEqual(view.row_for_key("track:two").uri, "spotify:track:two")

        asyncio.run(_test())

    def test_browse_pilot_discards_late_rows_from_older_request(self):
        class BlockingWebAPI:
            def __init__(self):
                self.calls = 0
                self.calls_lock = Lock()
                self.first_started = Event()
                self.first_finished = Event()
                self.second_finished = Event()
                self.release_first = Event()

            def get_liked_songs(self, *, limit, offset):
                with self.calls_lock:
                    self.calls += 1
                    call_number = self.calls
                if call_number == 1:
                    self.first_started.set()
                    self.release_first.wait()
                    self.first_finished.set()
                    return [{
                        "track": {
                            "id": "old",
                            "uri": "spotify:track:old",
                            "name": "Old row",
                            "artists": [{"name": "Artist"}],
                        }
                    }]

                self.second_finished.set()
                return [{
                    "track": {
                        "id": "new",
                        "uri": "spotify:track:new",
                        "name": "New row",
                        "artists": [{"name": "Artist"}],
                    }
                }]

        async def _test():
            api = BlockingWebAPI()
            auth = AuthManager(token_loader=lambda: None, api_factory=lambda _: api)
            app = SpotifyTuiApp(web_api=api, auth_manager=auth)
            try:
                async with app.run_test(size=(100, 28)) as pilot:
                    app._is_logged_in = True
                    app._state.set_auth_state(AuthState.AUTHENTICATED.value)

                    await pilot.press("2")
                    self.assertTrue(await asyncio.to_thread(api.first_started.wait, 2))

                    await pilot.press("right")
                    self.assertEqual(app._state.focus_region, "playbar")

                    await pilot.press("r")
                    self.assertTrue(await asyncio.to_thread(api.second_finished.wait, 2))

                    view = app.query_one(LibraryView)
                    for _ in range(100):
                        if view.row_for_key("track:new") is not None:
                            break
                        await pilot.pause()
                    else:
                        self.fail("newer browse rows were not rendered")
                    self.assertIsNone(view.row_for_key("track:old"))

                    api.release_first.set()
                    self.assertTrue(await asyncio.to_thread(api.first_finished.wait, 2))
                    for _ in range(10):
                        await pilot.pause()
                    self.assertIsNotNone(view.row_for_key("track:new"))
                    self.assertIsNone(view.row_for_key("track:old"))
            finally:
                api.release_first.set()

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
