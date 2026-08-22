# Stable Item Activation Specification

## Purpose

Ensure displayed library, playlist, and search rows retain identity from API
payload through selection and playback activation. Actions MUST operate on
stored item identity, never on rendered labels.

**Traceability:** Proposal `Capabilities > New Capabilities > stable-item-activation`,
the capability matrix boundary between Spotify Web API and playerctl, and the
exploration finding that current rows discard track URIs.

## Requirements

### Requirement: Stable row identity

Every displayed row MUST carry a stable internal identity and the source
identifier available for its type (track, album, artist, playlist, or library
entry). Playable track rows MUST retain a valid Spotify URI and/or track ID from
the API payload through redraw, sorting, refresh, selection, and focus changes.
Rendered text MUST NOT be the identity or the activation payload.

#### Scenario: Duplicate labels remain distinct

- GIVEN two API tracks with the same title and artist but different IDs/URIs
- WHEN both rows are rendered and selected in turn
- THEN each selection retains and exposes its own original identity

#### Scenario: Refresh preserves identity mapping

- GIVEN a selected track row and a refreshed result containing that track
- WHEN the view redraws
- THEN the corresponding row still maps to the same ID/URI rather than its display position alone

### Requirement: Enter and double-click activation

Pressing `Enter` on a focused playable row MUST invoke activation with that row’s
stored URI/ID. A double-click on the row MUST invoke the same activation path.
The application MUST report success or a recoverable playback failure without
claiming that API browsing started playback. Non-playable rows MUST receive an
explicit unavailable outcome rather than an invented URI.

#### Scenario: Keyboard activation uses stored URI

- GIVEN a selected search result whose displayed title differs from its URI
- WHEN the user presses `Enter`
- THEN the playback boundary receives the stored URI exactly

#### Scenario: Mouse activation matches keyboard activation

- GIVEN a playable row with a stable identity
- WHEN the user double-clicks it
- THEN the same activation command and feedback contract as `Enter` is used

#### Scenario: Non-playable item

- GIVEN a row without a playable Spotify URI
- WHEN the user activates it
- THEN no fabricated command is issued and the UI reports that activation is unavailable

### Requirement: Identity and activation tests

Unit tests MUST cover parsing and preservation of IDs/URIs, duplicate labels,
refresh mapping, and exact activation payloads. Textual pilots MUST cover both
keyboard and double-click activation with mocked playback, including failure
feedback. Tests MUST be deterministic and MUST NOT require a live Spotify
account or active player.

#### Scenario: Mocked activation proof

- GIVEN a fixed API payload and mocked player controller
- WHEN pilot tests activate a row by keyboard and mouse
- THEN the mock records the expected stored URI/ID and the UI reports the mapped result

## Scope boundary

This slice does not define playlist/album/artist detail pages, pagination
breadth, real queue mutation or inspection, recommendations, or alternate
playback sources. Any future queue action MUST use an explicitly defined
identity contract rather than treating the local queue as Spotify’s queue.
