# PRD: Chords & Tabs on Omarchy

**Source product (read-only):** https://github.com/markschellhas/chords-and-tabs

**Authoritative feature maps:** that repo’s `.features/*.yaml` (see also `.feature-map.yaml` and `AGENTS.md`). This PRD restates those maps only. It does not add capabilities from this repo’s leftover Svelte MIDI studio (`frontend/`).

This repo (`songwriter`) is the Omarchy destination: a bar chip + overlay that must implement the same product. Do not clone-and-edit, commit to, or open PRs against the source repository.

Implementation sequencing lives in [MIGRATION_PLAN.md](MIGRATION_PLAN.md). This document is the product contract.

## Product

Chords & Tabs is a song-builder: pick a key on the circle of fifths, drag diatonic (and neighbouring) triads into verse/chorus slots, and hear the progression with the sounding notes lit on the piano.

| Layer | Source | This port |
|-------|--------|-----------|
| Shell | Standalone JUCE window on Omarchy (Arch + Hyprland + PipeWire) | Omarchy plugin `io.github.markschellhas.songwriter` (`overlay` + `bar-widget`) |
| Layout (top → bottom) | Title **Chords & Tabs**, hint, TransportStrip, CircleOfFifths, SectionList, PianoKeyboard | Same regions in the overlay |
| Apps | `chords_and_tabs`, `chords-agent` | Overlay + a CLI that speaks the same `chords-agent` contract |

Chords are **triads** (`rootPc` + `Quality`). There is no chord-symbol text field, no typed `Cmaj7`, and changing the circle **does not transpose** placed chords. It changes the tonic, the rotated wedge, and the diatonic chip set.

## Feature set (exact)

These twelve slugs are the entire product. A feature is in scope if and only if it has a map in the source `.features/` directory.

| Slug | Purpose (from the map) |
|------|------------------------|
| `circle_of_fifths` | Rotate the circle so the active key sits at 12 o'clock and drag diatonic or neighbouring triads into bars. |
| `music_theory` | Name triads, diatonic sets, time signatures, and chord drag payloads for the rest of the app. |
| `song_structure` | Hold Verse/Chorus (and extra) sections whose bar count follows time signature; add, rename, or delete them. |
| `chord_slots` | Place, split, shrink, and clear chords in bar slots (4/4 holds at most four). |
| `row_repeats` | Toggle a :|| at the end of each 4-bar row so that row plays twice. |
| `playback` | Play, stop, and loop the song at BPM; audition a slot; drive playhead and sounding-note highlight. |
| `piano_keyboard` | Show a C3–C5 piano; click keys to play notes; light triad notes from play, preview, or selection. |
| `instruments` | Cycle synth timbre among Piano, Electric Piano, Organ, Pad, and Strings. |
| `laptop_keys` | Optional QWERTY map (A=C …; Z/X octave) that plays live notes and steals H/J/K/L from vim nav. |
| `region_focus` | j/k cycle focus among circle, song structure, and keyboard; h/l then rotate key or cycle sound. |
| `agent_api` | Let any command-running agent read placed chords and the full song from live loopback or last snapshot. |
| `audio_device` | Pick JACK (PipeWire) or ALSA output and persist the device graph. |

Omarchy adaptation for `audio_device` only: the plugin lives inside `omarchy-shell` and plays through PipeWire (`pw-play` / `paplay` / `aplay`) instead of opening JUCE’s Device dialog. All other features must match the source maps and the flows below.

---

## 1. `music_theory`

**Purpose:** Name triads, diatonic sets, time signatures, and chord drag payloads for the rest of the app.

**Apps:** `chords_and_tabs`, `chords-agent`

### User flows

| Path | Flow |
|------|------|
| primary | Caller → `CircleOfFifths::diatonicTriads(index)` → seven triads sharing the relative-minor set |
| payload | GUI → `encodeChord` / `decodeChord` → `chord\|<name>\|<rootPc>\|<qualityInt>` |

### Contract

