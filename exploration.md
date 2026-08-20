# Exploration: Spotify TUI Tool

## Current State

This is a new project at `/home/reaan/spotify-tui-tool` with only a git repo initialized. The user wants a terminal-based tool to control Spotify desktop (patched with SpotX) without requiring Spotify Premium.

Key constraints:
- Uses `playerctl` v2.4.1 for MPRIS playback control
- Python recommended (has unittest runner, bash doesn't)
- User runs Fish shell
- SpotX patches the desktop client to block ads and unlock some premium features on Linux

## Affected Areas

- New project — no existing code to modify
- Will create: main TUI application, playerctl wrapper, search module, config

---

## 1. Python TUI Options Comparison

| Library | Type | Interactive | Styling | Learning Curve | Best For |
|---------|------|-------------|---------|----------------|----------|
| **Textual** | Full app framework | Yes (async event loop) | CSS-like `.tcss` | Moderate | Interactive full-screen apps |
| **Rich** | Rendering library | No (use with Textual) | Markup/styles | Low | Pretty output, tables, progress bars |
| **Blessed** | curses wrapper | Yes | ANSI/curses | Low | Simple TUIs, lighter weight |
| **curses** | Stdlib (low-level) | Yes | Raw ANSI | High | Maximum control, no deps |
| **Urwid** | Full framework | Yes (event loop) | Canvas/widgets | High | Enterprise, long-term stability |
| **PyTermGUI** | Lightweight | Yes | YAML themes | Low | Quick prototypes |

### Recommendation: **Textual + Rich**

**Why:**
- Textual is built on Rich — they work together seamlessly
- Modern, active development (36k+ stars, 2026 updates)
- CSS-like styling is familiar and maintainable
- Reactive widgets + async event loop fit playerctl's async nature
- Rich provides excellent tables, panels, progress bars for track display
- Can start simple with Rich, migrate to Textual when interactivity needed

---

## 2. How playerctl Works for Search/Play

### What playerctl CAN do:
```bash
# Playback control
playerctl --player=spotify play|pause|play-pause|stop|next|previous
playerctl --player=spotify position 30+|30-|30
playerctl --player=spotify volume 0.5|0.1+|0.1-

# Metadata
playerctl --player=spotify metadata --format '{{artist}} - {{title}}'
playerctl --player=spotify status

# Open URI (KEY for "search and play")
playerctl --player=spotify open 'spotify:track:6rqhFgbbKwnb9MLmUQDhG6'
playerctl --player=spotify open 'spotify:playlist:37i9dQZF1DXcBWIGoYBM5M'
playerctl --player=spotify open 'spotify:album:1Je1IMUlBXcx1Fz0WE7oPT'
```

### What playerctl CANNOT do:
- **No native search** — cannot query Spotify's catalog
- **No browse** — cannot list playlists, albums, artists
- **No queue management** — cannot view/modify play queue

### Spotify URI Format:
```
spotify:track:{22-char-base62-id}
spotify:album:{22-char-base62-id}
spotify:playlist:{22-char-base62-id}
spotify:artist:{22-char-base62-id}
spotify:show:{id}      # podcasts
spotify:episode:{id}   # podcast episodes
```

### SpotX + playerctl Compatibility:
- SpotX-Bash exists for Linux/macOS (patches desktop client)
- Patched Spotify still exposes MPRIS interface
- `playerctl open` with Spotify URIs **should work** — MPRIS `OpenUri` is standard
- Historical issue: Spotify desktop sometimes ignored `OpenUri` (2019), but modern versions + SpotX patches likely work

---

## 3. Limitations Without Spotify API (No Premium)

| Feature | Without Premium + No API | With SpotX + playerctl |
|---------|--------------------------|------------------------|
| Playback control | ❌ (Web API requires Premium) | ✅ playerctl via MPRIS |
| Current track info | ❌ | ✅ playerctl metadata |
| Volume control | ❌ | ✅ playerctl volume |
| Search catalog | ❌ (Web API requires auth) | ❌ Need alternative |
| Playlists/browse | ❌ | ❌ Need alternative |
| Queue management | ❌ | ❌ MPRIS doesn't expose queue |
| Skip unlimited | ❌ (Free tier limited) | ✅ SpotX unlocks skips |
| Ad-free | ❌ | ✅ SpotX blocks ads |

### Search Alternatives (No Official API):

| Approach | Pros | Cons |
|----------|------|------|
| **Web scraping (spotify.com/search)** | No auth, full catalog | Fragile, rate-limited, ToS gray area |
| **Internal Spotify Web API** (used by web player) | Rich data, search works | Unstable, requires token extraction, ToS violation |
| **Third-party scrapers** (Apify, spotify-scraper) | Ready-made | External dependency, rate limits |
| **User copies URI from Spotify** | Simple, reliable, no scraping | Manual step, not "in-app" search |
| **Local database cache** | Fast, offline | Stale, maintenance burden |

### Recommended Search Strategy:
**Phase 1 (MVP):** Manual URI input — user copies `spotify:track:...` from Spotify app/web, pastes into TUI, tool plays it via `playerctl open`.

**Phase 2:** Add web search via scraping `https://open.spotify.com/search/{query}` — parse track URIs from results.

**Phase 3 (Optional):** Integrate with `spotify-scraper` Python lib or similar for richer search.

---

## 4. Simplest Effective Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Spotify TUI (Textual)                   │
├──────────────┬──────────────────┬───────────────────────────┤
│  UI Layer    │  Core Logic      │  External Integration      │
│  (Textual)   │  (Python)        │                            │
├──────────────┼──────────────────┼───────────────────────────┤
│ • NowPlaying │ • PlayerController│ • playerctl (subprocess)  │
│   Panel      │   - play/pause    │   - playback control      │
│ • SearchView │   - next/prev     │   - metadata polling      │
│   (input +   │   - volume        │   - open URI              │
│   results)   │   - status        │                            │
│ • QueueView  │ • SearchService   │ • Web Scraper (Phase 2)   │
│ • PlaylistView│  - parse URI     │   - search.spotify.com    │
│ • Keybindings│  - validate URI   │   - parse HTML/JSON       │
│              │  - history        │                            │
└──────────────┴──────────────────┴───────────────────────────┘
```

### Component Details:

#### PlayerController (playerctl wrapper)
```python
class PlayerController:
    def __init__(self, player_name: str = "spotify"):
        self.player = player_name
    
    def run(self, *args) -> str:  # subprocess wrapper
        ...
    
    def play(self): self.run("play")
    def pause(self): self.run("pause")
    def next(self): self.run("next")
    def previous(self): self.run("previous")
    def set_volume(self, level: float): self.run("volume", str(level))
    def get_volume(self) -> float: ...
    def get_metadata(self) -> TrackInfo: ...
    def get_status(self) -> PlaybackStatus: ...
    def open_uri(self, uri: str): self.run("open", uri)
```

#### SearchService (Phase 1: URI validation only)
```python
class SearchService:
    SPOTIFY_URI_PATTERN = re.compile(
        r'spotify:(track|album|playlist|artist|show|episode):[a-zA-Z0-9]{22}'
    )
    
    def validate_uri(self, uri: str) -> Optional[ParsedURI]:
        ...
    
    def parse_uri(self, uri: str) -> ParsedURI:
        # Returns {type: 'track', id: '...', uri: 'spotify:track:...'}
        ...
```

#### NowPlaying Panel (Rich/Textual)
- Polls metadata every 1-2 seconds via `playerctl metadata --format ...`
- Displays: album art (ASCII/Unicode), title, artist, album, progress bar, volume
- Click/key handlers for play/pause, next, prev, volume

---

## Recommendation

### Start with this MVP (2-3 files):
1. **`main.py`** — Textual App with NowPlaying panel + URI input
2. **`playerctl.py`** — PlayerController wrapper
3. **`search.py`** — URI validation/parsing

### Keybindings (vim-style):
| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `n` / `l` | Next track |
| `p` / `h` | Previous track |
| `j` / `k` | Volume down/up |
| `/` | Focus search input |
| `Enter` (in search) | Play URI |
| `q` / `Ctrl+C` | Quit |

### Dependencies:
```toml
# pyproject.toml
[project]
dependencies = [
    "textual>=0.52",
    "rich>=13.7",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio"]
```

### Testing:
- Unit tests for `PlayerController` (mock subprocess)
- Unit tests for `SearchService` URI parsing
- Integration test: spin up playerctl with a mock MPRIS player (or test against real Spotify if running)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SpotX breaks MPRIS | Low | High | Test early; fallback to dbus-send |
| `playerctl open` doesn't work with patched Spotify | Medium | High | Test immediately; alternative: `dbus-send` directly |
| Spotify changes web HTML (breaks scraping) | High (Phase 2) | Medium | Use robust selectors; fallback to manual URI |
| Playerctl not installed / no D-Bus session | Low | High | Check at startup; clear error message |
| Fish shell completion | Low | Low | Generate completions via `playerctl --help` |

---

## Ready for Proposal

**Yes** — the exploration is complete. The orchestrator should tell the user:

1. **Textual + Rich** is the recommended TUI stack
2. **playerctl** handles all playback control + metadata + URI opening
3. **Search** requires a separate strategy — start with manual URI input (MVP), add web scraping later
4. **Architecture** is clean: Textual UI → Python core → playerctl subprocess
5. **Risk**: Verify `playerctl open spotify:track:...` works with SpotX-patched Spotify first

### Next Step:
Run a quick validation:
```bash
# 1. Start Spotify (patched with SpotX)
# 2. Get a track URI from Spotify (right-click → Share → Copy Spotify URI)
# 3. Test: playerctl --player=spotify open 'spotify:track:...'
# 4. Test: playerctl --player=spotify metadata --format '{{artist}} - {{title}}'
```

If both work → proceed to **Proposal** phase with this architecture.