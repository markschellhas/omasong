# PRD: Chords & Tabs Omarchy Plugin

**Status:** Draft
**Owner:** Songwriter plugin

---

## Overview

Port the Chords & Tabs JUCE song-builder into this Omarchy shell plugin (`markschellhas.songwriter`) as a bar chip plus overlay with full feature parity.

**Original C++ implementation (read-only reference):** https://github.com/markschellhas/chords-and-tabs — the JUCE app, its `.features/*.yaml` maps, tests, and source under `src/`. This PRD restates the parity contract for the plugin; when a behavior is ambiguous or underspecified here, resolve it by reading that repo (maps first, then C++ / tests). Do not clone-and-edit, commit to, or open PRs against it.

Users who know the JUCE app should use the overlay without learning a new model: same default song, circle / chips / slots / piano / transport, same keys, same sounding-note highlight, and the same `chords-agent` contract. Local feature maps (`.features/*.yaml`) in this repo are currently empty; re-pull the C++ repo and re-read its maps before changing scope.

## Goals / Non-Goals

**Goals:**

1. Ship all twelve source-mapped capabilities in the Omarchy overlay with behavior matching the source maps and parity tests.
2. Match the source song document, default Verse/Chorus song, triad chord model (`{ rootPc, quality }`), and agent JSON shapes.
3. Match source keyboard UX: j/k and ↑/↓ region focus, h/l and ←/→ by region, Space play/stop, optional laptop-key map.
4. Expose `chords-agent progressions | song | health` against the running overlay (loopback or snapshot).
5. Play audio through PipeWire on the host (no JUCE device dialog).
6. Keep the source repo untouched; validate with `python3 tests/run.py` and `omarchy plugin validate`.

**Non-Goals:**

- Editing, forking-for-contribution, or opening PRs against the source Chords & Tabs repo.
- Replacing Omarchy’s bar or shipping a second Quickshell process.
- Tap tempo; Space-as-sustain; typed chord-symbol entry (`Cmaj7` grids).
- A second song / theory model that diverges from the source `Song`, `Timeline`, `MusicTheory`, and `LaptopKeys` contracts.
- Inventing capabilities that lack a source `.features/*.yaml` map (twelve features only).

## Current Implementation

Partial Omarchy plugin (v0.2.0). Overlay chrome and layout exist; behavior is not at source parity (per README).

**Entry points (on disk):**

| Path | Role |
|------|------|
| `manifest.json` | Plugin id `markschellhas.songwriter`; kinds `overlay` + `bar-widget` |
| `BarWidget.qml` | Bar chip → shell toggle |
| `Songwriter.qml` | Overlay host: layout, persist hooks, keys, playback state |
| `Transport.qml` | Play / Stop / Loop / BPM UI |
| `CircleOfFifths.qml` | Circle + wedge UI |
| `SongStructure.qml` | Sections / slots UI |
| `Piano.qml` | Piano + sound picker surface |
| `js/Model.js` | Theory / geometry helpers (not yet full `MusicTheory` / `encodeChord` parity) |
| `js/Song.js` | Song helpers using string chord symbols and flat `sections[].chords[]` — not the source measures/slots/span model |
| `js/Keyboard.js` | Laptop / layout key helpers |
| `js/Chords.js` | Additional chord helpers |
| `play-notes.py` | PipeWire note playback (`pw-play` / `paplay` / `aplay`) |
| `write-json.py` | JSON write helper |
| `tests/run.py`, `tests/js_tests.js` | JS unit tests (subset; not full source parity suite) |

**Observed gaps vs source contracts:** default song is empty Verse/Chorus slots (not `C|G|F|Dm` / `D|G|C|Em`); chords are string symbols rather than `{ rootPc, quality }` with span; no `placeChord` / `resizeSlot` / row-repeat / timeline parity; no `chords-agent` loopback on port 17891; local `.features/` maps are empty (`feature-map list` → `[]`).

## Proposed Implementation

Bring the plugin to full parity with the twelve source features, adapting only audio output for Omarchy.

**User-facing (layout top → bottom, matching source `MainComponent`):**

1. Title **Chords & Tabs** + hint (`region_focus`)
2. Transport — Play, Stop, Loop, BPM 40–240
3. Circle of fifths — rotating circle (active key at 12 o’clock) + seven I–vii° chips
4. Song structure — sections → 4-bar rows → measures → slots → `:||`
5. Piano — C3–C5, sound picker, optional laptop-key glyph

Bar chip toggles the overlay; clicks outside the card pass through; Esc closes.

**Feature set (in scope iff mapped in source):**