- A chord is `{ rootPc: 0–11 (C=0), quality: major \| minor \| diminished \| augmented }`.
- Name: major `C`, minor `Cm`, diminished `Cdim`, augmented `Caug`. Pitch-class names: `C Db D Eb E F F# G Ab A Bb B`.
- Circle stations (index 0 = C / Am), clockwise fifths:

  | index | major | relative minor |
  |------:|-------|----------------|
  | 0 | C | Am |
  | 1 | G | Em |
  | 2 | D | Bm |
  | 3 | A | F#m |
  | 4 | E | C#m |
  | 5 | B | G#m |
  | 6 | F# | D#m |
  | 7 | Db | Bbm |
  | 8 | Ab | Fm |
  | 9 | Eb | Cm |
  | 10 | Bb | Gm |
  | 11 | F | Dm |

- Diatonic numerals: `I`, `ii`, `iii`, `IV`, `V`, `vi`, `vii°` (major-key qualities: M m m M M m dim). Major and its relative minor share the same triad set.
- Drag payload: `chord|<name>|<rootPc>|<qualityInt>` with `qualityInt` 0=major, 1=minor, 2=diminished, 3=augmented.
- Time signature: `maxSlots()` = numerator (`4/4` → 4, `3/4` → 3, `2/4` → 2, `6/8` → 6). Quarter-note beats per bar = `4 * numerator / denominator`.
- Triad MIDI is voiced inside C3–C5 (48–72).

**Related:** `circle_of_fifths`, `chord_slots`, `song_structure`, `agent_api`, `playback`

---

## 2. `circle_of_fifths`

**Purpose:** Rotate the circle so the active key sits at 12 o'clock and drag diatonic or neighbouring triads into bars.

**App:** `chords_and_tabs`

### User flows

| Path | Flow |
|------|------|
| primary | User → click wedge, mouse wheel, h/l, or ←/→ → `rotate()`; tonic at 12 o'clock; `onSelectionChanged` |
| drag | User → drag outer/inner wedge or DiatonicChip → `encodeChord` payload onto a bar slot |
| preview | User → hover/press wedge → `onChordPreview` lights the piano triad |

### Contract

- 12 stations; outer ring = major, inner ring = relative minor.
- Active wedge is **rotated to 12 o’clock**, not merely highlighted in place.
- Seven “in this key” chips: `I ii iii IV V vi vii°`. Click or drag; click does **not** insert or transpose the song.
- Changing key updates tonic, rotation, and chips only. Placed chords stay where they are.

**Related:** `music_theory`, `chord_slots`, `region_focus`, `piano_keyboard`, `agent_api`

---

## 3. `song_structure`

**Purpose:** Hold Verse/Chorus (and extra) sections whose bar count follows time signature; add, rename, or delete them.

**App:** `chords_and_tabs`

### User flows

| Path | Flow |
|------|------|
| primary | User → + Append Section → Verse/Chorus/…/Custom → `Song.addSection` with `barsForTimeSignature` bars |
| edit | User → Edit → 4/4, 3/4, 2/4, or 6/8 → `setTimeSignature` resizes measures |
| rename | User → double-click title, More → Rename, or Edit → Rename → `setSectionName` |
| error | User → Delete last section → ignored (cannot delete last) |

### Contract

- Default song (`Song::resetToDefault`): **120 BPM**, **4/4**, Verse `C \| G \| F \| Dm`, Chorus `D \| G \| C \| Em`. Each 4/4 section has four bars, one full-bar slot each (`span` = 4).
- `barsForTimeSignature` = numerator: 4/4 → 4 bars, 3/4 → 3, 2/4 → 2, 6/8 → 6.
- Append names: Verse, Chorus, Pre-Chorus, Bridge, Intro, Outro, Solo, or Custom (empty name becomes `"Section"`).
- Time-signature menu: `4/4 (4 bars)`, `3/4 (3 bars)`, `2/4 (2 bars)`, `6/8 (6 bars)`.
- Measures layout in rows of `kBarsPerRow = 4`.

**Related:** `chord_slots`, `row_repeats`, `playback`, `agent_api`, `music_theory`, `region_focus`

---

## 4. `chord_slots`

**Purpose:** Place, split, shrink, and clear chords in bar slots (4/4 holds at most four).

**App:** `chords_and_tabs`

### User flows

