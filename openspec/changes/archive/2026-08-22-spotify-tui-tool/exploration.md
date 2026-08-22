# Exploration: Spotatui-like Spotify TUI

## Exploration: spotify-tui-tool

### Current State

The repository contains a Python 3.10+ Textual application with a thin, typed
`playerctl`/MPRIS wrapper and a newer, partially integrated Spotify Web API
authentication layer. The current implementation is materially beyond the
earlier MVP artifacts, so the source tree and current tests are the authority.
The working tree also contains uncommitted authentication/API changes; these
must be treated as current work in progress rather than as completed behavior.

The application currently works as follows:

- `src/spotify_tui_tool/app.py` composes a `Header`, `LayoutManager`, and
  `Footer`; on mount it mounts `Sidebar`, `ContentArea`, and `Playbar`, starts a
  one-second polling timer, and checks for saved OAuth tokens.
- `src/spotify_tui_tool/ui/layout.py` provides a fixed three-part arrangement:
  approximately 20% sidebar, 80% content, and a six-row bottom playbar. The
  configured width/height values are displayed by Settings but are not fully
  applied to the stylesheet or responsive breakpoints.
- `src/spotify_tui_tool/ui/content.py` swaps one widget at a time rather than
  maintaining a screen stack. The implemented view map contains Home, Library,
  Playlists, Search, Queue, Settings, Help, and Login.
- `src/spotify_tui_tool/ui/sidebar.py` renders source placeholders, library
  placeholders, a playlist placeholder, and Login. It has keyboard selection
  movement and hover CSS, but the indexed source does not show a complete click
  activation path from a `SidebarItem` to application view navigation.
- `src/spotify_tui_tool/ui/playbar.py` renders text for track, progress, volume,
  shuffle, and repeat. Playback controls are application key actions; the
  playbar is not yet a complete set of mouse-activated controls.
- `src/spotify_tui_tool/now_playing.py` performs three sequential playerctl
  calls (`metadata`, `position`, and `status`) and preserves the last known
  track after failures. `PlayerController` maps play/pause/next/previous,
  volume, seek, status, and `open` to playerctl commands. This is the strongest
  available non-Premium playback boundary.
- `src/spotify_tui_tool/auth.py` implements a localhost PKCE callback and token
  persistence under `~/.config/spotify-tui-tool/tokens.json`. `web_api.py`
  exposes current-user, liked-songs, playlists, search, and playback endpoints.
  The API layer can browse data, but the current app creates `SpotifyClient`
  without passing the API instance into it. Authentication state in the app and
  playback transport selection in `SpotifyClient` are therefore disconnected.
- Library and playlist views can receive API payloads, but their rows do not
  retain stable track/album/playlist identities. Search computes a track URI
  and then discards it, and no complete row activation path is present. The
  current search result selection method returns displayed text rather than a
  URI.
- Queue display is intentionally limited: `SpotifyClient.get_queue()` returns
  at most the current track because playerctl/MPRIS does not expose the full
  Spotify queue through the current wrapper. `AppState` has local queue methods,
  but they are not connected to a real queue transport.
- Like/unlike is still a status-message stub. Shuffle and repeat exist as
  state fields and playbar indicators, but a verified end-to-end control path is
  not present.
- Feedback is mostly a status string written into the playbar controls area.
  API calls in the search handler are synchronous, and broad exception
  handling can hide lifecycle errors. Loading, empty, stale, and retry states
  are not consistently modeled per view.

The current test evidence is important for scope: `324` tests ran with `3`
failures, `30` errors, and `7` skips. The failures include stale expectations
for URI search and the additional Login view/sidebar item. Login tests fail
because `LoginView` has no `compose()` method and its CSS contains an invalid
`margin: 0 auto` declaration for the installed Textual version. The local
runtime also has `playerctl 2.4.1`, but no active Spotify MPRIS player at
exploration time (`playerctl --player=spotify status` reported “No players
found”). Compilation succeeds.

#### Public Spotatui evidence

The public reference is `LargeModGames/spotatui` on GitHub, not the nonexistent
`spotatui/spotatui` path. Its README and keybinding/configuration documents
show the interaction model that is reasonable to reproduce conceptually:

- a source/device-aware TUI with a persistent content area and playbar;
- `Space`, `n`, `p`, `+`/`-`, and `<`/`>` for playback;
- vim navigation with `h`/`j`/`k`/`l`, `Enter` for activation, `/` for search,
  `?` for help, and `q` for back/quit;
