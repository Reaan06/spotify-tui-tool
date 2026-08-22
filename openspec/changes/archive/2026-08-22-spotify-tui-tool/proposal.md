# Proposal: Spotatui-like interactive Spotify TUI first slice

## Intent
Make the Python/Textual TUI Spotatui-like for keyboard/mouse browsing while truthful to its backends. Target users are Spotify listeners needing navigation, library/search browsing, and now-playing control without Premium. “Identical” means shared interaction concepts and hierarchy, not pixel parity, copied code/assets, or unsupported features.

## Scope
### In Scope
- Persistent sidebar/content/playbar, Textual theme, focus/selection, keyboard (`h/j/k/l`, arrows, Enter, `/`, Space, `n/p`, `+/-`, `< >`, `?`, Esc, `q`) and mouse activation/scrolling.
- Stable row IDs/URIs for library, playlists, and search; API browsing; auth, loading, empty, error, stale, retry, and success feedback.
- Non-blocking API work, responsive behavior at approximately 80 columns and wider, and playerctl/MPRIS playback commands.
### Out of Scope
Premium/API streaming, device management, queue inspection/mutation, lyrics, cover art, visualizer, alternate sources, plugins, recommendations, pagination/detail pages, and Spotatui assets/source.

## Capabilities
### New Capabilities
- `interactive-shell`: layout, focus, bindings, mouse, responsive degradation.
- `authenticated-browse`: login plus library/playlists/search states.
- `stable-item-activation`: identity-preserving rows mapped to playback.
- `truthful-playback-feedback`: playerctl authority, polling, unavailable/stale/error states.
### Modified Capabilities
- None; no `openspec/specs/` exists, so these are new contracts.
### Capability matrix
| Area | Authority | Boundary |
|---|---|---|
| Navigation/theme | Textual | shell |
| Browse/search | Spotify Web API | async state + rows |
| Play/open/poll | playerctl/MPRIS | transport |
| Queue/like/shuffle/repeat | unproven | surface honestly |

## Business rules and user flows
Tokens do not prove API usability; browsing and playback remain separate. Selecting a row uses its stored URI/ID and `playerctl open`; no Premium claim. Flow: authenticate or explain login → load → browse/select/activate → success or recoverable failure. Polling preserves the last track and labels stale/player-unavailable. API work MUST NOT block Textual.

## Approach and affected areas
Modify `src/spotify_tui_tool/{app.py,spotify_client.py,auth.py,web_api.py,state.py,ui/}` and `tests/`; preserve MPRIS. Review units: (1) shell/focus/responsive; (2) auth/API states and stable rows; (3) activation/playback feedback and pilots. Source/tests are authority. Spotatui was read through public docs, not run locally.

## Acceptance criteria
- [ ] Wide/compact pilots prove composition, keyboard/mouse paths, minimum dimensions, and stable activation.
- [ ] Unit/Textual tests cover auth/loading/empty/error/stale/no-player/API failure and non-blocking success.
- [ ] Help/UI never advertise unsupported features; init records strict TDD and verified `.venv/bin/python -m unittest` passes the bounded suite.

## Review workload forecast
Mode auto; stores both; delivery auto-chain. Budget: 1,600 lines; guard: 400. Estimate ~900–1,200 authored lines: High risk. `Decision needed before apply: No`; `Chained PRs recommended: Yes`; `400-line budget risk: High`. Auto-chain testable, rollbackable slices.

## Risks
Async races, breakpoints, API limits, and absent MPRIS can mislead users. Mitigate with states, mocks/pilots, and capability boundaries.

## Rollback Plan
Revert slices in reverse order; no migration.

## Dependencies
Source/tests, explorations, Textual/playerctl; Spotify checks opt-in.