| Path | Flow |
|------|------|
| primary | User → drop chord on empty slot → `Song.placeChord` fills it |
| split | User → drop onto filled chord → halve span and insert on drop side |
| resize | User → drag left/right edge → `resizeSlot` opens empty slots in freed units |
| clear | User → hover × on filled chip → `setChord` nullopt |

### Contract

- Slots in a bar sum to `timeSig.maxSlots()`. A 4/4 bar holds at most four slots (filled, empty, or mixed).
- Drop on a filled chord halves that slot and inserts the new chord on the drop side (`placeChord(..., insertAfter)`). At max capacity, a further drop **replaces**.
- Edge-drag snaps a filled slot to a smaller `span`; freed units become empty slots on that edge.
- Empty slots are rests. Click a filled slot auditions it (`playback`).
- There is no type-to-enter chord symbol.

**Related:** `circle_of_fifths`, `song_structure`, `playback`, `music_theory`, `agent_api`

---

## 5. `row_repeats`

**Purpose:** Toggle a :|| at the end of each 4-bar row so that row plays twice.

**App:** `chords_and_tabs`

### User flows

| Path | Flow |
|------|------|
| primary | User → click RepeatSignButton → `setRowRepeat`; `buildTimeline` emits the row with `repeatPass=1` |

### Contract

- One boolean per 4-bar row (`Section.rowRepeats`). Off by default.
- 4 bars → one row; 6 bars (e.g. 6/8) → two rows and two flags.
- Timeline duplicates only the toggled row. First pass `repeatPass=0`, second `repeatPass=1`.
- Default Verse+Chorus (8 bars, no repeats) is 8 events / 32 quarter-note beats. Verse row on → 12 events / 48 beats.

**Related:** `song_structure`, `playback`, `agent_api`

---

## 6. `playback`

**Purpose:** Play, stop, and loop the song at BPM; audition a slot; drive playhead and sounding-note highlight.

**App:** `chords_and_tabs`

### User flows

| Path | Flow |
|------|------|
| primary | User → Play or Space → `ChordEngine.play` walks `buildTimeline` events |
| loop | User → Loop toggle → `setLooping` wraps `currentBeat` |
| bpm | User → BPM slider 40–240 → `Song.setBpm` and `engine.setBpm` |
| audition | User → click filled slot → `playChord` for `slotDurationBeats`, then cancel |

### Contract

- Transport: Play, Stop, Loop, BPM (40–240). Space toggles play/stop when laptop mapping is off.
- Timeline events: `{ startBeat, durationBeats, chord, rest, sectionIndex, measureIndex, slotIndex, repeatPass }`.
- Playhead sits on the current slot. Sounding triad lights the piano (`piano_keyboard`).
- Slot duration is in quarter-note beats (same units as `PlayEvent`). A full 4/4 bar is 4.0 beats.

**Related:** `song_structure`, `chord_slots`, `row_repeats`, `piano_keyboard`, `instruments`, `audio_device`

---

## 7. `piano_keyboard`

**Purpose:** Show a C3–C5 piano; click keys to play notes; light triad notes from play, preview, or selection.

**App:** `chords_and_tabs`

### User flows

| Path | Flow |
|------|------|
| primary | User → mouse down on key → `onNoteOn` midi → `ChordEngine.noteOn` |
| highlight | Timer → `soundingNotes` or selected/preview triad → `setHighlightedNotes` |

### Contract

- Range: MIDI **48–72** (C3–C5), inclusive.
- Click a key: note on while held, note off on release.
- Highlight sources: playback sounding notes, circle preview, selected slot triad.
- Hosts SoundPicker chevrons (`instruments`) and the keyboard-glyph toggle (`laptop_keys`).

**Related:** `playback`, `instruments`, `laptop_keys`, `circle_of_fifths`, `region_focus`

---

## 8. `instruments`

**Purpose:** Cycle synth timbre among Piano, Electric Piano, Organ, Pad, and Strings.

**App:** `chords_and_tabs`

### User flows

| Path | Flow |
|------|------|
| primary | User → SoundPicker chevrons or h/l in Keyboard region → `cycleInstrument`; persist `prefs.xml` |

### Contract

- Order: Piano (0), Electric Piano, Organ, Pad, Strings. Cycle wraps.
- Same engine timbre for playback, audition, preview, and live notes.
- Persist last instrument with the rest of app prefs.

