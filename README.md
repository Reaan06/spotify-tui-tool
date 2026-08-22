# Spotify TUI Tool

A Textual-based TUI for controlling SpotX-patched Spotify desktop via playerctl/MPRIS — no Premium required.

## Features

- **Playback control**: play, pause, next, previous
- **Volume control**: up/down with vim-style keybindings
- **Seek**: forward/backward 5 seconds
- **Now Playing**: real-time track metadata display (artist, title, album, progress)
- **Search**: browse Spotify track, album, and artist results
- **History**: last 10 opened URIs, most-recent-first
- **3-panel layout**: sidebar, content area, playbar
- **View switching**: Home, Library, Playlists, Search, Settings, Help, Login

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
| `/` | Search view |
| `1`-`4` | Switch views (1=Home, 2=Library, 3=Playlists, 4=Search) |
| `6` / `7` | Settings / Login |
| `j` / `k` | Sidebar navigation |
| `h` / `l` | Sidebar/Content navigation |
| `?` | Help view |
| `Esc` | Close the active transient view |
| `q` | Close an empty transient search, close another transient view, or quit |

### Views

- **Home**: Currently playing track
- **Library**: Read-only liked songs from the Spotify Web API
- **Playlists**: Read-only user playlists from the Spotify Web API
- **Search**: Spotify track, album, and artist results
- **Settings**: Configuration and keybinding reference
- **Help**: Full keybinding table

### Spotify API Authentication

Use the Login view (`7`) or the sidebar login action to start Spotify OAuth.
The application uses PKCE with a loopback callback at
`http://127.0.0.1:8888/callback` and requests read-only scopes for the current
profile, liked songs, and playlists. Successful tokens are stored in
`~/.config/spotify-tui-tool/tokens.json` with private file permissions, then
validated through the read-only `/me` endpoint before browsing is enabled.

Playback remains playerctl/MPRIS-based; the Spotify Web API is not used for
streaming or playback control.

## Development

### Running Tests

The supported offline test runner is `unittest`. Coverage, linting, and static
type checking are not currently configured for this project. Live Spotify,
`playerctl`, and MPRIS checks are opt-in and depend on the local environment.

```bash
# Run all unit tests
.venv/bin/python -m unittest discover -s tests -v

# Run specific test file
.venv/bin/python -m unittest tests.test_playerctl -v

# Run live integration checks only when Spotify and playerctl/MPRIS are available
.venv/bin/python -m unittest tests.test_integration -v
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
│           ├── search.py        # Search view
│           ├── settings.py      # Settings view
│           └── login.py         # Login view
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
