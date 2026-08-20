# Spotify TUI Tool

A Textual-based TUI for controlling SpotX-patched Spotify desktop via playerctl/MPRIS — no Premium required.

## Features

- **Playback control**: play, pause, next, previous
- **Volume control**: up/down with vim-style keybindings
- **Seek**: forward/backward 5 seconds
- **Now Playing**: real-time track metadata display (artist, title, album, progress)
- **Search**: paste Spotify URIs or URLs to play tracks, playlists, albums
- **History**: last 10 opened URIs, most-recent-first
- **3-panel layout**: sidebar, content area, playbar
- **View switching**: Home, Library, Playlists, Search, Queue, Settings, Help

## Requirements

- Python 3.10+
- `playerctl` installed and on PATH
- Spotify desktop client running (patched with SpotX for ad-free experience)

## Installation

```bash
# Clone the repository
git clone https://github.com/Reaan06/spotify-tui-tool.git
cd spotify-tui-tool

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"
```

## Usage

```bash
# Run the TUI
spotify-tui-tool

# Or run directly
python -m spotify_tui_tool.app
```

### Keybindings

| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `n` | Next track |
| `p` | Previous track |
| `+` / `-` | Volume up/down |
| `<` / `>` | Seek backward/forward |
| `F` | Like/Unlike (stub) |
| `/` | Search view |
| `1`-`6` | Switch views (1=Home, 2=Library, 3=Playlists, 4=Search, 5=Queue, 6=Settings) |
| `j` / `k` | Sidebar navigation |
| `h` / `l` | Sidebar/Content navigation |
| `?` | Help view |
| `Esc` | Back to Home |
| `q` | Quit |

### Views

- **Home**: Currently playing track
- **Library**: Liked songs (stub — not available via playerctl)
- **Playlists**: Playlist list (stub — use spotatui for browsing)
- **Search**: Search with URI input
- **Queue**: Current play queue
- **Settings**: Configuration and keybinding reference
- **Help**: Full keybinding table

## Development

### Running Tests

```bash
# Run all unit tests
python -m unittest discover -s tests -v

# Run specific test file
python -m unittest tests.test_playerctl -v

# Run integration tests (requires running Spotify)
python -m unittest tests.test_integration -v
```

### Project Structure

```
spotify-tui-tool/
├── src/spotify_tui_tool/
│   ├── __init__.py              # Package metadata
│   ├── app.py                   # Main Textual app
│   ├── config.py                # Configuration manager
│   ├── exceptions.py            # Exception hierarchy
│   ├── main.py                  # CLI entry point
│   ├── models.py                # Data models (TrackInfo, ParsedURI, PlaybackStatus)
│   ├── now_playing.py           # Metadata polling and parsing
│   ├── playerctl.py             # PlayerController subprocess wrapper
│   ├── search.py                # URI validation and search service
│   ├── spotify_client.py        # Unified Spotify service layer
│   ├── state.py                 # Global state management
│   └── ui/
│       ├── __init__.py          # UI exports
│       ├── content.py           # Content area with view switching
│       ├── layout.py            # 3-panel layout manager
│       ├── playbar.py           # Now playing + controls
│       ├── sidebar.py           # Navigation sidebar
│       ├── styles.css           # CSS styling
│       └── views/
│           ├── __init__.py      # View exports
│           ├── help.py          # Help view (keybindings)
│           ├── home.py          # Home view (current track)
│           ├── library.py       # Library view (liked songs)
│           ├── playlists.py     # Playlists view
│           ├── queue.py         # Queue view
│           ├── search.py        # Search view
│           └── settings.py      # Settings view
├── tests/
│   ├── test_app.py              # App instantiation and action tests
│   ├── test_config.py           # Config manager tests
│   ├── test_content.py          # Content area tests
│   ├── test_exceptions.py       # Exception hierarchy tests
│   ├── test_layout.py           # Layout manager tests
│   ├── test_playbar.py          # Playbar component tests
│   ├── test_sidebar.py          # Sidebar component tests
│   ├── test_spotify_client.py   # SpotifyClient service tests
│   ├── test_state.py            # State manager tests
│   ├── test_ui_integration.py   # UI integration tests
│   └── ... (other test files)
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Spotify TUI (Textual)                   │
├──────────────┬──────────────────┬───────────────────────────┤
│  UI Layer    │  Core Logic      │  External Integration      │
│  (Textual)   │  (Python)        │                            │
├──────────────┼──────────────────┼───────────────────────────┤
│ LayoutManager│ PlayerController │ playerctl (subprocess)     │
│ Sidebar      │ SearchService    │ - playback control         │
│ ContentArea  │ SpotifyClient    │ - metadata polling         │
│ Playbar      │ Config           │ - volume/seek              │
│ Views        │ State            │                            │
└──────────────┴──────────────────┴───────────────────────────┘
```

## License

MIT