**Related:** `piano_keyboard`, `playback`, `region_focus`, `audio_device`

---

## 9. `laptop_keys`

**Purpose:** Optional QWERTY map (A=C …; Z/X octave) that plays live notes and steals H/J/K/L from vim nav.

**App:** `chords_and_tabs`

### User flows

| Path | Flow |
|------|------|
| primary | User → KeyboardToggle on → `handleComputerKeyPress` maps A/W/S… to MIDI |
| octave | User → Z/X → `shiftOctave` (0–8) |
| alt | Mapping off → j/k/h/l remain region nav |

### Contract

- **Off by default.** Glyph toggle turns it on.
- Semitone from C (default octave 4 → C4 = MIDI 60):

  | Key | ST | Note | Key | ST | Note |
  |-----|---:|------|-----|---:|------|
  | A | 0 | C | K | 12 | C |
  | W | 1 | C♯ | O | 13 | C♯ |
  | S | 2 | D | L | 14 | D |
  | E | 3 | D♯ | P | 15 | D♯ |
  | D | 4 | E | ; | 16 | E |
  | F | 5 | F | ' | 17 | F |
  | T | 6 | F♯ | | | |
  | G | 7 | G | | | |
  | Y | 8 | G♯ | | | |
  | H | 9 | A | | | |
  | U | 10 | A♯ | | | |
  | J | 11 | B | | | |

- MIDI = `(clamp(octave, 0, 8) + 1) * 12 + semitone`, clamped 0–127.
- When on, these keys take over H/J/K/L from `region_focus`. Space is not sustain.

This is **not** the leftover songwriter-frontend map (`a s d f g h j k l ; '` white / `w e r t y u i o p [` black, Space = sustain).

**Related:** `piano_keyboard`, `playback`, `region_focus`

---

## 10. `region_focus`

**Purpose:** j/k cycle focus among circle, song structure, and keyboard; h/l then rotate key or cycle sound.

**App:** `chords_and_tabs`

### User flows

| Path | Flow |
|------|------|
| primary | User → j/k → `cycleNavRegion`; focus frame and hint text update |
| hl | User → h/l → Circle rotates key; Keyboard cycles instrument; Song ignores |

### Contract

- Regions, top to bottom: Circle (0) → Song → Keyboard. j = down, k = up; wrap.
- Display names: “Circle of fifths”, “Song structure”, “Keyboard”.
- h/l: Circle = previous/next key; Keyboard = previous/next sound; Song = no-op.
- ←/→ and wheel still rotate the circle regardless of region.
- When `laptop_keys` is on, H/J/K/L are notes, not nav.

**Related:** `circle_of_fifths`, `instruments`, `laptop_keys`, `song_structure`, `piano_keyboard`

---

## 11. `agent_api`

**Purpose:** Let any command-running agent read placed chords and the full song from live loopback or last snapshot.

**Apps:** `chords-agent`, `chords_and_tabs`

### User flows

| Path | Flow |
|------|------|
| primary | Agent → `chords-agent progressions` → GET `/progressions` or snapshot `progressions.json` |
| song | Agent → `chords-agent song` → full document; empty slots `null` |
| health | Agent → `chords-agent health` → exit 0 if live else 2 |
| error | `chords-agent --live` with app down → exit 2 |

### Contract

Do not infer the song from source defaults. Read live state.

| Command | Output |
|---------|--------|
| `chords-agent progressions` | Placed chords by section plus a `C \| G F C \| Dm` string |
| `chords-agent song` | Full document; empty slots are `null` |
| `chords-agent health` | Live app up (exit `0`) or not (exit `2`) |

- Loopback: `127.0.0.1` port **17891**, or `$CHORDS_AGENT_PORT`, or the port in `agent-api.json`.
- Snapshot dir: `$CHORDS_AGENT_HOME` or `~/.config/chords-and-tabs/` (macOS source path is `~/Library/Application Support/chords-and-tabs/`). The app still writes snapshots if the bind fails.
- `--live` skips the snapshot and fails if the app is not running.

**`progressions` body** (placed chords only; empty slots omitted from `chords`, shown as `-` in `progression`; `numeral` only when diatonic in the current key):

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

