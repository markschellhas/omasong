# Migration plan: Chords & Tabs → Omarchy plugin

**Source product (read-only):** https://github.com/markschellhas/chords-and-tabs

**Product contract:** [PRD.md](PRD.md) — restates the source `.features/*.yaml` maps exactly. This file is sequencing and gap status only. If the two disagree, the feature maps and the PRD win.

Do not clone-and-edit, commit to, open PRs against, or otherwise change that repository. This repo (`songwriter`) is the Omarchy destination. Inventory the source by reading it.

Chords & Tabs is a JUCE song-builder: pick a key on the circle of fifths, drag diatonic (and neighbouring) triads into verse/chorus slots, and hear the progression with the sounding notes lit on the piano. It already targets Omarchy (Arch + Hyprland + PipeWire) as a **standalone window**. This project turns the **same product** into an **Omarchy shell plugin** (bar chip + overlay) with the same features and the same functionality.

## Feature maps (source of truth)

Re-pull https://github.com/markschellhas/chords-and-tabs and read `.features/` before changing behavior. The product is these twelve slugs and nothing else:

| Slug | Source map |
|------|------------|
| `circle_of_fifths` | `.features/circle_of_fifths.yaml` |
| `music_theory` | `.features/music_theory.yaml` |
| `song_structure` | `.features/song_structure.yaml` |
| `chord_slots` | `.features/chord_slots.yaml` |
| `row_repeats` | `.features/row_repeats.yaml` |
| `playback` | `.features/playback.yaml` |
| `piano_keyboard` | `.features/piano_keyboard.yaml` |
| `instruments` | `.features/instruments.yaml` |
| `laptop_keys` | `.features/laptop_keys.yaml` |
| `region_focus` | `.features/region_focus.yaml` |
| `agent_api` | `.features/agent_api.yaml` |
| `audio_device` | `.features/audio_device.yaml` |

## Constraints

| Rule | Meaning |
|------|---------|
| Source is immutable | No commits, issues, or PRs on `markschellhas/chords-and-tabs` |
| Feature parity | Overlay must do what the JUCE app’s `.features/` maps describe |
| Same data | Song document, defaults, and agent JSON match the source contracts |
| Same interaction | Drag/split/resize slots, vim-style region focus, laptop-key map, row repeats |
| Plugin contract | Third-party Omarchy plugin: `manifest.json` at git root, `overlay` + `bar-widget` |
| License | Source application code is GPLv3-style (matching herman-band). The plugin port must follow that, not relicense the behavior as MIT |

## Source architecture (what we are porting)

Layout (top → bottom), from `MainComponent`:

1. Title **Chords & Tabs** + hint line
2. **TransportStrip** — Play, Stop, Loop, BPM, Device
3. **CircleOfFifthsComponent** — rotating circle + seven “in this key” roman chips
4. **SectionListComponent** — sections → 4-bar rows → measures → chord slots
5. **PianoKeyboard** — C3–C5, sound picker, optional laptop-key map

Supporting systems:

| Source files | Role |
|--------------|------|
| `src/model/Song.*` | Song, sections, measures, slots with `span`, row repeats, place/resize/split |
| `src/model/Timeline.*` | Flatten song into `PlayEvent`s (beats, rests, row-repeat pass) |
| `src/theory/MusicTheory.*` | Circle stations, diatonic I–vii°, triad MIDI in C3–C5 |
| `src/theory/LaptopKeys.h` | A=C, W=C♯, … Z/X octave; off until glyph toggle |
| `src/audio/ChordEngine.*` | Play/preview/live notes, loop, sounding-note query |
| `src/audio/Instruments.h` | Piano, Electric Piano, Organ, Pad, Strings |
| `src/nav/RegionFocus.h` | j/k cycle Circle / Song / Keyboard |
| `src/api/SongJson.*` + `AgentHttpServer.*` + `chords-agent` | Live JSON on `127.0.0.1:17891`, snapshot under `~/.config/chords-and-tabs/` |

Default song (`Song::resetToDefault`): **120 BPM**, **4/4**, Verse `C | G | F | Dm`, Chorus `D | G | C | Em`. Four bars per 4/4 section, one full-bar slot each.

