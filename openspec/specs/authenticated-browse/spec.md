# Authenticated Browse Specification

## Purpose

Define login restoration and read-only Spotify Web API browsing for the current
user, liked/library items, playlists, and search. Browsing capability MUST stay
separate from playback capability and MUST remain honest about token usability.

**Traceability:** Proposal `Capabilities > New Capabilities > authenticated-browse`,
`Business rules and user flows`, and the exploration recommendation for explicit
auth/API states.

## Requirements

### Requirement: Explicit authentication lifecycle

The application MUST provide a usable login state and MUST restore persisted
authentication asynchronously. A token file or token presence MUST NOT be
treated as proof that the API is usable. The UI MUST distinguish unauthenticated,
restoring/authenticating, authenticated, and invalid/expired states, explain
recoverable failures, and provide an explicit retry or login action.

#### Scenario: Valid restoration

- GIVEN persisted credentials that the mocked API accepts
- WHEN the application restores authentication
- THEN it reaches authenticated state and begins the requested browse load

#### Scenario: Invalid restoration

- GIVEN persisted credentials rejected by the mocked API
- WHEN restoration completes
- THEN the UI shows an actionable authentication error and offers login/retry without claiming success

### Requirement: Observable browse states

Each browse/search surface MUST expose loading, success, empty, error, stale,
and retryable outcomes without blocking or destroying the persistent shell.
Successful data MUST remain visible while a refresh is pending or when a
recoverable refresh fails, with a stale indication that is distinguishable from
fresh success. Empty results MUST be distinct from errors. The bounded first
slice MAY display only the returned data window; pagination breadth is out of
scope.

#### Scenario: Success, empty, and failure

- GIVEN an authenticated mocked API
- WHEN a request returns items, no items, or a recoverable error
- THEN the surface shows respectively success rows, an explicit empty state, or an error with retry

#### Scenario: Refresh preserves stale data

- GIVEN a previously successful result and a failed refresh
- WHEN the refresh response fails or becomes outdated
- THEN prior data remains visible with stale/retry feedback and is not presented as fresh

### Requirement: Non-blocking and race-safe API interaction

Spotify API and authentication operations MUST execute outside the Textual event
loop. The shell MUST continue handling input, focus, and redraw while work is
pending. A late response MUST NOT overwrite a newer request or a view that is
no longer active; every terminal outcome MUST be represented as success, empty,
error, or stale state.

#### Scenario: Input remains responsive during API work

- GIVEN a mocked request that does not complete immediately
- WHEN the user moves focus or opens help
- THEN those interactions complete before the request resolves

#### Scenario: Out-of-order responses

- GIVEN two requests for the same surface where the older request resolves last
- WHEN both responses arrive
- THEN only the newest request controls displayed data and state

### Requirement: Deterministic browse verification

Unit tests MUST mock authentication and API responses for every lifecycle state.
Textual pilot tests MUST cover login restoration, retry, loading, empty,
error/stale, and successful browse flows without network access. Live Spotify
checks MAY exist only as explicit opt-in tests and MUST NOT be required for the
bounded suite.

#### Scenario: Offline repeatability

- GIVEN fixed mocked authentication/API responses
- WHEN the bounded test suite runs repeatedly
- THEN it produces the same state and row outcomes without credentials or network access

## Open product decisions

OAuth scopes, exact endpoint data limits, stale timeout, and user-facing copy
are not fixed by the proposal. Design/apply MUST resolve and document them;
this specification does not silently assume values.