**`song` body** includes every slot (`null` if empty) as `sections[].measures[].slots[]`, plus the same `key`, `bpm`, `timeSignature`, and `rowRepeats`. Chord objects in `song` omit `bar` / `slot` (position is the array index).

**Related:** `song_structure`, `chord_slots`, `circle_of_fifths`, `row_repeats`, `music_theory`

---

## 12. `audio_device`

**Purpose:** Pick JACK (PipeWire) or ALSA output and persist the JUCE device graph.

**App:** `chords_and_tabs`

### User flows

| Path | Flow |
|------|------|
| primary | User → Device → AudioDeviceSelectorComponent → `device.xml` under `userApplicationDataDirectory/chords-and-tabs` |

### Omarchy mapping (only intentional change)

The overlay does not open a JUCE device selector. Output is PipeWire via the plugin host (`pw-play` / `paplay` / `aplay`). Persist instrument prefs next to song state. Do not invent a second audio-device UI.

**Related:** `playback`, `instruments`

---

## Shared song document

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

Default after `resetToDefault`:

| Section | Meter | Bars | Slots |
|---------|-------|------|-------|
| Verse | 4/4 | 4 | C, G, F, Dm (one full-bar slot each) |
| Chorus | 4/4 | 4 | D, G, C, Em (one full-bar slot each) |

## Overlay chrome (not a separate feature map)

The source window also shows the title **Chords & Tabs**, a hint line that reflects `region_focus`, and Esc-equivalent close. The plugin maps that to the overlay card + bar chip. Esc closes. This is shell chrome around the twelve features, not a thirteenth feature.

## Explicitly out of scope

These appear in `frontend/specification.md` (leftover Svelte MIDI studio). They are **not** product requirements.

- MIDI recording, armed tracks, overdub, quantization, count-in, tap tempo
- Multi-track mixer (solo, mute, volume, pan, track colors)
- Typed chord-symbol grid (`Cmaj`, `Dm7`, `Csus4`, …) or key-change transpose of placed chords
- AI chat sidebar
- MIDI file import/export
- Demucs / `audio_splitter.py` / `vocal_to_midi.py`
- Laptop map `a s d f g h j k l ; '` / Space-as-sustain
- Editing https://github.com/markschellhas/chords-and-tabs

## Acceptance

A user who knows the JUCE app can use the overlay without learning a new model:

1. All twelve feature purposes and user flows above behave as in the source maps.
2. Default song and agent JSON match the source contracts.
3. `chords-agent progressions`, `song`, and `health` work against the plugin.
4. Source repo remains untouched.

## Sources

Read, do not invent a second model:

| Map | Source doors |
|-----|----------------|
| `circle_of_fifths` | `src/gui/CircleOfFifthsComponent.cpp`, `src/MainComponent.cpp` |
| `music_theory` | `src/theory/MusicTheory.h`, `src/theory/MusicTheory.cpp` |
| `song_structure` | `src/gui/SectionListComponent.cpp`, `src/gui/SectionComponent.cpp`, `src/model/Song.h` |
| `chord_slots` | `src/gui/ChordSlotComponent.cpp`, `src/gui/MeasureComponent.cpp`, `src/model/Song.h` |
| `row_repeats` | `src/gui/SectionComponent.cpp`, `src/model/Song.h`, `src/model/Timeline.cpp` |
| `playback` | `src/gui/TransportStrip.cpp`, `src/audio/ChordEngine.cpp`, `src/model/Timeline.h` |
| `piano_keyboard` | `src/gui/PianoKeyboard.cpp`, `src/MainComponent.cpp` |
| `instruments` | `src/audio/Instruments.h`, `src/gui/PianoKeyboard.cpp` |
| `laptop_keys` | `src/theory/LaptopKeys.h`, `src/gui/PianoKeyboard.cpp` |
| `region_focus` | `src/nav/RegionFocus.h`, `src/MainComponent.cpp` |
| `agent_api` | `src/cli/chords-agent.cpp`, `src/api/AgentHttpServer.cpp`, `AGENTS.md` |
| `audio_device` | `src/gui/TransportStrip.cpp`, `src/MainComponent.cpp` |

Re-pull the source and re-read `.features/` before changing this PRD.
