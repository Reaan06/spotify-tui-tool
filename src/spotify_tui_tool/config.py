"""Configuration manager — load/save app config.

Phase 1 of spotatui integration.  Manages app configuration
with YAML file support.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Optional YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class Config:
    """App configuration with sensible defaults."""
    
    # Layout
    sidebar_width_percent: int = 20
    playbar_height_rows: int = 6
    sidebar_position: str = "left"  # left, right, hidden
    
    # Behavior
    tick_rate_ms: int = 1000
    volume_increment: int = 10
    seek_milliseconds: int = 5000
    
    # Theme
    theme: str = "dark"
    
    # Startup
    startup_view: str = "home"
    
    @classmethod
    def default_config_path(cls) -> Path:
        """Get the default config file path."""
        config_dir = Path.home() / ".config" / "spotify-tui-tool"
        return config_dir / "config.yml"
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> Config:
        """Load config from file or return defaults.
        
        Args:
            path: Path to config file. If None, uses default location.
        
        Returns:
            Config instance with loaded or default values.
        """
        if path is None:
            path = cls.default_config_path()
        
        if not path.exists():
            return cls()
        
        if not HAS_YAML:
            return cls()
        
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}
            return cls._from_dict(data)
        except Exception:
            return cls()
    
    @classmethod
    def _from_dict(cls, data: dict) -> Config:
        """Create Config from a dictionary."""
        config = cls()
        
        # Layout
        if "sidebar_width_percent" in data:
            config.sidebar_width_percent = int(data["sidebar_width_percent"])
        if "playbar_height_rows" in data:
            config.playbar_height_rows = int(data["playbar_height_rows"])
        if "sidebar_position" in data:
            config.sidebar_position = str(data["sidebar_position"])
        
        # Behavior
        if "tick_rate_ms" in data:
            config.tick_rate_ms = int(data["tick_rate_ms"])
        if "volume_increment" in data:
            config.volume_increment = int(data["volume_increment"])
        if "seek_milliseconds" in data:
            config.seek_milliseconds = int(data["seek_milliseconds"])
        
        # Theme
        if "theme" in data:
            config.theme = str(data["theme"])
        
        # Startup
        if "startup_view" in data:
            config.startup_view = str(data["startup_view"])
        
        return config
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save config to file.
        
        Args:
            path: Path to config file. If None, uses default location.
        """
        if path is None:
            path = self.default_config_path()
        
        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if not HAS_YAML:
            # Can't save without YAML
            return
        
        data = self._to_dict()
        
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
    
    def _to_dict(self) -> dict:
        """Convert Config to a dictionary."""
        return {
            "sidebar_width_percent": self.sidebar_width_percent,
            "playbar_height_rows": self.playbar_height_rows,
            "sidebar_position": self.sidebar_position,
            "tick_rate_ms": self.tick_rate_ms,
            "volume_increment": self.volume_increment,
            "seek_milliseconds": self.seek_milliseconds,
            "theme": self.theme,
            "startup_view": self.startup_view,
        }
