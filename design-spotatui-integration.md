# Design: spotatui Integration Phase 1 — UI Framework

## Architecture Overview

```
src/spotify_tui_tool/
├── app.py                 # Main app (existing, will be refactored)
├── main.py                # Entry point (existing)
├── models.py              # Data models (existing)
├── exceptions.py          # Exceptions (existing)
├── playerctl.py           # Player controller (existing)
├── search.py              # Search service (existing)
├── now_playing.py         # Now playing widget (existing)
├── ui/                    # NEW: UI components
│   ├── __init__.py
│   ├── layout.py          # 3-panel layout manager
│   ├── sidebar.py         # Sidebar component
│   ├── content.py         # Content area component
│   ├── playbar.py         # Playbar component
│   ├── views/             # NEW: Content views
│   │   ├── __init__.py
│   │   ├── home.py        # Home view
│   │   ├── library.py     # Library view
│   │   ├── playlists.py   # Playlists view
│   │   ├── search.py      # Search view
│   │   ├── queue.py       # Queue view
│   │   ├── settings.py    # Settings view
│   │   └── help.py        # Help view
│   └── widgets/           # NEW: Reusable widgets
│       ├── __init__.py
│       ├── track_table.py # Track table widget
│       ├── progress_bar.py# Progress bar widget
│       └── volume_bar.py  # Volume bar widget
├── config.py              # NEW: Configuration manager
└── state.py               # NEW: App state manager
```

## Component Design

### 1. Layout Manager (`ui/layout.py`)

```python
class LayoutManager(Widget):
    """Manages the 3-panel layout."""
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="main-container"):
            yield Sidebar(id="sidebar")
            with Vertical(id="content-area"):
                yield Content(id="content")
                yield Playbar(id="playbar")
```

### 2. Sidebar (`ui/sidebar.py`)

```python
class Sidebar(Widget):
    """Left panel with source selector, library, playlists."""
    
    # Sections
    SOURCES = ["Spotify", "Local", "Radio"]
    LIBRARY = ["Liked Songs", "Albums", "Artists"]
    
    def compose(self) -> ComposeResult:
        yield Static("Sources", classes="section-header")
        yield ListView(*[
            ListItem(Static(source)) for source in self.SOURCES
        ], id="sources-list")
        
        yield Static("Library", classes="section-header")
        yield ListView(*[
            ListItem(Static(item)) for item in self.LIBRARY
        ], id="library-list")
        
        yield Static("Playlists", classes="section-header")
        yield ListView(
            ListItem(Static("(No playlists)")),
            id="playlists-list"
        )
```

### 3. Content Area (`ui/content.py`)

```python
class Content(Widget):
    """Center panel displaying the current view."""
    
    view_map = {
        "home": HomeView,
        "library": LibraryView,
        "playlists": PlaylistsView,
        "search": SearchView,
        "queue": QueueView,
        "settings": SettingsView,
        "help": HelpView,
    }
    
    def switch_view(self, view_name: str) -> None:
        """Switch to a different view."""
        # Remove current view
        # Mount new view
        pass
```

### 4. Playbar (`ui/playbar.py`)

```python
class Playbar(Widget):
    """Bottom panel with now-playing info and controls."""
    
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static(id="track-info")
            yield Static(id="progress")
            yield Static(id="volume")
            yield Static(id="controls")
    
    def update_track(self, info: TrackInfo) -> None:
        """Update the playbar with current track info."""
        # Update artist, title, album
        # Update progress bar
        # Update volume
        # Update control indicators
```

### 5. Views

#### Home View (`ui/views/home.py`)
```python
class HomeView(Widget):
    """Home screen with recently played."""
    
    def compose(self) -> ComposeResult:
        yield Static("Recently Played", classes="view-header")
        yield DataTable(id="recent-tracks")
```

#### Library View (`ui/views/library.py`)
```python
class LibraryView(Widget):
    """Liked songs library."""
    
    def compose(self) -> ComposeResult:
        yield Static("Liked Songs", classes="view-header")
        yield DataTable(id="library-tracks")
        # Columns: #, Title, Artist, Album, Duration
```

#### Search View (`ui/views/search.py`)
```python
class SearchView(Widget):
    """Search with input and results tabs."""
    
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search tracks, albums, artists...", id="search-input")
        yield TabbedContent(
            TabPane("Tracks", id="tracks-tab"),
            TabPane("Albums", id="albums-tab"),
            TabPane("Artists", id="artists-tab"),
            id="search-tabs"
        )
```

