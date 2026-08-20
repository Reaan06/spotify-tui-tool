# Exploration: spotatui Feature Integration

## Goal
Replicate spotatui's TUI frontend in our Textual-based spotify-tui-tool, integrating all visual and interactive features while keeping our playerctl backend for playback control.

## spotatui Feature Analysis

### Core UI Structure (3-panel layout)
1. **Sidebar** (left) — Sources, Library, Playlists, Devices
2. **Content Area** (center) — Track tables, album lists, search results
3. **Playbar** (bottom) — Now playing, progress, controls, cover art

### Features to Replicate

| Feature | Priority | Complexity | Notes |
|---------|----------|------------|-------|
| Library view (liked songs) | HIGH | Medium | Requires Spotify Web API auth |
| Playlists view | HIGH | Medium | Requires Spotify Web API auth |
| Search (tracks, albums, artists) | HIGH | Medium | Requires Spotify Web API auth |
| Queue management | HIGH | Low | playerctl has limited queue support |
| Lyrics display | MEDIUM | High | Need external API (LRCLIB, etc.) |
| Cover art rendering | MEDIUM | High | Terminal image rendering (timg, chafa) |
| Audio visualizer | LOW | High | System-wide FFT, complex |
| Mini-player view | MEDIUM | Low | Simplified playbar |
| Settings screen | MEDIUM | Low | Config file management |
| Help screen | LOW | Low | Keybinding reference |
| Devices view | LOW | Medium | Spotify Connect devices |
| Stats/listening history | LOW | Medium | Local SQLite database |

### UI Components to Build

1. **Sidebar**
   - Source selector (Spotify, Local, Radio)
   - Library section (Liked Songs, Albums, Artists)
   - Playlists list
   - Device selector

2. **Content Views**
   - Track table (with columns: #, Title, Artist, Album, Duration)
   - Album grid/list
   - Artist list
   - Search results (tabs: Tracks, Albums, Artists, Playlists)
   - Queue view
   - Lyrics view
   - Settings form
   - Help reference

3. **Playbar**
   - Now playing info (artist, title, album)
   - Progress bar with time
   - Volume slider
   - Control buttons (prev, play/pause, next, shuffle, repeat)
   - Cover art thumbnail (optional)

4. **Navigation**
   - Vim-style keybindings (h/j/k/l)
   - Tab switching (1-6 for views)
   - Modal dialogs (search, settings)

### Technical Challenges

1. **Spotify Web API Authentication**
   - Need OAuth2 flow for accessing library/playlists/search
   - Token refresh mechanism
   - Scope requirements: user-library-read, user-read-playback-state, etc.

2. **Cover Art Rendering**
   - Terminal image protocols: Kitty, iTerm2, Sixel
   - Fallback: ASCII art or skip
   - Library: `timg`, `chafa`, or `Viuer` (Rust) equivalent in Python

3. **Lyrics**
   - External API: LRCLIB (free, no auth)
   - Synced lyrics format (LRC)
   - Display: line-by-line highlighting

4. **Queue Management**
   - playerctl has limited queue support
   - May need to track queue locally
   - Spotify Web API: `GET /v1/me/player/queue` (requires Premium)

5. **Audio Visualizer**
   - System-wide audio capture
   - FFT processing
   - Terminal rendering (bar chart, waveform)
   - Complex, defer to later phase

### Architecture Decision

**Recommended approach:** Build the UI framework first, then integrate Spotify API for data.

```
┌─────────────────────────────────────────────────────────────┐
│                    Spotify TUI (Textual)                     │
├──────────────┬──────────────────┬───────────────────────────┤
│  UI Layer    │  Core Logic      │  External Integration      │
│  (Textual)   │  (Python)        │                            │
├──────────────┼──────────────────┼───────────────────────────┤
│ • Sidebar    │ • PlayerController│ • playerctl (playback)    │
│ • Content    │ • SpotifyClient   │ • Spotify Web API (data)  │
│ • Playbar    │ • SearchService   │ • LRCLIB (lyrics)         │
│ • Modals     │ • QueueManager    │ • timg/chafa (images)     │
│ • Keybindings│ • ConfigManager   │                           │
└──────────────┴──────────────────┴───────────────────────────┘
```

### Implementation Phases

**Phase 1: UI Framework** (this PR)
- 3-panel layout with resizable panes
- Sidebar with source/library/playlists sections
- Content area with view switching
- Playbar with controls
- Vim-style keybindings
- Settings screen

**Phase 2: Spotify Integration** (next PR)
- OAuth2 authentication flow
- Library fetching (liked songs, albums, artists)
- Playlist fetching and display
- Search via Spotify Web API

**Phase 3: Enhanced Features** (future PRs)
- Queue management
- Lyrics display
- Cover art rendering
- Stats/history
- Audio visualizer

### Dependencies

```toml
# pyproject.toml additions
dependencies = [
    "textual>=0.52",
    "rich>=13.7",
    "httpx>=0.27",           # HTTP client for Spotify API
    "crypto车库>=42.0",       # OAuth2 handling
    "Pillow>=10.0",          # Image processing for cover art
]

[project.optional-dependencies]
images = ["timg>=1.0"]      # Terminal image viewer
lyrics = ["lrcparser>=0.1"] # LRC lyrics parser
```

### Keybindings (matching spotatui)

| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `n`/`p` | Next/Previous |
| `+`/`-` | Volume up/down |
| `<`/`>` | Seek backward/forward |
| `F` | Like/Unlike |
| `Ctrl-s` | Toggle shuffle |
| `Ctrl-r` | Cycle repeat |
| `/` | Search |
| `a` | Jump to album |
| `A` | Jump to artist |
| `Q` | Show queue |
| `B` | Lyrics view |
| `T` | Mini-player |
| `G` | Cover art |
| `Alt-,` | Settings |
| `?` | Help |
| `1-6` | Switch views |
| `Esc` | Back |
| `q` | Quit |

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Spotify API rate limits | Medium | Medium | Cache responses, exponential backoff |
| OAuth2 token expiry | High | Low | Auto-refresh before expiry |
| Terminal image support varies | High | Low | Graceful fallback to text |
| Lyrics API unavailable | Medium | Low | Skip lyrics feature |
| playerctl queue limited | High | Medium | Track queue locally |

### Next Steps

1. Create proposal artifact
2. Design the 3-panel layout in Textual
3. Implement sidebar component
4. Implement content views
5. Implement playbar
6. Add keybindings
7. Test with real Spotify
