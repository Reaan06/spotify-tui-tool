"""Tests for LoginView component."""

import asyncio
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.views.login import LoginView


class _LoginTestApp(App):
    def compose(self) -> ComposeResult:
        yield LoginView()


class TestLoginView(unittest.TestCase):
    """Test LoginView can be instantiated and composed."""

    def test_import(self):
        from spotify_tui_tool.ui.views.login import LoginView
        self.assertTrue(callable(LoginView))

    def test_instantiate(self):
        widget = LoginView()
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, LoginView)

    def test_compose_returns_widgets(self):
        async def _test():
            app = _LoginTestApp()
            async with app.run_test():
                children = list(app.query(LoginView).first().children)
                self.assertGreater(len(children), 0)
        asyncio.run(_test())

    def test_login_button_exists(self):
        async def _test():
            app = _LoginTestApp()
            async with app.run_test():
                button = app.query_one("#login-button")
                self.assertIsNotNone(button)
                self.assertEqual(button.label, "Login with Spotify")
        asyncio.run(_test())

    def test_default_not_logged_in(self):
        async def _test():
            app = _LoginTestApp()
            async with app.run_test():
                view = app.query_one(LoginView)
                self.assertFalse(view.is_logged_in)
                self.assertEqual(view.username, "")
        asyncio.run(_test())

    def test_update_login_status_logged_in(self):
        async def _test():
            app = _LoginTestApp()
            async with app.run_test():
                view = app.query_one(LoginView)
                view.update_login_status(True, "test_user")
                self.assertTrue(view.is_logged_in)
                self.assertEqual(view.username, "test_user")
        asyncio.run(_test())

    def test_update_login_status_not_logged_in(self):
        async def _test():
            app = _LoginTestApp()
            async with app.run_test():
                view = app.query_one(LoginView)
                view.update_login_status(True, "test_user")
                view.update_login_status(False)
                self.assertFalse(view.is_logged_in)
                self.assertEqual(view.username, "")
        asyncio.run(_test())

    def test_login_requested_message(self):
        async def _test():
            app = _LoginTestApp()
            async with app.run_test():
                view = app.query_one(LoginView)
                button = app.query_one("#login-button")
                messages = []
                view.on("LoginView.LoginRequested", lambda msg: messages.append(msg))
                button.press()
                self.assertEqual(len(messages), 1)
        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
