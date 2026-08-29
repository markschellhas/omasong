# Chords & Tabs — Omarchy plugin

**Source (read-only):** https://github.com/markschellhas/chords-and-tabs  
**Maps:** that repo’s `.features/*.yaml` are the product. This file restates them and says how the plugin implements them. Re-pull the source and re-read the maps before changing this document or the plugin.

This repo is the Omarchy destination: plugin id `io.github.markschellhas.songwriter`, a bar chip plus overlay with **full feature parity**. Do not clone-and-edit, commit to, or open PRs against the source.

A user who knows the JUCE app must be able to use the overlay without learning a new model. Same default song, same circle / chips / slots / piano / transport, same keys, same sounding-note highlight, same `chords-agent` contract.

## Plugin

Third-party Omarchy plugin: `manifest.json` at git root, kinds `overlay` + `bar-widget`.

```
manifest.json          id: io.github.markschellhas.songwriter
BarWidget.qml          bar chip → shell toggle
Songwriter.qml         overlay host: title, hint, Esc, keys, persist, agent
Transport.qml          Play, Stop, Loop, BPM 40–240
CircleOfFifths.qml     rotating circle + seven I–vii° chips
SongStructure.qml      sections / 4-bar rows / measures / slots / :||
Piano.qml              C3–C5, SoundPicker, laptop-key glyph
js/Model.js            MusicTheory: stations, diatonic I–vii°, encodeChord
js/Song.js             Song + Timeline: span, meter, place/split/resize, repeats
js/Keyboard.js         LaptopKeys.h exactly (off until toggled)
play-notes.py          triad + live notes (PipeWire) until a richer synth exists
tests/                 MusicTheory, Song, LaptopKeys, Timeline cases from source
```

Layout, top → bottom, matching `MainComponent`:

1. Title **Chords & Tabs** + hint (current `region_focus`)
2. Transport — Play, Stop, Loop, BPM
3. Circle of fifths — rotating circle + seven “in this key” chips
4. Song structure — sections → 4-bar rows → measures → slots
5. Piano — C3–C5, sound picker, optional laptop-key map

Bar chip toggles the overlay. Clicks outside the card pass through. Esc closes.

**License:** source application code is GPLv3-style (matching herman-band). Follow that for the port. JUCE is not vendored here.

**One adaptation:** `audio_device` — no JUCE Device dialog. Play through PipeWire (`pw-play` / `paplay` / `aplay`). Everything else matches the maps.

## Rules

| Rule | Meaning |
|------|---------|
| Twelve features only | A capability is in scope iff it has a source `.features/*.yaml` map |
| Triads | `{ rootPc, quality }`. No chord-symbol text field, no typed `Cmaj7` |
| No transpose on key change | Circle changes tonic, rotation, and chips. Placed chords stay |
| Same data | Song document, defaults, and agent JSON match the source |
| Same keys | j/k regions, h/l key or sound, ←/→ / wheel rotate, Space play/stop, optional laptop map |
| Do not invent a second model | Port `Song`, `Timeline`, `MusicTheory`, `LaptopKeys` by reading the source |

Out of scope: editing the source repo; replacing Omarchy’s bar or shipping a second Quickshell process; tap tempo; Space-as-sustain; typed chord grids.

## Feature set

| Slug | Purpose |
|------|---------|
| `music_theory` | Name triads, diatonic sets, time signatures, and chord drag payloads for the rest of the app. |
| `circle_of_fifths` | Rotate the circle so the active key sits at 12 o'clock and drag diatonic or neighbouring triads into bars. |
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

---

## 1. `music_theory` → `js/Model.js`

**Purpose:** Name triads, diatonic sets, time signatures, and chord drag payloads for the rest of the app.

**Source:** `src/theory/MusicTheory.h`, `src/theory/MusicTheory.cpp`  
**Apps:** `chords_and_tabs`, `chords-agent`