- contextual actions such as `a`/`A` for album/artist navigation, `d` for
  source/device selection, `z` for queueing, `Q` for queue, `F` for like,
  `B` for lyrics, and `T` for a miniplayer;
- configurable keybindings, live settings filtering, persisted layout sizes,
  responsive search placement, and mouse hit-testing that follows layout
  arrangement.

These are behavioral references, not a mandate to copy code, proprietary
assets, logo art, screenshots, or exact visual design. Spotatui's current
native streaming, cross-source playback, queue engine, lyrics, visualizer,
plugins, and device model are materially different from this project's
playerctl/MPRIS boundary. Its README explicitly states that Spotify Web API
playback requires Premium, while browsing can work for a free account; this
supports keeping local playerctl playback as the default authority in the first
slice.

Evidence links:

- https://github.com/LargeModGames/spotatui
- https://raw.githubusercontent.com/LargeModGames/spotatui/main/docs/keybindings.md
- https://raw.githubusercontent.com/LargeModGames/spotatui/main/docs/configuration.md
- https://raw.githubusercontent.com/LargeModGames/spotatui/main/README.md

Exact current pixel layout, all mouse hitboxes, and version-specific screen
details remain evidence gaps because the reference was inspected through public
repository/documentation endpoints rather than run locally in this session.

### Affected Areas

- `src/spotify_tui_tool/app.py` — application lifecycle, command routing,
  polling, auth restoration, search submission, and status feedback.
- `src/spotify_tui_tool/spotify_client.py` — must define the authority and
  capability boundary between playerctl playback and authenticated API data.
- `src/spotify_tui_tool/playerctl.py` and `src/spotify_tui_tool/now_playing.py`
  — existing MPRIS control and polling boundary for non-Premium playback and
  now-playing state.
- `src/spotify_tui_tool/auth.py` and `src/spotify_tui_tool/web_api.py` — OAuth
  lifecycle, token refresh, browse/search operations, and API error mapping.
- `src/spotify_tui_tool/state.py` — current-view, focus, selection, playback,
  queue, and history state; it is a candidate single source of truth but is not
  consistently wired to widgets today.
- `src/spotify_tui_tool/ui/layout.py`, `ui/content.py`, `ui/sidebar.py`, and
  `ui/playbar.py` — responsive composition, focus/navigation, keyboard/mouse
  affordances, and now-playing presentation.
- `src/spotify_tui_tool/ui/views/login.py` — currently incomplete composition
  and therefore a prerequisite for reliable authenticated browsing.
- `src/spotify_tui_tool/ui/views/search.py`, `library.py`, `playlists.py`, and
  `queue.py` — row identity, activation, loading/empty/error states, and the
  capability-limited data views.
- `tests/` — existing unittest/Textual pilot coverage, currently exposing the
  Login composition/CSS regression and stale contracts. The project context
  records `.venv/bin/python -m unittest` as the practical runner; live Spotify
  integration must remain optional.
- `README.md`, `pyproject.toml`, and configuration paths — documentation and
  dependency/configuration truth must be updated only after behavior is
  stabilized.

### Approaches

1. **Bounded vertical slice over the existing Textual architecture** — repair
   composition and state/event contracts, introduce stable row identities, and
   implement one coherent keyboard/mouse flow from navigation to data loading
   to playerctl playback.
   - Pros: preserves tested code and the working MPRIS boundary; makes the
     current failures visible and fixable; supports incremental visual parity.
   - Cons: the existing widget-remount model and broad exception handling need
     cleanup before deeper parity work; exact Spotatui feature breadth remains
     out of scope.
   - Effort: Medium

2. **Rewrite around a centralized event/state architecture before adding
   features** — replace ad hoc app-to-widget updates with explicit commands,
   capability-aware services, focus state, and reusable track/table models.
   - Pros: better long-term testability and a clearer path to multiple screens,
     mouse activation, loading states, and alternate backends.
   - Cons: high regression and review risk; delays visible improvements; would
     duplicate much of the existing Textual layout and test surface.
   - Effort: High

3. **Pursue full Spotatui feature parity immediately** — add API playback,
   device management, real queue mutation, lyrics, cover art, visualizer,
   alternate sources, and plugin-like extensibility together.
   - Pros: closest theoretical feature match.
   - Cons: contradicts the current playerctl/non-Premium goal, assumes Premium
     and unavailable capabilities, creates a large unreviewable change, and
     makes behavior impossible to validate consistently without live services.
   - Effort: Very high

### Recommendation

