"""
Tests for Config — configuration management.

Strict TDD: tests written FIRST (RED).

Test runner: python -m unittest
"""
import unittest
import tempfile
from pathlib import Path

from spotify_tui_tool.config import Config


class TestConfigDefaults(unittest.TestCase):
    """Config should have sensible defaults."""

    def test_default_sidebar_width(self):
        """Default sidebar width should be 20%."""
        config = Config()
        self.assertEqual(config.sidebar_width_percent, 20)

    def test_default_playbar_height(self):
        """Default playbar height should be 6 rows."""
        config = Config()
        self.assertEqual(config.playbar_height_rows, 6)

    def test_default_sidebar_position(self):
        """Default sidebar position should be 'left'."""
        config = Config()
        self.assertEqual(config.sidebar_position, "left")

    def test_default_tick_rate(self):
        """Default tick rate should be 1000ms."""
        config = Config()
        self.assertEqual(config.tick_rate_ms, 1000)

    def test_default_volume_increment(self):
        """Default volume increment should be 10."""
        config = Config()
        self.assertEqual(config.volume_increment, 10)

    def test_default_seek_milliseconds(self):
        """Default seek should be 5000ms."""
        config = Config()
        self.assertEqual(config.seek_milliseconds, 5000)

    def test_default_theme(self):
        """Default theme should be 'dark'."""
        config = Config()
        self.assertEqual(config.theme, "dark")

    def test_default_startup_view(self):
        """Default startup view should be 'home'."""
        config = Config()
        self.assertEqual(config.startup_view, "home")


class TestConfigFromDict(unittest.TestCase):
    """Config._from_dict should create config from dictionary."""

    def test_from_dict_all_fields(self):
        """All fields should be populated from dict."""
        data = {
            "sidebar_width_percent": 25,
            "playbar_height_rows": 8,
            "sidebar_position": "right",
            "tick_rate_ms": 500,
            "volume_increment": 5,
            "seek_milliseconds": 10000,
            "theme": "light",
            "startup_view": "library",
        }
        config = Config._from_dict(data)
        self.assertEqual(config.sidebar_width_percent, 25)
        self.assertEqual(config.playbar_height_rows, 8)
        self.assertEqual(config.sidebar_position, "right")
        self.assertEqual(config.tick_rate_ms, 500)
        self.assertEqual(config.volume_increment, 5)
        self.assertEqual(config.seek_milliseconds, 10000)
        self.assertEqual(config.theme, "light")
        self.assertEqual(config.startup_view, "library")

    def test_from_dict_partial(self):
        """Partial dict should use defaults for missing fields."""
        data = {"theme": "light"}
        config = Config._from_dict(data)
        self.assertEqual(config.theme, "light")
        self.assertEqual(config.sidebar_width_percent, 20)  # default

    def test_from_dict_empty(self):
        """Empty dict should return default config."""
        config = Config._from_dict({})
        self.assertEqual(config.sidebar_width_percent, 20)
        self.assertEqual(config.theme, "dark")


class TestConfigToDict(unittest.TestCase):
    """Config._to_dict should convert config to dictionary."""

    def test_to_dict(self):
        """to_dict should return all fields."""
        config = Config(sidebar_width_percent=25, theme="light")
        data = config._to_dict()
        self.assertEqual(data["sidebar_width_percent"], 25)
        self.assertEqual(data["theme"], "light")
        self.assertEqual(data["sidebar_position"], "left")


class TestConfigSaveLoad(unittest.TestCase):
    """Config save and load should work with files."""

    def test_save_creates_file(self):
        """save() should create the config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.yml"
            config = Config(theme="light")
            config.save(path)
            self.assertTrue(path.exists())

    def test_save_load_roundtrip(self):
        """save() then load() should return same config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.yml"
            original = Config(
                sidebar_width_percent=25,
                theme="light",
                startup_view="library",
            )
            original.save(path)
            loaded = Config.load(path)
            self.assertEqual(loaded.sidebar_width_percent, 25)
            self.assertEqual(loaded.theme, "light")
            self.assertEqual(loaded.startup_view, "library")

    def test_load_nonexistent_returns_defaults(self):
        """load() with nonexistent file should return defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nonexistent.yml"
            config = Config.load(path)
            self.assertEqual(config.theme, "dark")


if __name__ == "__main__":
    unittest.main()
