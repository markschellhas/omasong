# PRD: Beat Sequencer

**Status:** Draft
**Owner:** Songwriter plugin

---

## Overview

Add an optional beat lane beneath every chord bar. Each beat lane belongs to the same measure as the chord slots above it and opens a compact step sequencer for kick, snare, and hi-hat. Saved patterns play from the existing song transport so rhythm and chords share BPM, looping, section playback, and row repeats.

## Goals / Non-Goals

**Goals:**

1. Let the user show or hide all beat lanes with one clearly labeled control.
2. Give every measure an independent kick, snare, and hi-hat pattern.
3. Support sixteenth-note steps derived from the measure time signature: 16 in 4/4, 12 in 3/4, and 12 in 6/8.
4. Persist patterns in session songs, named library songs, and full agent song documents.
5. Start each measure's beat pattern from the same transport event as its chords, including loops, section playback, rests, and repeated rows.

**Non-Goals:**

1. Sample import, per-hit velocity, swing, effects, and mixer controls.
2. A standalone drum-machine transport or a second BPM.
3. Changing the `chords-agent progressions` chord-focused response.
4. Replacing the existing QML timer and detached audio-helper architecture.

## Current Implementation

The song model in `js/Song.js` stores sections containing measures and chord slots. `SongStructure.qml` renders four measures per row, and `Songwriter.qml` builds a beat timeline, advances it with a QML `Timer`, and launches `play-notes.py` for chord audio. Session persistence, named-library persistence, and `chords-agent song` serialize the song document. There is currently no percussion data, editor, UI lane, or percussion renderer.

## Proposed Implementation

Each normalized measure gains a `beats` object containing boolean `kick`, `snare`, and `hihat` step arrays. Empty and legacy measures normalize to an empty pattern sized from their section time signature. A song-level `beatsVisible` UI preference controls whether a compact beat lane appears below each chord bar.

Clicking a beat lane opens a QML sequencer panel for that measure. It displays three labeled rows and one button per sixteenth-note step; clicking a step toggles it immediately. The lane summarizes active hits and highlights while its measure plays.

At the first event in each measure/pass, `Songwriter.qml` launches the audio helper once with the whole pattern and the current BPM. The helper renders kick, snare, and hi-hat transients into one measure-length WAV, avoiding one process per drum hit.

## Technical Details

- Extend `js/Song.js` normalization, cloning, bar creation, time-signature synchronization, emptiness checks, and mutation helpers for beat patterns.
- Preserve old song compatibility by synthesizing empty patterns when `beats` is absent and resizing patterns deterministically when meter changes.
- Add pure helpers for step counts, pattern encoding, and measure-start detection with JavaScript unit tests.
- Extend `play-notes.py` with a bounded drum-pattern CLI/rendering mode and WAV tests.
- Add `BeatSequencer.qml` using existing `Style`, `Color`, `Button`, spacing, border, typography, focus, and menu-overlay conventions.
- Add beat-lane signals and layout to `SongStructure.qml`, with orchestration and persistence wiring in `Songwriter.qml`.
- Include beats in `Agent.songJson`; leave `Agent.progressionsJson` unchanged.
- Add and connect a `beats` feature map; update related song structure, playback, song library, and agent API maps.

## Effort Estimates

- Song model and serialization: M
- Drum audio rendering and transport integration: M
- Beat lane and sequencer UI: L
- Tests and feature maps: M

## Open Questions

- Future work may add velocity or swing, but the initial model intentionally stores only on/off steps.
- A persistent audio engine may become desirable if later versions require live per-step editing without measure-boundary restart or sample-accurate advanced sequencing.

## Related Docs

- `.features/song_structure.yaml`
- `.features/chord_slots.yaml`
- `.features/playback.yaml`
- `.features/song_library.yaml`
- `README.md`