| Path | Flow |
|------|------|
| primary | Caller → `CircleOfFifths::diatonicTriads(index)` → seven triads sharing the relative-minor set |
| payload | GUI → `encodeChord` / `decodeChord` → `chord\|<name>\|<rootPc>\|<qualityInt>` |

- Chord: `{ rootPc: 0–11 (C=0), quality: major \| minor \| diminished \| augmented }`.
- Name: major `C`, minor `Cm`, diminished `Cdim`, augmented `Caug`. Pitch classes: `C Db D Eb E F F# G Ab A Bb B`.
- Stations, clockwise fifths, index 0 = C / Am:

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

- Numerals: `I ii iii IV V vi vii°` (qualities M m m M M m dim). Major and relative minor share the triad set.
- Payload: `chord|<name>|<rootPc>|<qualityInt>` (`0` major, `1` minor, `2` diminished, `3` augmented).
- `maxSlots()` = numerator (`4/4` → 4, `3/4` → 3, `2/4` → 2, `6/8` → 6). Beats per bar = `4 * numerator / denominator`.
- Triad MIDI voiced in C3–C5 (48–72).

**Parity:** source `MusicTheoryTest` cases pass against `js/Model.js`.

**Related:** `circle_of_fifths`, `chord_slots`, `song_structure`, `agent_api`, `playback`

---

## 2. `circle_of_fifths` → `CircleOfFifths.qml`

**Purpose:** Rotate the circle so the active key sits at 12 o'clock and drag diatonic or neighbouring triads into bars.

**Source:** `src/gui/CircleOfFifthsComponent.cpp`, `src/MainComponent.cpp`

| Path | Flow |
|------|------|
| primary | User → click wedge, mouse wheel, h/l, or ←/→ → `rotate()`; tonic at 12 o'clock; `onSelectionChanged` |
| drag | User → drag outer/inner wedge or DiatonicChip → `encodeChord` payload onto a bar slot |
| preview | User → hover/press wedge → `onChordPreview` lights the piano triad |

- 12 stations; outer = major, inner = relative minor.
- Active wedge **rotates to 12 o’clock** (not a highlight left in place).
- Seven chips `I ii iii IV V vi vii°`. Click = preview only. Click does not insert or transpose.
- Key change updates tonic, rotation, and chips. Placed chords stay.

**Parity:** rotate by click / wheel / h/l / arrows; drag starts `chord|…` payload; preview lights the piano; song chords do not move.

**Related:** `music_theory`, `chord_slots`, `region_focus`, `piano_keyboard`, `agent_api`

---

## 3. `song_structure` → `SongStructure.qml` + `js/Song.js`

**Purpose:** Hold Verse/Chorus (and extra) sections whose bar count follows time signature; add, rename, or delete them.

**Source:** `src/gui/SectionListComponent.cpp`, `src/gui/SectionComponent.cpp`, `src/model/Song.h`

| Path | Flow |
|------|------|
| primary | User → + Append Section → Verse/Chorus/…/Custom → `Song.addSection` with `barsForTimeSignature` bars |
| edit | User → Edit → 4/4, 3/4, 2/4, or 6/8 → `setTimeSignature` resizes measures |
| rename | User → double-click title, More → Rename, or Edit → Rename → `setSectionName` |
| error | User → Delete last section → ignored (cannot delete last) |

- Default (`Song::resetToDefault`): **120 BPM**, **4/4**, Verse `C | G | F | Dm`, Chorus `D | G | C | Em`. Four bars per 4/4 section, one full-bar slot (`span` = 4).
- `barsForTimeSignature` = numerator: 4/4 → 4, 3/4 → 3, 2/4 → 2, 6/8 → 6.
- Append: Verse, Chorus, Pre-Chorus, Bridge, Intro, Outro, Solo, Custom (empty → `"Section"`).
- Edit menu: `4/4 (4 bars)`, `3/4 (3 bars)`, `2/4 (2 bars)`, `6/8 (6 bars)`.
- Rows of `kBarsPerRow = 4`.