#### Settings View (`ui/views/settings.py`)
```python
class SettingsView(Widget):
    """Settings and configuration."""
    
    def compose(self) -> ComposeResult:
        yield Static("Settings", classes="view-header")
        yield Static("Keybindings:", classes="section-header")
        yield Static("  Space - Play/Pause")
        yield Static("  n/p - Next/Previous")
        # ... more keybindings
        yield Static("Options:", classes="section-header")
        yield Static("  Shuffle: OFF")
        yield Static("  Repeat: OFF")
```

#### Help View (`ui/views/help.py`)
```python
class HelpView(Widget):
    """Help screen with all keybindings."""
    
    def compose(self) -> ComposeResult:
        yield Static("Help", classes="view-header")
        yield DataTable(id="help-table")
        # Columns: Key, Action, Category
```

## State Management (`state.py`)

```python
@dataclass
class AppState:
    """Global application state."""
    
    # Current view
    current_view: str = "home"
    
    # Sidebar selection
    sidebar_section: str = "library"
    sidebar_index: int = 0
    
    # Playback state
    is_playing: bool = False
    current_track: Optional[TrackInfo] = None
    volume: float = 0.5
    shuffle: bool = False
    repeat_mode: str = "off"  # off, track, all
    
    # Search state
    search_query: str = ""
    search_results: List = field(default_factory=list)
    
    # Queue
    queue: List[TrackInfo] = field(default_factory=list)
```

## Configuration (`config.py`)

```python
@dataclass
class Config:
    """App configuration."""
    
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
    
    @classmethod
    def load(cls) -> "Config":
        """Load config from file or return defaults."""
        # Try to load from ~/.config/spotify-tui-tool/config.yml
        # Fall back to defaults
        pass
    
    def save(self) -> None:
        """Save config to file."""
        pass
```

## Keybindings Implementation

```python
# In app.py
BINDINGS = [
    # Playback
    Binding("space", "play_pause", "Play/Pause"),
    Binding("n", "next_track", "Next"),
    Binding("p", "previous_track", "Previous"),
    Binding("plus", "volume_up", "Vol +"),
    Binding("minus", "volume_down", "Vol -"),
    Binding("less_than", "seek_backward", "Seek -"),
    Binding("greater_than", "seek_forward", "Seek +"),
    
    # Actions
    Binding("f", "like_track", "Like"),
    Binding("slash", "focus_search", "Search"),
    
    # Views
    Binding("1", "view_home", "Home"),
    Binding("2", "view_library", "Library"),
    Binding("3", "view_playlists", "Playlists"),
    Binding("4", "view_search", "Search"),
    Binding("5", "view_queue", "Queue"),
    Binding("6", "view_settings", "Settings"),
    
    # Navigation
    Binding("j", "sidebar_down", "Down"),
    Binding("k", "sidebar_up", "Up"),
    Binding("h", "sidebar_left", "Left"),
    Binding("l", "sidebar_right", "Right"),
    
    # System
    Binding("escape", "go_back", "Back"),
    Binding("q", "quit", "Quit"),
    Binding("question", "show_help", "Help"),
]
```

## CSS Styling

```css
/* layout.tcss */
#main-container {
    height: 100%;
}

#sidebar {
    width: 20%;
    background: $surface;
    border-right: solid $primary;
}

#content-area {
    width: 80%;
}

#content {
    height: 1fr;
}

#playbar {
    height: 6;
    background: $surface;
    border-top: solid $primary;
}

/* Sidebar styles */
.section-header {
    text-style: bold;
    color: $primary;
}

/* Playbar styles */
#track-info {
    width: 40%;
}

#progress {
    width: 30%;
}

#volume {
    width: 15%;
}

#controls {
    width: 15%;
}
```

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock playerctl for playback tests
- Test state management
- Test configuration loading

### Integration Tests
- Test view switching
- Test keybinding mappings
- Test layout responsiveness

### Visual Tests
- Use Textual pilot for headless testing
- Verify layout renders correctly
- Verify components update properly

## Implementation Order

1. **State Manager** (`state.py`) — Foundation
2. **Config Manager** (`config.py`) — Configuration
3. **Layout Manager** (`ui/layout.py`) — 3-panel structure
4. **Sidebar** (`ui/sidebar.py`) — Navigation
5. **Playbar** (`ui/playbar.py`) — Playback display
6. **Content Area** (`ui/content.py`) — View switching
7. **Views** (`ui/views/*.py`) — Individual screens
8. **Widgets** (`ui/widgets/*.py`) — Reusable components
9. **Keybindings** — Wire everything together
10. **CSS Styling** — Visual polish
11. **Tests** — Validate everything