Choose Approach 1 and define the first implementation slice as **interactive
navigation plus authenticated read-only browsing with playerctl-controlled
playback**. The slice should:

1. Restore a valid Login view and explicit auth/loading/error states, without
   treating the presence of a token file as proof that the API is usable.
2. Establish a capability-aware service boundary: Spotify Web API is used for
   current user, liked songs, playlists, and track/album/artist search;
   playerctl/MPRIS remains the default playback authority. Activating a
   playable Spotify track should preserve the existing `playerctl open` path
   unless a future change explicitly chooses Premium/device semantics.
3. Give every displayed row a stable internal identity and URI/ID, so Enter,
   double-click or the agreed mouse gesture, and a future `z` queue action act
   on the item rather than on rendered text. Track search must not discard its
   URI.
4. Make the sidebar, content tables, search input, and playbar controls share a
   deliberate focus/selection model. Support the useful Spotatui subset:
   `h/j/k/l`, arrows, `Enter`, `/`, `Space`, `n`, `p`, `+`/`-`, `<`/`>`, `?`,
   `Esc`, and `q`; expose bindings through help rather than silently claiming
   unsupported actions.
5. Add mouse support for sidebar activation, table row activation, playbar
   controls, scrolling, and search focus. Hover styling alone is not sufficient
   evidence of mouse interactivity.
6. Define responsive behavior for the supported terminal range, with an
   explicitly tested minimum around 80 columns and a compact breakpoint that
   avoids clipping the sidebar, tables, and playbar. Treat exact Spotatui
   proportions as a visual target, not an invariant.
7. Keep the one-second now-playing refresh, but represent loading, stale data,
   player-unavailable, API failure, empty results, and successful action
   feedback as non-destructive states. Do not block the Textual event loop with
   network requests; use workers or an equivalent boundary and test both
   success and failure transitions.
8. Test pure data/command mapping with unittest mocks, Textual pilot flows at
   compact and wide terminal sizes, row identity/activation, and no-player/API
   failure. Keep live Spotify/playerctl checks explicitly opt-in.

The first slice should be judged by interaction contracts and capability
truthfulness, not by visual screenshots alone. Once it is stable, a later
proposal can independently evaluate playlist detail, real queue support,
device selection, cover art, lyrics, or other parity features.

#### Explicit non-goals for the first slice

- Native Spotify streaming, Spotify Connect device management, or API playback
  as the default transport.
- Full queue inspection or mutation through playerctl; a local queue is not a
  substitute for the Spotify queue unless its semantics are explicitly named.
- Playlist/album/artist detail pages, pagination beyond the bounded data window,
  recommendations, recently played, podcasts, or listening statistics.
- Lyrics, cover-art/image protocols, audio visualization, alternate sources,
  plugins, AI DJ, recap/history parity, or source switching.
- Copying Spotatui's proprietary-looking visual assets, logo, demo media, or
  source code. Reproduce interaction concepts and implement an original
  Textual theme.
- The claim that the Python application will be visually or behaviorally
  identical to a moving upstream Rust application. “As close as practical”
  remains the target, bounded by this project's backend and licensing limits.

### Risks

- Spotify API policy, endpoint availability, scopes, rate limits, and Premium
  requirements can change; browsing and playback capabilities must be modeled
  separately and surfaced honestly.
- The current app's API/auth state is disconnected from `SpotifyClient`, so an
  apparently small playback change could accidentally switch transport or
  break the non-Premium SpotX workflow.
- `playerctl` behavior depends on the desktop client, MPRIS registration, D-Bus,
  and the active player name. The current environment has no active player, so
  live playback claims cannot be verified here.
- Textual focus, async workers, dynamic widget replacement, and mouse events
  can introduce race conditions and stale widget references. Pilot tests should
  cover view transitions and delayed responses.
- The current synchronous Web API handler can freeze the TUI, while broad
  exception handling can conceal errors. Introducing explicit state transitions
  is necessary before adding more screens.
- Responsive tables and a persistent playbar compete for limited terminal
  height. The minimum supported dimensions and degradation rules must be
  specified before visual polish.
- Existing prior MVP/Spotatui artifacts describe planned or now-stale behavior;
  proposal/spec work must cite the current source and current failing tests,
  not blindly extend those documents.

### Ready for Proposal

Yes. The next phase should create a bounded proposal for the interactive
navigation/authenticated-browsing/playerctl-playback slice, including a
capability matrix, explicit non-goals, an incremental test plan, and a review
split if the resulting UI work exceeds the configured review budget. No
production implementation is part of this exploration.