**Parity:** source `SongModelTest` section / meter / cannot-delete-last cases. Overlay opens on the default Verse/Chorus, not empty cells.

**Related:** `chord_slots`, `row_repeats`, `playback`, `agent_api`, `music_theory`, `region_focus`

---

## 4. `chord_slots` → `SongStructure.qml` + `js/Song.js`

**Purpose:** Place, split, shrink, and clear chords in bar slots (4/4 holds at most four).

**Source:** `src/gui/ChordSlotComponent.cpp`, `src/gui/MeasureComponent.cpp`, `src/model/Song.h`

| Path | Flow |
|------|------|
| primary | User → drop chord on empty slot → `Song.placeChord` fills it |
| split | User → drop onto filled chord → halve span and insert on drop side |
| resize | User → drag left/right edge → `resizeSlot` opens empty slots in freed units |
| clear | User → hover × on filled chip → `setChord` nullopt |

- Slots in a bar sum to `timeSig.maxSlots()`. 4/4 holds at most four (filled, empty, or mixed).
- Drop on a filled chord halves it and inserts on the drop side (`placeChord(..., insertAfter)`). At max capacity, a further drop **replaces**.
- Edge-drag snaps `span` down; freed units become empty slots on that edge.
- Empty slots are rests. Click a filled slot auditions it. No type-to-enter symbol.

**Parity:** source `placeChord` / `resizeSlot` tests. QML drop, split, edge-resize, and hover-×.

**Related:** `circle_of_fifths`, `song_structure`, `playback`, `music_theory`, `agent_api`

---

## 5. `row_repeats` → `SongStructure.qml` + `js/Song.js`

**Purpose:** Toggle a :|| at the end of each 4-bar row so that row plays twice.

**Source:** `src/gui/SectionComponent.cpp`, `src/model/Song.h`, `src/model/Timeline.cpp`

| Path | Flow |
|------|------|
| primary | User → click RepeatSignButton → `setRowRepeat`; `buildTimeline` emits the row with `repeatPass=1` |

- One bool per 4-bar row (`Section.rowRepeats`). Off by default.
- 4 bars → one row; 6 bars (6/8) → two rows and two flags.
- Timeline duplicates only the toggled row. First pass `repeatPass=0`, second `1`.
- Default Verse+Chorus, no repeats: 8 events / 32 beats. Verse row on: 12 events / 48 beats.

**Parity:** `:||` visible per row; timeline length matches source tests.

**Related:** `song_structure`, `playback`, `agent_api`

---

## 6. `playback` → `Transport.qml` + `js/Song.js`

**Purpose:** Play, stop, and loop the song at BPM; audition a slot; drive playhead and sounding-note highlight.

**Source:** `src/gui/TransportStrip.cpp`, `src/audio/ChordEngine.cpp`, `src/model/Timeline.h`

| Path | Flow |
|------|------|
| primary | User → Play or Space → `ChordEngine.play` walks `buildTimeline` events |
| loop | User → Loop toggle → `setLooping` wraps `currentBeat` |
| bpm | User → BPM slider 40–240 → `Song.setBpm` and `engine.setBpm` |
| audition | User → click filled slot → `playChord` for `slotDurationBeats`, then cancel |

- Transport: Play, Stop, Loop, BPM 40–240. Space toggles play/stop when laptop mapping is off.
- Events: `{ startBeat, durationBeats, chord, rest, sectionIndex, measureIndex, slotIndex, repeatPass }`.
- Playhead on the current slot. Sounding triad lights the piano.
- Slot duration in quarter-note beats. A full 4/4 bar is 4.0.

**Parity:** playhead follows span, meter, and repeats. No tap tempo.

**Related:** `song_structure`, `chord_slots`, `row_repeats`, `piano_keyboard`, `instruments`, `audio_device`

---

## 7. `piano_keyboard` → `Piano.qml`

**Purpose:** Show a C3–C5 piano; click keys to play notes; light triad notes from play, preview, or selection.