## Feature inventory and Omarchy mapping

Parity means the overlay behaves like the JUCE app, feature map by feature map. Device → JACK/ALSA is the one intentional adaptation: the plugin lives inside `omarchy-shell` and should play through PipeWire (`pw-play` / `paplay`) instead of opening JUCE’s device dialog.

| Feature | Source behavior | Omarchy mapping | Status in this repo |
|---------|-----------------|-----------------|---------------------|
| *(chrome)* | Title, hint, Esc-equivalent close | Overlay `PanelWindow` + bar chip toggle | Partial (wrong title model, no hint) |
| `playback` | Play / Stop / Loop / BPM 40–240 | `Transport.qml` + engine | Partial (has tap tempo extra, which the maps do not include) |
| `playback` | Space toggles play/stop | Overlay key handler | Missing (Space is sustain today) |
| `circle_of_fifths` | 12 stations C/Am … F/Dm; **active wedge at 12 o’clock** | `CircleOfFifths.qml` + `js/Model.js` | Partial (highlights in place, does not rotate) |
| `circle_of_fifths` / `region_focus` | h/l or ←/→ or wheel rotate the circle | Same keys when Circle region is focused | Partial (arrows only; no rotation) |
| `circle_of_fifths` | Click wedge: preview triad | `play-notes.py` / synth | Partial (also auto-inserts / transposes — **wrong**) |
| `circle_of_fifths` / `chord_slots` | Drag wedge onto a bar slot | QML drag-and-drop | Missing |
| `circle_of_fifths` / `music_theory` | Seven diatonic chips I, ii, iii, IV, V, vi, vii°; drag or click | Chip row under circle | Missing (only I IV V vi text) |
| `region_focus` | j/k focus Circle ↔ Song ↔ Keyboard | `RegionFocus` port | Missing |
| `song_structure` | Sections: add / rename (double-click or Edit) / delete | `SongStructure.qml` | Partial (typed cells, no Edit menu) |
| `song_structure` / `music_theory` | Per-section time signature 4/4, 3/4, 2/4, 6/8; bar count = numerator | Song model | Missing |
| `row_repeats` | Measures in rows of 4; `:||` repeats that row once | Repeat sign + `rowRepeats` | Missing |
| `chord_slots` | Slots have `span`; bar slots sum to `maxSlots` (4/4 → 4) | Port `Song::placeChord` / `resizeSlot` | Missing (flat 8 empty string cells) |
| `chord_slots` | Drop on filled chord **halves** it and inserts | `placeChord(..., insertAfter)` | Missing |
| `chord_slots` | Drag left/right **edge** to shrink/grow; empty slots appear | `resizeSlot` | Missing |
| `chord_slots` | Hover × clears a filled chip | Clear affordance | Missing |
| `playback` | Play walks timeline; playhead on current slot | `buildTimeline` + transport timer | Partial (one-slot-per-index, ignores span/meter/repeats) |
| `piano_keyboard` / `playback` | Sounding triad lights on the piano | Highlight MIDI from engine | Missing (activeNotes not wired to playback) |
| `piano_keyboard` | Piano C3–C5 (MIDI 48–72); click note on/off | `Piano.qml` | Partial (2 octaves from octave 4 = C4–B5) |
| `instruments` | Sounds: Piano, EP, Organ, Pad, Strings; chevrons / h/l in Keyboard region | Instrument cycle | Missing |
| `laptop_keys` | Map **off by default**; glyph toggle; A=C … `'`=F; Z/X octave | `LaptopKeys.h` | Wrong map (not `LaptopKeys.h`) and always-on |
| `agent_api` | Persist last song + key | Prefer source path `~/.config/chords-and-tabs/` and source JSON shape | Wrong path/shape (`~/.local/state/omarchy/songwriter/song.json`) |
| `agent_api` | `chords-agent progressions \| song \| health` on port 17891 | Loopback HTTP or `omarchy-shell` IPC + CLI | Missing |
| `song_structure` | Starter Verse/Chorus progressions | `Song.resetToDefault` | Wrong (empty verse/chorus) |
| `audio_device` | Device → JACK/ALSA, persist graph | PipeWire via host (intentional) | Partial (no Device dialog; output path exists) |

