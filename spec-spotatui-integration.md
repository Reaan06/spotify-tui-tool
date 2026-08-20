# Spec: spotatui Integration Phase 1 — UI Framework

## Requirements

### R1: 3-Panel Layout
- The app SHALL display a 3-panel layout: Sidebar (left), Content (center), Playbar (bottom)
- The sidebar SHALL occupy 20% of terminal width (configurable)
- The playbar SHALL occupy 6 rows height (configurable)
- The layout SHALL be responsive at 80-200 columns

### R2: Sidebar Component
- The sidebar SHALL display a source selector (Spotify, Local, Radio)
- The sidebar SHALL display library sections: Liked Songs, Albums, Artists
- The sidebar SHALL display a playlists placeholder (list with "No playlists" message)
- The sidebar SHALL highlight the currently selected item
- The sidebar SHALL support vim-style navigation (j/k)

### R3: Content Area
- The content area SHALL display different views based on sidebar selection
- Supported views: Home, Library, Playlists, Search, Queue, Settings, Help
- Each view SHALL render appropriate content (tables, lists, forms)
- Views SHALL be switchable via sidebar selection or keybindings (1-6)

### R4: Playbar Component
- The playbar SHALL display current track info: artist — title
- The playbar SHALL display album name
- The playbar SHALL display a progress bar with current/total time
- The playbar SHALL display volume level
- The playbar SHALL display control indicators (shuffle, repeat status)
- The playbar SHALL update in real-time (1s interval)

### R5: Keybindings
- Navigation: h/j/k/l, arrow keys
- Views: 1-6 for quick switching
- Playback: Space (play/pause), n/p (next/prev), +/- (volume), </> (seek)
- Actions: F (like), / (search), Q (queue), B (lyrics placeholder), T (mini placeholder)
- Modal: Esc (back), q (quit), ? (help)

### R6: Settings Screen
- The settings screen SHALL display current configuration
- The settings screen SHALL allow toggling options (shuffle, repeat)
- The settings screen SHALL show keybinding reference

### R7: Help Screen
- The help screen SHALL display all available keybindings
- The help screen SHALL be scrollable
- The help screen SHALL be accessible via ? key

## Acceptance Criteria

### AC1: Layout
- [ ] Given terminal width >= 80 columns
- [ ] When the app starts
- [ ] Then sidebar occupies ~20% width
- [ ] And content occupies ~60% width
- [ ] And playbar occupies bottom 6 rows

### AC2: Sidebar Navigation
- [ ] Given the app is running
- [ ] When user presses j/k in sidebar
- [ ] Then selection moves down/up
- [ ] And content area updates to reflect selection

### AC3: View Switching
- [ ] Given the app is running
- [ ] When user presses 1-6
- [ ] Then the corresponding view is displayed
- [ ] And the sidebar selection updates

### AC4: Playbar Display
- [ ] Given Spotify is playing a track
- [ ] When the app renders
- [ ] Then playbar shows "Artist — Title"
- [ ] And progress bar shows current position
- [ ] And volume shows current level

### AC5: Keybindings Work
- [ ] Given the app is running
- [ ] When user presses Space
- [ ] Then playback toggles (play/pause)
- [ ] And status bar shows feedback

### AC6: Settings Accessible
- [ ] Given the app is running
- [ ] When user presses Alt-, or clicks Settings
- [ ] Then settings screen is displayed
- [ ] And settings can be navigated

### AC7: Help Accessible
- [ ] Given the app is running
- [ ] When user presses ?
- [ ] Then help screen is displayed
- [ ] And all keybindings are listed

## Component Specifications

### Sidebar
```
┌─────────────────┐
│ Sources         │
│  ▶ Spotify      │
│    Local        │
│    Radio        │
├─────────────────┤
│ Library         │
│  ♥ Liked Songs  │
│  ♪ Albums       │
│  ♫ Artists      │
├─────────────────┤
│ Playlists       │
│  (No playlists) │
└─────────────────┘
```

### Playbar
```
┌─────────────────────────────────────────────────────────────┐
│ ▶ Artist — Title                                            │
│   Album Name                                                │
│   ████████████████░░░░ 1:23/3:45  Vol: 75%  ♪ shuffle ⟲ off │
└─────────────────────────────────────────────────────────────┘
```

### Content Views
- **Home**: "Recently Played" table (placeholder)
- **Library**: Track table with columns: #, Title, Artist, Album, Duration
- **Playlists**: Playlist list with name, track count
- **Search**: Input field + results tabs
- **Queue**: Current queue list
- **Settings**: Configuration options
- **Help**: Keybinding reference

## Keybinding Reference

| Key | Action | Category |
|-----|--------|----------|
| Space | Play/Pause | Playback |
| n | Next track | Playback |
| p | Previous track | Playback |
| + | Volume up | Playback |
| - | Volume down | Playback |
| < | Seek backward | Playback |
| > | Seek forward | Playback |
| F | Like/Unlike | Action |
| / | Search | Navigation |
| 1 | Home view | Navigation |
| 2 | Library view | Navigation |
| 3 | Playlists view | Navigation |
| 4 | Search view | Navigation |
| 5 | Queue view | Navigation |
| 6 | Settings view | Navigation |
| j | Move down | Navigation |
| k | Move up | Navigation |
| h | Move left (sidebar) | Navigation |
| l | Move right (content) | Navigation |
| Esc | Back | Navigation |
| q | Quit | System |
| ? | Help | System |

## Layout Specifications

### Minimum Terminal Size
- Width: 80 columns
- Height: 24 rows

### Responsive Breakpoints
- Small: 80-120 columns (compact layout)
- Medium: 121-150 columns (standard layout)
- Large: 151+ columns (wide layout, more columns in tables)

### Color Scheme
- Use Textual default theme (dark)
- Primary color: Cyan
- Accent color: Green
- Error color: Red
- Dim color: Gray