**Source:** `src/gui/PianoKeyboard.cpp`, `src/MainComponent.cpp`

| Path | Flow |
|------|------|
| primary | User → mouse down on key → `onNoteOn` midi → `ChordEngine.noteOn` |
| highlight | Timer → `soundingNotes` or selected/preview triad → `setHighlightedNotes` |

- MIDI **48–72** (C3–C5), inclusive.
- Click: note on while held, off on release.
- Highlight from playback, circle preview, and selected slot.
- Hosts SoundPicker chevrons and the laptop-key glyph.

**Parity:** range is C3–C5, not a sliding two-octave window from C4.

**Related:** `playback`, `instruments`, `laptop_keys`, `circle_of_fifths`, `region_focus`

---

## 8. `instruments` → `Piano.qml` + engine

**Purpose:** Cycle synth timbre among Piano, Electric Piano, Organ, Pad, and Strings.

**Source:** `src/audio/Instruments.h`, `src/gui/PianoKeyboard.cpp`

| Path | Flow |
|------|------|
| primary | User → SoundPicker chevrons or h/l in Keyboard region → `cycleInstrument`; persist `prefs.xml` |

- Order: Piano (0), Electric Piano, Organ, Pad, Strings. Cycle wraps.
- Same timbre for playback, audition, preview, and live notes.
- Persist last instrument with song prefs. Sine stand-ins are fine until a richer synth exists.

**Parity:** five named sounds, chevrons, h/l in Keyboard region, persist.

**Related:** `piano_keyboard`, `playback`, `region_focus`, `audio_device`

---

## 9. `laptop_keys` → `js/Keyboard.js` + `Piano.qml`

**Purpose:** Optional QWERTY map (A=C …; Z/X octave) that plays live notes and steals H/J/K/L from vim nav.

**Source:** `src/theory/LaptopKeys.h`, `src/gui/PianoKeyboard.cpp`

| Path | Flow |
|------|------|
| primary | User → KeyboardToggle on → `handleComputerKeyPress` maps A/W/S… to MIDI |
| octave | User → Z/X → `shiftOctave` (0–8) |
| alt | Mapping off → j/k/h/l remain region nav |

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
- When on, these keys take over H/J/K/L. Space is not sustain.

**Parity:** source `LaptopKeysTest`. Map is `LaptopKeys.h`, off until the glyph is on.

**Related:** `piano_keyboard`, `playback`, `region_focus`

---

## 10. `region_focus` → `Songwriter.qml`

**Purpose:** j/k cycle focus among circle, song structure, and keyboard; h/l then rotate key or cycle sound.

**Source:** `src/nav/RegionFocus.h`, `src/MainComponent.cpp`

| Path | Flow |
|------|------|
| primary | User → j/k → `cycleNavRegion`; focus frame and hint text update |
| hl | User → h/l → Circle rotates key; Keyboard cycles instrument; Song ignores |

- Regions top → bottom: Circle (0), Song, Keyboard. j = down, k = up; wrap.
- Names: “Circle of fifths”, “Song structure”, “Keyboard”.
- h/l: Circle = previous/next key; Keyboard = previous/next sound; Song = no-op.
- ←/→ and wheel still rotate the circle in any region.
- When `laptop_keys` is on, H/J/K/L are notes, not nav.

**Parity:** focus frame + hint update; h/l meaning depends on region.

**Related:** `circle_of_fifths`, `instruments`, `laptop_keys`, `song_structure`, `piano_keyboard`

---

## 11. `agent_api` → `Songwriter.qml` + CLI

**Purpose:** Let any command-running agent read placed chords and the full song from live loopback or last snapshot.

**Source:** `src/cli/chords-agent.cpp`, `src/api/AgentHttpServer.cpp`, `src/api/SongJson.cpp`, `AGENTS.md`  
**Apps:** `chords-agent`, `chords_and_tabs`

