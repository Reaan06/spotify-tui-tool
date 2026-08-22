# Truthful Playback Feedback Specification

## Purpose

Define the non-Premium playback boundary: playerctl/MPRIS is authoritative for
commands and current-track polling, while the Spotify Web API remains a browse
source. The UI MUST distinguish unavailable, stale, stopped, and successful
playback states.

**Traceability:** Proposal `Capabilities > New Capabilities > truthful-playback-feedback`,
`Capability matrix`, `Business rules and user flows`, and the exploration
recommendation to preserve playerctl as the default authority.

## Requirements

### Requirement: Playerctl/MPRIS authority and capabilities

Play, pause/play-pause, next, previous, volume, seek, status, and URI opening
MUST route through the supported playerctl/MPRIS boundary. The application MUST
NOT claim Premium/API streaming, device control, queue mutation/inspection, or
other unproven capabilities. Missing playerctl, no active Spotify MPRIS player,
and command failure MUST produce distinct honest, recoverable feedback.

#### Scenario: Successful command

- GIVEN a mocked available Spotify MPRIS player
- WHEN the user invokes a supported playback binding
- THEN the player boundary receives the corresponding command and success is reported

#### Scenario: Unavailable transport

- GIVEN playerctl is missing or no Spotify MPRIS player is active
- WHEN a playback command or row activation is attempted
- THEN the UI reports unavailable playback and does not report success or API streaming

### Requirement: Current-track polling and stale semantics

The application MUST poll current-track metadata and playback status at the
existing approximately one-second cadence without blocking the Textual event
loop. A successful poll MUST update the playbar. After one missed poll, the last
known track MAY remain visible as fresh; after two consecutive missed polls it
MUST be marked stale. No known track MUST be represented as stopped/empty or
player-unavailable according to the observed transport result.

#### Scenario: Poll success and failure

- GIVEN mocked metadata/status responses followed by two transport failures
- WHEN successive polls run
- THEN the first missed poll retains the current result and the second consecutive miss marks it stale

#### Scenario: No player versus stopped player

- GIVEN one poll reports no active player and another reports an active stopped player
- WHEN each result is rendered
- THEN the UI distinguishes player-unavailable from stopped/empty playback

### Requirement: Honest action feedback and verification

Playback success, failure, stale, and unavailable feedback MUST be visible
without destroying navigation or the last trustworthy track context. Help and
controls MUST expose only supported actions and MUST label unavailable actions
honestly. Unit tests MUST mock playerctl/MPRIS for command mapping, missing
binary, no-player, and command failure; Textual pilots MUST cover control and
feedback paths. Live playerctl checks MAY run only through explicit opt-in tests.

#### Scenario: Recoverable playback failure

- GIVEN a command failure after a known track was displayed
- WHEN the command returns an error
- THEN the last track context remains intact and a retryable failure is shown

#### Scenario: Deterministic no-player suite

- GIVEN mocked playerctl outcomes and no live desktop player
- WHEN the bounded tests run
- THEN unavailable/stale mappings and supported command payloads are reproducible

## Explicit non-goals

The first slice MUST NOT implement Premium/API streaming, device management,
real queue mutation or inspection, lyrics, cover art, visualizers, alternate
sources, plugins, recommendations, detail-page or pagination breadth, or
copied Spotatui assets/source. Interaction acceptance proves command, focus,
state, and feedback parity—not exact pixels or unsupported feature parity.

## Open product decisions

The exact player name selection, unavailable-message wording, and any future
capability discovery policy remain unresolved. The stale threshold is two
consecutive missed polls and MUST remain aligned with the implementation.
