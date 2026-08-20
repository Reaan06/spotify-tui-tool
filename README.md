# Spotify TUI Tool

A Textual-based TUI for controlling SpotX-patched Spotify desktop via playerctl/MPRIS — no Premium required.

## Features

- **Playback control**: play, pause, next, previous
- **Volume control**: up/down with vim-style keybindings
- **Now Playing**: real-time track metadata display (artist, title, album, progress)
- **Search**: paste Spotify URIs or URLs to play tracks, playlists, albums
- **History**: last 10 opened URIs, most-recent-first

## Requirements

- Python 3.10+
- `playerctl` installed and on PATH
- Spotify desktop client running (patched with SpotX for ad-free experience)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/spotify-tui-tool.git
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
| `n` / `l` | Next track |
| `p` / `h` | Previous track |
| `k` | Volume up |
| `j` | Volume down |
| `/` | Focus search input |
| `Enter` | Play URI (in search) |
| `q` / `Ctrl+C` | Quit |

### Search

1. Press `/` to focus the search input
2. Paste a Spotify URI or URL:
   - `spotify:track:6rqhFgbbKwnb9MLmUQDhG6`
   - `https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6`
   - `spotify:playlist:37i9dQZF1DXcBWIGoYBM5M`
3. Press `Enter` to play

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
│   ├── __init__.py          # Package metadata
│   ├── app.py               # Main Textual app
│   ├── exceptions.py        # Exception hierarchy
│   ├── main.py              # CLI entry point
│   ├── models.py            # Data models (TrackInfo, ParsedURI, PlaybackStatus)
│   ├── now_playing.py       # Metadata polling and parsing
│   ├── playerctl.py         # PlayerController subprocess wrapper
│   └── search.py            # URI validation and search service
├── tests/
│   ├── test_app.py          # App instantiation and action tests
│   ├── test_exceptions.py   # Exception hierarchy tests
│   ├── test_integration.py  # Live Spotify integration tests
│   ├── test_models.py       # Data model tests
│   ├── test_now_playing.py  # Metadata parsing tests
│   ├── test_playerctl.py    # PlayerController tests
│   └── test_search.py       # SearchService tests
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Spotify TUI (Textual)                   │
├──────────────┬──────────────────┬───────────────────────────┤
│  UI Layer    │  Core Logic      │  External Integration      │
│  (Textual)   │  (Python)        │                            │
├──────────────┼──────────────────┼───────────────────────────┤
│ NowPlaying   │ PlayerController │ playerctl (subprocess)     │
│ SearchView   │ SearchService    │ - playback control         │
│ Keybindings  │                  │ - metadata polling         │
└──────────────┴──────────────────┴───────────────────────────┘
```

## License

MIT
