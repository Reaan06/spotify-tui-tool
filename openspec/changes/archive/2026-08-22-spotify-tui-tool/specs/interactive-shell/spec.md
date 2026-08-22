# Interactive Shell Specification

## Purpose

Define the bounded Spotatui-like interaction shell: persistent regions, focus,
responsive degradation, truthful bindings, and mouse behavior. This is an
original Textual interaction contract, not a pixel-copy contract.

**Traceability:** Proposal `Capabilities > New Capabilities > interactive-shell`,
`Scope > In Scope`, `Acceptance criteria`, and the exploration recommendation
for compact/wide pilots.

## Requirements

### Requirement: Persistent responsive shell

The application MUST keep a sidebar, content region, and playbar present while
views and data states change. It MUST remain usable at approximately 80 columns
and at a wider terminal size, with no clipped essential controls or overlapping
regions. Compact behavior MUST degrade deliberately (for example by reducing
sidebar presentation) rather than silently losing navigation. Exact breakpoint
and proportions remain a product decision for design; they MUST be recorded and
tested before implementation is accepted.

#### Scenario: Wide composition

- GIVEN a wide pilot terminal
- WHEN the application mounts and a view changes
- THEN sidebar, content, and playbar remain composed and independently usable

#### Scenario: Compact composition

- GIVEN a pilot terminal near 80 columns
- WHEN the application mounts and content is loaded
- THEN essential navigation, rows, feedback, and playbar controls remain visible without overlap

### Requirement: Region focus and navigation

The shell MUST expose deterministic focus among sidebar, content/search, and
playbar controls. `h/j/k/l` and arrow keys MUST provide directional navigation
(`j`/Down advances a list, `k`/Up reverses it, and `h`/Left or `l`/Right moves
between applicable regions). `Enter` MUST activate the focused selection; `/`
MUST focus search; `Space` MUST toggle play/pause; `n` and `p` MUST request next
and previous; `+`/`-` MUST request volume changes; `<`/`>` MUST request seek
changes; `Esc` MUST cancel or close the active transient state; and `q` MUST
back out of a transient view or quit when no back action applies. Focus MUST be
visible and MUST NOT be lost when a view refreshes.

#### Scenario: Keyboard path to activation

- GIVEN the application is focused on the sidebar
- WHEN the user navigates to a content source and presses `Enter`
- THEN the content region receives focus and the selected source is shown

#### Scenario: Mouse activation and scrolling

- GIVEN a composed shell with a sidebar, scrollable content, search input, and playbar
- WHEN the user clicks those targets or scrolls a region
- THEN the target receives the corresponding action/focus and only the intended region scrolls

### Requirement: Truthful help and interaction acceptance

The help view MUST list every implemented binding in this slice, including
`Space`, `n`, `p`, `+/-`, `< >`, `?`, `Esc`, and `q`, with their actual scope.
It MUST NOT advertise unsupported queue, device, lyrics, streaming, or source
actions. Acceptance MUST prove focus, keyboard, mouse, scrolling, and state
transitions through deterministic unit tests and Textual pilots at compact and
wide sizes; screenshots MAY support review but MUST NOT be the sole parity
evidence. “Parity” means equivalent interaction concepts and hierarchy, not
exact pixels.

#### Scenario: Help reflects capability boundary

- GIVEN the help view is opened
- WHEN the user reviews available bindings
- THEN supported actions are listed accurately and unsupported actions are absent or explicitly unavailable

#### Scenario: Deterministic pilot parity

- GIVEN mocked services and fixed terminal dimensions
- WHEN a pilot executes keyboard, mouse, focus, and scrolling paths
- THEN the same observable actions and feedback occur reproducibly without live Spotify or playerctl

## Scope boundary

This first slice MUST NOT add Premium/API streaming, device management, real
queue mutation or inspection, lyrics, cover art, a visualizer, alternate
sources, plugins, recommendations, detail-page or pagination breadth, or copied
Spotatui assets/source. Any exact compact breakpoint, `q` history semantics, or
unsupported-action wording not fixed by the proposal is an unresolved product
decision and MUST be surfaced rather than invented.