| Slug | Purpose |
|------|---------|
| `music_theory` | Name triads, diatonic sets, meters, `chord\|name\|rootPc\|qualityInt` payloads |
| `circle_of_fifths` | Rotate key to 12 o’clock; drag wedges/chips into bars; preview lights piano |
| `song_structure` | Verse/Chorus (+ extras); bar count follows time signature; add/rename/delete (cannot delete last) |
| `chord_slots` | Place, split, edge-resize, clear; empty = rest; click filled = audition |
| `row_repeats` | `:||` per 4-bar row doubles that row in the timeline |
| `playback` | Play / stop / loop / BPM; playhead; sounding-note highlight |
| `piano_keyboard` | C3–C5; click notes; triad highlight from play / preview / selection |
| `instruments` | Piano, Electric Piano, Organ, Pad, Strings; persist with prefs |
| `laptop_keys` | Off by default; A=C …; Z/X octave; steals H/J/K/L when on |
| `region_focus` | j/k or ↑/↓ among Circle / Song / Keyboard; h/l or ←/→ act by region |
| `agent_api` | `chords-agent` read live or snapshot song/progressions/health |
| `audio_device` | PipeWire host output only (no Device UI) — sole intentional adaptation |

**Rules that must hold:**

- Triads only: `{ rootPc, quality }`. No chord-symbol text field.
- Circle key change updates tonic, rotation, and chips; placed chords do not transpose.
- Song document, defaults, and agent JSON match the source.
- Do not invent a second model — port `Song`, `Timeline`, `MusicTheory`, `LaptopKeys` from source.

**Default song:** 120 BPM, 4/4, Verse `C | G | F | Dm`, Chorus `D | G | C | Em` (one full-bar slot each).

## Technical Details

**Song document shape (target):**

```
Song
  bpm: 40–240 (default 120)
  sections[]
    name
    timeSig { numerator, denominator }
    measures[]          # length = barsForTimeSignature
      slots[]           # spans sum to timeSig.maxSlots()
        chord?: { rootPc, quality }
        span
    rowRepeats[]        # one bool per 4-bar row
```

**Key contracts:**

- Chord naming / stations / diatonic I–vii° / `encodeChord` payload / `maxSlots()` and beats-per-bar from source `MusicTheory`.
- Circle: 12 stations (outer major / inner relative minor); chips click = preview only; drag = payload.
- Slots: drop empty → fill; drop filled → split/insert or replace at capacity; edge-drag shrinks span; hover × clears.
- Timeline events drive playback; row repeats duplicate toggled rows (`repeatPass` 0 then 1).
- Agent: loopback `127.0.0.1:17891` (or `$CHORDS_AGENT_PORT` / `agent-api.json`); snapshot under `$CHORDS_AGENT_HOME` or `~/.config/chords-and-tabs/`; `--live` fails if app down (exit 2).
- Audio: `play-notes.py` (or successor) via PipeWire; sine stand-ins OK until richer synth; persist instrument with song prefs.
- License: follow source GPLv3-style for the port; JUCE is not vendored.

**Suggested build order (parity gate per phase):**

1. Model — `js/Model.js`, `js/Song.js`, `js/Keyboard.js` + tests from source `MusicTheoryTest` / `SongModelTest` / `LaptopKeysTest` / timeline cases.
2. Circle + chips — rotate, drag payload, preview.
3. Song structure — sections, meter, slots (drop/split/resize/clear), `:||`.
4. Transport + piano — playhead, C3–C5, five sounds, laptop map, sounding-note glow.
5. Focus + persist + agent — region focus, source-shaped snapshot, `chords-agent` on 17891.
6. Omarchy — `omarchy plugin validate`, bar chip, overlay, Esc; final check needs a real Omarchy box.

**Verification:**

```bash
python3 tests/run.py
omarchy plugin validate ~/.config/omarchy/plugins/markschellhas.songwriter
```

## Effort Estimates

| Workstream | Effort |
|------------|--------|
| Theory / Song / Timeline / LaptopKeys JS port + parity tests | L |
| Circle of fifths + diatonic chips UI | M |
| Song structure, chord slots, row repeats UI | L |
| Transport, playback engine, piano, instruments, laptop keys | L |
| Region focus, persist, agent API + CLI contract | M |
| PipeWire audio path (no device UI) | S |
| Omarchy packaging / validate / bar + overlay polish | S |

## Open Questions

1. Should this repo author local `.features/*.yaml` mirrors of the twelve source maps, or continue treating the source repo maps as the only product authority?
2. Where should agent snapshots and prefs live on Omarchy (`~/.config/chords-and-tabs/` vs a plugin-scoped path)?
3. How far to take synth fidelity beyond sine stand-ins for the five instrument names?
4. Is MIT in `manifest.json` intentional until the GPLv3-style port terms are finalized?
5. Final Omarchy acceptance requires hardware with `omarchy-shell` — what is the minimum CI vs on-device checklist?

## Related Docs

- **Original C++ implementation (clarifications beyond this PRD):** https://github.com/markschellhas/chords-and-tabs — `.features/*.yaml`, `src/` (e.g. `MusicTheory`, `Song`, `Timeline`, `LaptopKeys`, GUI, `chords-agent`), and parity tests. Prefer maps, then code/tests, when this PRD is silent or unclear.
- Plugin overview: [README.md](../../README.md)
- Agent instructions: [AGENTS.md](../../AGENTS.md)
- Local feature maps: `.features/` — currently empty (`./bin/feature-map list`)
- Feature Map config: [.feature-map.yaml](../../.feature-map.yaml)
