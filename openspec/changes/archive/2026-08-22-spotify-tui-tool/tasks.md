# Tasks: Spotify TUI Tool

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 1,100–1,250 authored |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|---|
| 1 | Shell, focus, responsive mouse/keyboard | PR 1 | `.venv/bin/python -m unittest tests.test_shell tests.test_shell_pilot` | Textual pilots at 80x24 and wide; no live services | `src/spotify_tui_tool/ui/layout.py`, shell widgets, bindings, and shell tests |
| 2 | Auth lifecycle, browse states, workers, stable rows | PR 2 | `.venv/bin/python -m unittest tests.test_auth_browse tests.test_web_api tests.test_rows` | Mocked OAuth/API pilots; offline by design | Auth/browse/row files and their tests |
| 3 | Activation and truthful playerctl feedback | PR 3 | `.venv/bin/python -m unittest tests.test_playerctl tests.test_activation tests.test_playback_pilot` | Mocked playerctl scenarios; no live MPRIS | Playback/activation files and regression tests |

## Phase 1: Shell (PR 1)

- [x] 1.1 RED: Add `tests/test_shell.py` and `tests/test_shell_pilot.py` for wide/80x24 composition, focus navigation, every binding, mouse/scroll behavior, transient `q`/`Esc`, truthful help, and responsive pending API input.
- [x] 1.2 GREEN: Update `src/spotify_tui_tool/{app.py,state.py,ui/layout.py,ui/sidebar.py,ui/content.py,ui/playbar.py,ui/views/help.py}` for persistent regions, 22%/16-column layouts, visible focus, and accepted bindings.
- [x] 1.3 REFACTOR: Keep shell behavior deterministic and verify unsupported queue/device/lyrics/streaming actions are absent from help.

## Phase 2: Auth, Browse, and Identity (PR 2)

- [x] 2.1 RED: Add `tests/test_auth_browse.py`, `tests/test_web_api.py`, `tests/test_rows.py`, and `tests/test_browse_pilot.py` for C1 lifecycle/copy, scopes/endpoints/windows, loading/success/empty/error/stale/retry, non-blocking races, duplicate labels, and refresh identity.
- [x] 2.2 GREEN: Update `src/spotify_tui_tool/{models.py,auth.py,web_api.py,state.py,app.py}`, add `src/spotify_tui_tool/ui/{rows.py,states.py}`, and update `src/spotify_tui_tool/ui/views/{login.py,library.py,playlists.py,search.py}` with worker generation/view checks and `BrowseRow(kind,id,uri,...)`.
- [x] 2.3 REFACTOR: Preserve rows during failed refresh, keep browse separate from playback, and prove offline repeatability with `.venv/bin/python -m unittest tests.test_auth_browse tests.test_browse_pilot`.

### Phase 2 gatekeeper correction (bounded retry)

The Phase 2 correction removes the unsupported queue shell route/view and
enforces the read-only Web API/playerctl boundary. RED coverage is recorded in
`tests/test_phase2_gate_corrections.py`; the correction remains offline and
mocked, does not add a task checkbox, and leaves Phase 3 pending.

## Phase 3: Activation and Playback Truth (PR 3)

- [x] 3.1 RED: Add `tests/test_playerctl.py`, `tests/test_activation.py`, and `tests/test_playback_pilot.py`; mock fixed Spotify argv/player, missing binary, no player, and nonzero exit as distinct retryable states with no false success, plus Enter/double-click/non-playable, poll stale, stopped, and failure feedback.
- [x] 3.2 GREEN: Update `src/spotify_tui_tool/{spotify_client.py,app.py,models.py,ui/playbar.py,ui/rows.py}` so activation uses stored URI only and playerctl remains the sole transport authority.
- [x] 3.3 REFACTOR/VERIFY: Run `.venv/bin/python -m unittest` on the bounded suite and record the result; retain last track context, exact wording, and no unsupported capability claims.
