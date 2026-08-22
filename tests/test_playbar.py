"""Tests for Playbar component."""

import asyncio
import unittest

from textual.app import App, ComposeResult

from spotify_tui_tool.ui.playbar import Playbar
from spotify_tui_tool.models import PlaybackState, TrackInfo, PlaybackStatus


class _PlaybarTestApp(App):
    def compose(self) -> ComposeResult:
        yield Playbar()


class TestPlaybar(unittest.TestCase):
    """Test Playbar can be instantiated and composed."""

    def test_import(self):
        from spotify_tui_tool.ui.playbar import Playbar
        self.assertTrue(callable(Playbar))

    def test_instantiate(self):
        widget = Playbar()
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, Playbar)

    def test_compose_returns_widgets(self):
        async def _test():
            app = _PlaybarTestApp()
            async with app.run_test():
                track_info = app.query_one("#track-info")
                progress = app.query_one("#progress-area")
                controls = app.query_one("#controls-area")
                self.assertIsNotNone(track_info)
                self.assertIsNotNone(progress)
                self.assertIsNotNone(controls)
        asyncio.run(_test())

    def test_default_reactives(self):
        async def _test():
            app = _PlaybarTestApp()
            async with app.run_test():
                widget = app.query_one(Playbar)
                self.assertIsNone(widget.current_track)
                self.assertFalse(widget.is_playing)
                self.assertEqual(widget.volume, 0.5)
                self.assertFalse(widget.shuffle)
                self.assertEqual(widget.repeat_mode, "off")
        asyncio.run(_test())

    def test_update_track(self):
        async def _test():
            app = _PlaybarTestApp()
            async with app.run_test():
                widget = app.query_one(Playbar)
                track = TrackInfo(artist="Artist", title="Title", duration_ms=180000)
                widget.update_track(track, playing=True)
                self.assertEqual(widget.current_track, track)
                self.assertTrue(widget.is_playing)
        asyncio.run(_test())

    def test_update_track_none(self):
        async def _test():
            app = _PlaybarTestApp()
            async with app.run_test():
                widget = app.query_one(Playbar)
                widget.update_track(None, playing=False)
                self.assertIsNone(widget.current_track)
                self.assertFalse(widget.is_playing)
        asyncio.run(_test())

    def test_dynamic_markup_is_rendered_as_literal_text(self):
        async def _test():
            app = _PlaybarTestApp()
            async with app.run_test():
                widget = app.query_one(Playbar)
                widget.update_track(
                    TrackInfo(
                        artist="[red]artist[/red]",
                        title="[bold]title[/bold]",
                    ),
                    playing=True,
                )
                widget.set_status("[green]status[/green]")
                track_info = str(app.query_one("#track-info").render())
                controls = str(app.query_one("#controls-area").render())
                self.assertIn("[red]artist[/red]", track_info)
                self.assertIn("[bold]title[/bold]", track_info)
                self.assertIn("[green]status[/green]", controls)

                widget.update_track(
                    TrackInfo(
                        playback_state=PlaybackState.UNAVAILABLE,
                        playback_message="[yellow]message[/yellow]",
                    ),
                    playing=False,
                )
                self.assertIn(
                    "[yellow]message[/yellow]",
                    str(app.query_one("#track-info").render()),
                )

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