| Path | Flow |
|------|------|
| primary | Agent → `chords-agent progressions` → GET `/progressions` or snapshot `progressions.json` |
| song | Agent → `chords-agent song` → full document; empty slots `null` |
| health | Agent → `chords-agent health` → exit 0 if live else 2 |
| error | `chords-agent --live` with app down → exit 2 |

Do not infer the song from defaults. Read live state.

| Command | Output |
|---------|--------|
| `chords-agent progressions` | Placed chords by section plus a `C \| G F C \| Dm` string |
| `chords-agent song` | Full document; empty slots are `null` |
| `chords-agent health` | Live app up (exit `0`) or not (exit `2`) |

- Loopback: `127.0.0.1` port **17891**, or `$CHORDS_AGENT_PORT`, or the port in `agent-api.json`.
- Snapshot: `$CHORDS_AGENT_HOME` or `~/.config/chords-and-tabs/`. Still write snapshots if the bind fails.
- `--live` skips the snapshot and fails if the app is down.

**`progressions`** — empty slots omitted from `chords`, shown as `-` in `progression`; `numeral` only when diatonic in the current key:

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

**`song`** includes every slot as `sections[].measures[].slots[]` (`null` if empty), plus `key`, `bpm`, `timeSignature`, `rowRepeats`. Chord objects there omit `bar` / `slot` (position is the array index).

**Parity:** `chords-agent progressions | song | health` works against the running overlay. Persist last song + key in the source JSON shape.

**Related:** `song_structure`, `chord_slots`, `circle_of_fifths`, `row_repeats`, `music_theory`

---

## 12. `audio_device`

**Purpose:** Pick JACK (PipeWire) or ALSA output and persist the JUCE device graph.

**Source:** `src/gui/TransportStrip.cpp`, `src/MainComponent.cpp`

| Path | Flow |
|------|------|
| primary | User → Device → AudioDeviceSelectorComponent → `device.xml` under `userApplicationDataDirectory/chords-and-tabs` |

**Omarchy:** no Device button and no JUCE selector. Output is PipeWire via the host. Persist instrument prefs next to song state.

**Parity:** play, preview, and live notes come out the speakers. Do not invent a second device UI.

**Related:** `playback`, `instruments`

---

## Song document

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

| Section | Meter | Bars | Slots |
|---------|-------|------|-------|
| Verse | 4/4 | 4 | C, G, F, Dm (one full-bar slot each) |
| Chorus | 4/4 | 4 | D, G, C, Em (one full-bar slot each) |

Port `Song` + `Timeline` from `src/model/`. Do not invent a second song model.

## Build order

Implement against the contracts above. Each phase is done only when its parity line holds.

1. **Model** — `js/Model.js`, `js/Song.js`, `js/Keyboard.js` + tests from `MusicTheoryTest`, `SongModelTest`, `LaptopKeysTest`, plus timeline / row-repeat cases. Default JSON matches source. `placeChord` / `resizeSlot` / meter bar counts match C++.
2. **Circle + chips** — rotate to 12 o’clock; outer major / inner minor; seven chips; click = preview; drag = payload.
3. **Song structure** — section header (name, Edit, more); 4-bar rows; `:||`; drop / split / edge-resize / clear; time-signature menu.
4. **Transport + piano** — Play / Stop / Loop / BPM / Space; timeline playhead; C3–C5; five sounds; glyph map; Z/X; sounding-note glow.
5. **Focus + persist + agent** — j/k regions; h/l by region; source-shaped snapshot; `chords-agent` on 17891.
6. **Omarchy** — `omarchy plugin validate`, enable, bar chip, overlay, Esc, drag, play, agent CLI. That last check needs a real Omarchy box (`omarchy-shell` is not in this VM).

## Done

- All twelve purposes and user flows behave as in the source maps.
- Default song and agent JSON match the source contracts.
- `chords-agent progressions`, `song`, and `health` work against the plugin.
- Source repo remains untouched.

```bash
python3 tests/run.py
omarchy plugin validate ~/.config/omarchy/plugins/io.github.markschellhas.songwriter
```
