"""
Tests for AppState — global application state management.

Strict TDD: tests written FIRST (RED).

Test runner: python -m unittest
"""
import unittest

from spotify_tui_tool.state import AppState
from spotify_tui_tool.models import TrackInfo, PlaybackStatus


class TestAppStateDefaults(unittest.TestCase):
    """AppState should have sensible defaults."""

    def test_default_view(self):
        """Default view should be 'home'."""
        state = AppState()
        self.assertEqual(state.current_view, "home")

    def test_default_sidebar(self):
        """Default sidebar section should be 'library' with index 0."""
        state = AppState()
        self.assertEqual(state.sidebar_section, "library")
        self.assertEqual(state.sidebar_index, 0)

    def test_default_playback(self):
        """Default playback state should be paused, no track."""
        state = AppState()
        self.assertFalse(state.is_playing)
        self.assertIsNone(state.current_track)
        self.assertEqual(state.volume, 0.5)
        self.assertFalse(state.shuffle)
        self.assertEqual(state.repeat_mode, "off")

    def test_default_queue(self):
        """Default queue should be empty."""
        state = AppState()
        self.assertEqual(len(state.queue), 0)

    def test_default_history(self):
        """Default history should be empty."""
        state = AppState()
        self.assertEqual(len(state.history), 0)


class TestSetView(unittest.TestCase):
    """set_view should switch to valid views."""

    def test_set_valid_view(self):
        """Setting a valid view should update current_view."""
        state = AppState()
        state.set_view("library")
        self.assertEqual(state.current_view, "library")

    def test_set_invalid_view(self):
        """Setting an invalid view should not change current_view."""
        state = AppState()
        state.set_view("invalid")
        self.assertEqual(state.current_view, "home")

    def test_all_valid_views(self):
        """All valid views should be accepted."""
        state = AppState()
        valid_views = {"home", "library", "playlists", "search", "queue", "settings", "help"}
        for view in valid_views:
            state.set_view(view)
            self.assertEqual(state.current_view, view)


class TestPlaybackState(unittest.TestCase):
    """Playback state management."""

    def test_set_playing(self):
        """set_playing should update is_playing."""
        state = AppState()
        state.set_playing(True)
        self.assertTrue(state.is_playing)

    def test_set_track(self):
        """set_track should update current_track."""
        state = AppState()
        track = TrackInfo(artist="Test", title="Song")
        state.set_track(track)
        self.assertEqual(state.current_track.artist, "Test")

    def test_set_track_none(self):
        """set_track(None) should clear current_track."""
        state = AppState()
        state.set_track(TrackInfo(artist="Test"))
        state.set_track(None)
        self.assertIsNone(state.current_track)

    def test_set_volume(self):
        """set_volume should update volume."""
        state = AppState()
        state.set_volume(0.8)
        self.assertEqual(state.volume, 0.8)

    def test_set_volume_clamp_low(self):
        """set_volume should clamp to 0.0 minimum."""
        state = AppState()
        state.set_volume(-0.5)
        self.assertEqual(state.volume, 0.0)

    def test_set_volume_clamp_high(self):
        """set_volume should clamp to 1.0 maximum."""
        state = AppState()
        state.set_volume(1.5)
        self.assertEqual(state.volume, 1.0)


class TestShuffleRepeat(unittest.TestCase):
    """Shuffle and repeat mode management."""

    def test_toggle_shuffle(self):
        """toggle_shuffle should flip shuffle state."""
        state = AppState()
        self.assertFalse(state.shuffle)
        state.toggle_shuffle()
        self.assertTrue(state.shuffle)
        state.toggle_shuffle()
        self.assertFalse(state.shuffle)

    def test_cycle_repeat(self):
        """cycle_repeat should cycle: off -> track -> all -> off."""
        state = AppState()
        self.assertEqual(state.repeat_mode, "off")
        state.cycle_repeat()
        self.assertEqual(state.repeat_mode, "track")
        state.cycle_repeat()
        self.assertEqual(state.repeat_mode, "all")
        state.cycle_repeat()
        self.assertEqual(state.repeat_mode, "off")


class TestSidebarSelection(unittest.TestCase):
    """Sidebar selection management."""

    def test_set_sidebar_selection(self):
        """set_sidebar_selection should update section and index."""
        state = AppState()
        state.set_sidebar_selection("sources", 2)
        self.assertEqual(state.sidebar_section, "sources")
        self.assertEqual(state.sidebar_index, 2)


class TestQueue(unittest.TestCase):
    """Queue management."""

    def test_add_to_queue(self):
        """add_to_queue should append track."""
        state = AppState()
        track = TrackInfo(artist="Test", title="Song")
        state.add_to_queue(track)
        self.assertEqual(len(state.queue), 1)
        self.assertEqual(state.queue[0].artist, "Test")

    def test_remove_from_queue(self):
        """remove_from_queue should remove track by index."""
        state = AppState()
        track1 = TrackInfo(artist="A", title="1")
        track2 = TrackInfo(artist="B", title="2")
        state.add_to_queue(track1)
        state.add_to_queue(track2)
        state.remove_from_queue(0)
        self.assertEqual(len(state.queue), 1)
        self.assertEqual(state.queue[0].artist, "B")

    def test_remove_from_queue_invalid_index(self):
        """remove_from_queue with invalid index should do nothing."""
        state = AppState()
        state.add_to_queue(TrackInfo())
        state.remove_from_queue(5)
        self.assertEqual(len(state.queue), 1)

    def test_clear_queue(self):
        """clear_queue should empty the queue."""
        state = AppState()
        state.add_to_queue(TrackInfo())
        state.add_to_queue(TrackInfo())
        state.clear_queue()
        self.assertEqual(len(state.queue), 0)


class TestHistory(unittest.TestCase):
    """History management."""

    def test_add_to_history(self):
        """add_to_history should add URI to front."""
        state = AppState()
        state.add_to_history("spotify:track:abc")
        self.assertEqual(len(state.history), 1)
        self.assertEqual(state.history[0], "spotify:track:abc")

    def test_add_to_history_dedup(self):
        """add_to_history should move existing URI to front."""
        state = AppState()
        state.add_to_history("spotify:track:abc")
        state.add_to_history("spotify:track:def")
        state.add_to_history("spotify:track:abc")
        self.assertEqual(len(state.history), 2)
        self.assertEqual(state.history[0], "spotify:track:abc")

    def test_add_to_history_cap(self):
        """add_to_history should cap at 50 entries."""
        state = AppState()
        for i in range(55):
            state.add_to_history(f"spotify:track:{i:04d}")
        self.assertEqual(len(state.history), 50)
        self.assertEqual(state.history[0], "spotify:track:0054")


if __name__ == "__main__":
    unittest.main()
