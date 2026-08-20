# Tasks: spotatui Integration Phase 1 — UI Framework

## Task List

### T1: State Manager (Foundation)
**Files**: `src/spotify_tui_tool/state.py`
**Tests**: `tests/test_state.py`
**Estimate**: ~80 lines

- [ ] Create `AppState` dataclass with all state fields
- [ ] Add methods to update state (set_view, set_playing, etc.)
- [ ] Write unit tests for state management
- [ ] Verify all tests pass

### T2: Config Manager
**Files**: `src/spotify_tui_tool/config.py`
**Tests**: `tests/test_config.py`
**Estimate**: ~100 lines

- [ ] Create `Config` dataclass with defaults
- [ ] Implement `load()` from YAML file
- [ ] Implement `save()` to YAML file
- [ ] Add config validation
- [ ] Write unit tests for config
- [ ] Verify all tests pass

### T3: Layout Manager
**Files**: `src/spotify_tui_tool/ui/__init__.py`, `src/spotify_tui_tool/ui/layout.py`
**Tests**: `tests/test_layout.py`
**Estimate**: ~120 lines

- [ ] Create 3-panel layout structure
- [ ] Add responsive breakpoints
- [ ] Implement pane resizing
- [ ] Write integration tests
- [ ] Verify layout renders correctly

### T4: Sidebar Component
**Files**: `src/spotify_tui_tool/ui/sidebar.py`
**Tests**: `tests/test_sidebar.py`
**Estimate**: ~150 lines

- [ ] Create sidebar with sections (Sources, Library, Playlists)
- [ ] Implement vim-style navigation (j/k)
- [ ] Add selection highlighting
- [ ] Emit events on selection change
- [ ] Write unit tests
- [ ] Verify sidebar renders correctly

### T5: Playbar Component
**Files**: `src/spotify_tui_tool/ui/playbar.py`
**Tests**: `tests/test_playbar.py`
**Estimate**: ~180 lines

- [ ] Create playbar layout (track-info, progress, volume, controls)
- [ ] Implement progress bar with time display
- [ ] Add volume indicator
- [ ] Add control indicators (shuffle, repeat)
- [ ] Implement real-time updates (1s interval)
- [ ] Write unit tests
- [ ] Verify playbar renders correctly

### T6: Content Area
**Files**: `src/spotify_tui_tool/ui/content.py`
**Tests**: `tests/test_content.py`
**Estimate**: ~100 lines

- [ ] Create content area container
- [ ] Implement view switching
- [ ] Add view lifecycle management
- [ ] Write integration tests
- [ ] Verify view switching works

### T7: Home View
**Files**: `src/spotify_tui_tool/ui/views/home.py`
**Tests**: `tests/test_views_home.py`
**Estimate**: ~80 lines

- [ ] Create home view with "Recently Played" section
- [ ] Add placeholder track table
- [ ] Write unit tests
- [ ] Verify view renders correctly

### T8: Library View
**Files**: `src/spotify_tui_tool/ui/views/library.py`
**Tests**: `tests/test_views_library.py`
**Estimate**: ~120 lines

- [ ] Create library view with liked songs table
- [ ] Add columns: #, Title, Artist, Album, Duration
- [ ] Implement row selection
- [ ] Write unit tests
- [ ] Verify view renders correctly

### T9: Playlists View
**Files**: `src/spotify_tui_tool/ui/views/playlists.py`
**Tests**: `tests/test_views_playlists.py`
**Estimate**: ~80 lines

- [ ] Create playlists view with playlist list
- [ ] Add placeholder message "No playlists"
- [ ] Write unit tests
- [ ] Verify view renders correctly

### T10: Search View
**Files**: `src/spotify_tui_tool/ui/views/search.py`
**Tests**: `tests/test_views_search.py`
**Estimate**: ~150 lines

- [ ] Create search view with input field
- [ ] Add tabs for Tracks, Albums, Artists
- [ ] Implement search input handling
- [ ] Write unit tests
- [ ] Verify view renders correctly

### T11: Queue View
**Files**: `src/spotify_tui_tool/ui/views/queue.py`
**Tests**: `tests/test_views_queue.py`
**Estimate**: ~100 lines

- [ ] Create queue view with current queue list
- [ ] Add placeholder message "Queue empty"
- [ ] Write unit tests
- [ ] Verify view renders correctly

### T12: Settings View
**Files**: `src/spotify_tui_tool/ui/views/settings.py`
**Tests**: `tests/test_views_settings.py`
**Estimate**: ~120 lines

- [ ] Create settings view with configuration options
- [ ] Add keybinding reference section
- [ ] Add toggle options (shuffle, repeat)
- [ ] Write unit tests
- [ ] Verify view renders correctly

### T13: Help View
**Files**: `src/spotify_tui_tool/ui/views/help.py`
**Tests**: `tests/test_views_help.py`
**Estimate**: ~100 lines

- [ ] Create help view with keybinding table
- [ ] Make table scrollable
- [ ] Write unit tests
- [ ] Verify view renders correctly

### T14: Refactor App
**Files**: `src/spotify_tui_tool/app.py`
**Tests**: `tests/test_app.py` (update existing)
**Estimate**: ~200 lines

- [ ] Integrate layout manager
- [ ] Add all keybindings
- [ ] Wire sidebar to content switching
- [ ] Wire playbar to player controller
- [ ] Update existing tests
- [ ] Verify all tests pass

### T15: CSS Styling
**Files**: `src/spotify_tui_tool/ui/layout.tcss`
**Tests**: Visual verification
**Estimate**: ~150 lines

- [ ] Create CSS file for layout
- [ ] Style sidebar
- [ ] Style playbar
- [ ] Style content area
- [ ] Verify visual appearance

### T16: Integration Testing
**Files**: `tests/test_integration_ui.py`
**Tests**: Integration tests
**Estimate**: ~150 lines

- [ ] Test full app flow
- [ ] Test view switching via keybindings
- [ ] Test playback controls
- [ ] Test responsive layout
- [ ] Verify all tests pass

### T17: Documentation
**Files**: `README.md` (update)
**Estimate**: ~50 lines

- [ ] Update README with new features
- [ ] Add keybinding reference
- [ ] Add screenshots (optional)
- [ ] Verify documentation is accurate

## Task Dependencies

```
T1 (State) → T2 (Config) → T3 (Layout) → T4 (Sidebar)
                                  ↓
                            T5 (Playbar)
                                  ↓
                            T6 (Content) → T7-T13 (Views)
                                  ↓
                            T14 (Refactor App)
                                  ↓
                            T15 (CSS) → T16 (Integration) → T17 (Docs)
```

## Parallel Execution Opportunities

- T1, T2 can run in parallel (no dependencies)
- T7, T8, T9, T10, T11, T12, T13 can run in parallel (views are independent)
- T15, T16 can run in parallel (styling and testing)

## Estimated Total

- **Total tasks**: 17
- **Total lines**: ~1,830
- **Estimated time**: 4-6 hours (automated)
- **Changed files**: ~20 new, ~3 modified
- **Test files**: ~15 new, ~1 modified

## Risk Mitigation

- Each task is independently testable
- Tasks can be committed incrementally
- All existing tests must pass after each task
- Visual verification at each milestone
