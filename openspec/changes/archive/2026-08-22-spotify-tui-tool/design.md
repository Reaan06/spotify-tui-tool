# Design: Spotatui-like interactive Spotify TUI first slice

## Technical Approach

Extend the existing Textual composition. `AppState` and `ContentArea` are the
routing seam; reusable rows and explicit surface states feed views; workers
perform OAuth/API/playerctl I/O. Widgets render only accepted state. This
preserves `PlayerController`/MPRIS while repairing the current synchronous API
and remount behavior.

## Architecture Decisions

| Area | Decision and rationale |
|---|---|
| Shell | Wide layout is sidebar 22%, content 78%, five-row playbar. At `<=96` columns use a 16-column abbreviated sidebar and four-row playbar; the `80x24` pilot is the minimum, otherwise show a resize message. Semantic Textual CSS and an original dark theme preserve essential controls without pixel-parity claims. |
| Browse | Read-only scopes are `user-read-private user-library-read playlist-read-private playlist-read-collaborative`; use `/me` (1), `/me/tracks` (50), `/me/playlists` (50), and `/search` track/album/artist (20), offset 0. This avoids modify, playback, and pagination claims. |
| Playback | All transport, seek, status, polling, and URI opening delegate to `PlayerController(player_name="spotify")`; no device discovery or Web API fallback. Auth therefore cannot silently change the non-Premium authority. |
| Interaction | `q`/`Esc` pop transient help/login/search; `q` quits only without a back target. Sidebar/playbar click, table/search focus, playable-row double-click, and hovered-region wheel are supported; no drag, queue, or device gestures. |
| Async and identity | Worker results carry a surface generation and view identity; stale results are discarded on the Textual thread. `BrowseRow(kind, id, uri, title, subtitle, playable)` is keyed by `kind:id`; focus stores region and key, never rendered text. |

### Authentication lifecycle (correction C1)

The state machine resolves `authenticated-browse/spec.md:91-95`:

```text
unauthenticated --login--> authenticating --OAuth/API success--> authenticated
       ^                         |                                  |
       | cancel/failure           | failure                          | 401 + refresh failure
       +--------------------------+                                  v
                         invalid/expired <--restore/API reject-- restoring
```

On mount, no token enters `unauthenticated`; persisted credentials enter
`restoring`. Restoration validates the token with `/me`; one refresh is allowed
on 401, then the state becomes `invalid/expired`. Login enters `authenticating`;
OAuth success plus `/me` enters `authenticated`; cancellation/failure returns
to `unauthenticated` or `invalid/expired` with the reason. `r` retries one
restore/validation attempt; Login starts OAuth again. No automatic retry loop.
Copy is: `unauthenticated` “Not signed in. Press Enter to log in.”;
`restoring` “Restoring Spotify session…”; `authenticating` “Waiting for Spotify
login…”; `authenticated` “Signed in as {user}.”; `invalid/expired` “Spotify
session is invalid or expired. Press Enter to log in or r to retry.”

Browse failures retain rows as stale with retry; empty is distinct from error.
Playback states are `fresh`, `stale` after two missed one-second polls,
`stopped`, and `unavailable`. Use “Playback unavailable: no Spotify MPRIS
player is active.” and “Playback failed: {detail}. Try again.” Non-playable
rows say “This item cannot be played through the local player.”

## Data Flow and File Changes

```text
key/mouse → App command → AppState → worker(service)
                              ↓ generation/view check
                         view + playbar state
```

Modify `src/spotify_tui_tool/{models.py,spotify_client.py,auth.py,web_api.py,
state.py,app.py}`, `ui/{layout.py,content.py,sidebar.py,playbar.py,views/*}`;
add/modify mocked unit and Textual pilot tests under `tests/`. `SpotifyWebAPI`
is browse/auth only; activation calls `player.open_uri(row.uri)` only for a
playable row with a URI.

## Testing and Verification Contract (correction C2)

Strict TDD is required: initialization records strict-TDD mode and the exact
runner `.venv/bin/python -m unittest`; each slice writes RED tests first, then
implements GREEN behavior and refactors. Unit tests cover auth lifecycle,
endpoint mapping, identity, states, wording, races, and fixed playerctl argv.
Pilots at `80x24` and wide sizes cover focus, bindings, mouse, scrolling,
non-blocking help, retry, empty/error/stale/success, and keyboard/double-click
activation. The verification phase MUST execute `.venv/bin/python -m unittest`
against the bounded suite and record the command and result. This design makes
no claim that tests currently pass. `sdd-tasks` MUST carry this contract and
the RED cases into every slice.

## Threat Matrix

| Boundary | Applicability and required RED test |
|---|---|
| Documentation-like paths | N/A — no execution classification. |
| Git repository selection | N/A — no VCS automation. |
| Commit state | N/A — no commit automation. |
| Push state | N/A — no push automation. |
| PR commands | N/A — no PR automation. |
| Playerctl subprocess/MPRIS | Applicable — fixed argv/player; missing binary, no player, and nonzero exit map to distinct retryable states; mock each and assert no false success. |

## Migration / Rollout

Session contract: `execution_mode=auto`, `artifact_store.mode=both`,
`delivery_strategy=auto-chain`, `review_budget_lines=1600`. Use three
auto-chain slices, each about 380 authored lines (forecast
1,100–1,250, below the 1,600-line budget): (1) shell/focus/mouse/help/pilots;
(2) auth lifecycle, read-only browse, workers, scopes, windows, and rows;
(3) activation, playerctl-only enforcement, polling states, wording, and
regression pilots. Each is testable and revertible; no migration.

## Traceability and Open Questions

Interactive-shell maps to slice 1; authenticated-browse maps to C1, lifecycle,
states, races, and slice 2; stable-item-activation maps to `BrowseRow` and
slice 3; truthful-playback-feedback maps to the player port and RED subprocess
tests. C2 maps to the proposal acceptance criterion and the `sdd-tasks`/
verification handoff. All product decisions are resolved. No migration is
required.

**Next Step: sdd-tasks**
