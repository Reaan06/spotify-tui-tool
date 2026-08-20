# Proposal: spotatui Feature Integration

## Intent
Transform spotify-tui-tool from a simple playback controller into a full-featured TUI that replicates spotatui's frontend, providing library browsing, playlist management, search, queue control, lyrics, and cover art — all while using playerctl for actual playback control.

## Scope

### In Scope (Phase 1 — this PR)
- 3-panel layout (Sidebar, Content, Playbar)
- Sidebar with source selector, library, playlists
- Content area with view switching (Home, Library, Playlists, Search, Queue, Settings)
- Playbar with now-playing info, progress, controls
- Vim-style keybindings matching spotatui
- Settings screen
- Help screen

### Out of Scope (future PRs)
- Spotify Web API authentication (Phase 2)
- Actual library/playlist data fetching (Phase 2)
- Lyrics display (Phase 3)
- Cover art rendering (Phase 3)
- Audio visualizer (Phase 3)
- Stats/history (Phase 3)

## Approach

### Architecture
- **UI Framework**: Textual with CSS styling
- **Layout**: 3-panel grid (sidebar 20%, content 60%, playbar 15%)
- **State Management**: Reactive properties for current view, selected item, playback state
- **Navigation**: View switching via sidebar or keybindings

### Components

1. **Sidebar**
   - Source selector (Spotify, Local, Radio)
   - Library section (Liked Songs, Albums, Artists)
   - Playlists list (placeholder until API integration)
   - Device selector

2. **Content Views**
   - Home: Recently played, recommendations
   - Library: Liked songs table
   - Playlists: Playlist list
   - Search: Search input + results tabs
   - Queue: Current queue
   - Settings: Configuration options

3. **Playbar**
   - Now playing: artist — title
   - Album name
   - Progress bar with time
   - Volume slider
   - Controls: prev, play/pause, next, shuffle, repeat

### Keybindings
Match spotatui's keybindings for familiarity:
- Navigation: `h/j/k/l`, arrow keys
- Views: `1-6` for quick switching
- Playback: `Space`, `n/p`, `+/-`, `</>`
- Actions: `F` (like), `/` (search), `Q` (queue), `B` (lyrics), `T` (mini)

## Acceptance Criteria

1. ✅ 3-panel layout renders correctly at 80+ columns
2. ✅ Sidebar shows source selector, library sections, playlists placeholder
3. ✅ Content area switches between views
4. ✅ Playbar shows current track info and controls
5. ✅ All keybindings work as documented
6. ✅ Settings screen allows configuration
7. ✅ Help screen shows all keybindings
8. ✅ Responsive: works at 80-200 columns
9. ✅ All 115 existing tests still pass
10. ✅ New tests for UI components

## Estimated Size
- ~800-1200 changed lines (within 10,000 line budget)
- 7-10 new files (components, views, styles)
- 3-5 new test files

## Dependencies
- Existing: textual, rich, playerctl
- New: None (Phase 1 is pure UI, no new dependencies)

## Testing Strategy
- Unit tests for each component
- Integration tests for view switching
- Visual testing with Textual pilot
- Manual testing with real Spotify

## Delivery
- Single PR (within budget)
- Stacked commits: one per component
- All tests green before merge