Changing the circle **does not transpose placed chords** in the source. It changes the tonic, the rotated wedge, and the diatonic chip set. The current plugin transposes the whole song on key change; that must be removed.

Chords are **triads** (`rootPc` + `Quality`), not typed symbols like `Cmaj7`. The source does not have a chord-symbol text field.

## Destination architecture

Keep the Omarchy plugin shape already started here:

```
manifest.json          id: io.github.markschellhas.songwriter
BarWidget.qml          bar chip → shell toggle
Songwriter.qml         overlay host, keys, persist, agent publish
Transport.qml
CircleOfFifths.qml     rotating circle + 7 chips
SongStructure.qml      sections / rows / measures / slots
Piano.qml              C3–C5 + sound picker + glyph toggle
js/Model.js            port MusicTheory circle + diatonic I–vii°
js/Song.js             port Song + Timeline (span, meter, repeats)
js/Keyboard.js         port LaptopKeys.h exactly
play-notes.py          triad + live notes until a real synth exists
tests/                 port MusicTheory, Song, LaptopKeys, Timeline cases
```

Port logic by reading the source files listed above. Do not invent a second song model.

Agent contract (must match `AGENTS.md` in the source):

```json
{
  "key": { "index": 0, "major": "C", "relativeMinor": "Am" },
  "bpm": 120,
  "sections": [
    {
      "name": "Verse",
      "timeSignature": "4/4",
      "rowRepeats": [false],
      "progression": "C | G F C | Dm",
      "chords": [
        { "name": "C", "root": "C", "rootPc": 0, "quality": "major", "bar": 0, "slot": 0, "numeral": "I" }
      ]
    }
  ]
}
```

Empty slots are omitted from `chords` and shown as `-` in `progression`. `song` includes empty slots as `null`.

## Build phases

### Phase 0 — Contract ([PRD.md](PRD.md) + this document)

- Treat the source URL and `.features/*.yaml` as canonical.
- Align license with the source before shipping a public port.

### Phase 1 — Model parity

Port `MusicTheory`, `Song`, `Timeline`, `LaptopKeys` into QML JS (or a small Python engine the QML calls). Reproduce source tests: `MusicTheoryTest`, `SongModelTest`, `LaptopKeysTest`, plus timeline/row-repeat cases.

Acceptance: default song JSON matches source defaults; `placeChord` / `resizeSlot` / time-signature bar counts match C++.

### Phase 2 — Circle + chips

Rotate so the selected station is at 12 o’clock. Outer = major, inner = relative minor. Seven diatonic chips. Click = preview only. Drag starts a chord payload (`chord|name|rootPc|quality`).

### Phase 3 — Song structure

Sections with header (name, Edit, more). 4-bar rows, `:||` per row. Drop / split / edge-resize / clear. Time signature menu 4/4 3/4 2/4 6/8.

### Phase 4 — Transport + piano + highlight

Play/stop/loop/BPM/Space. Timeline-accurate playhead. Piano C3–C5, five sounds (sine timbres until a better synth), glyph laptop map, Z/X octave, sounding-note glow.

### Phase 5 — Focus, persist, agent

j/k regions; h/l meaning depends on region. Persist like the source. `chords-agent` compatible loopback (or a wrapper that speaks the same CLI).

### Phase 6 — Live Omarchy check

`omarchy plugin validate`, enable, bar chip, overlay, Esc, drag, play, agent CLI. This VM cannot run `omarchy-shell`; that check is on a real Omarchy box.

## Definition of done

A user who knows the JUCE app can use the overlay without learning a new model:

- Same default song and the same circle/chip/slot/piano/transport behavior
- Same keys (j/k, h/l, arrows, Space, optional laptop map)
- Same sounding-note highlight
- `chords-agent progressions` / `song` / `health` work against the plugin
- Source repo still untouched

## Out of scope

- Editing https://github.com/markschellhas/chords-and-tabs
- Replacing Omarchy’s bar or shipping a second Quickshell process
