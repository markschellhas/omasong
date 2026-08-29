# Chords & Tabs Omarchy Plugin Implementation Plan

> **For agent:** REQUIRED SUB-SKILL: Use subagent-driven-development to implement this plan task-by-task.
> Update each task's **Status** as work advances (not only at the end). Progress bar counts only `done` tasks.
> On resume: read **Progress** + each task's **Status** / **Resume** — do not re-do completed phases.

**Goal:** Bring this Omarchy plugin to full parity with the twelve Chords & Tabs source maps: same song document, circle/chips/slots/piano/transport, keys, sounding-note highlight, and `chords-agent` contract.

**Architecture:** QML overlay (`Songwriter.qml`) hosts transport, rotating circle, section/slot grid, and piano. Domain logic lives in `js/Model.js`, `js/Song.js`, and `js/Keyboard.js` (port of source `MusicTheory`, `Song`+`Timeline`, `LaptopKeys`). Audio is PipeWire via `play-notes.py` (no JUCE device UI). Agents read live loopback or snapshots through a `chords-agent` CLI.

**Areas affected:** repo root QML, `js/`, `tests/`, `play-notes.py`, new `chords-agent` + snapshot/HTTP helpers, `.features/*.yaml`, `README.md`

**Tech Stack:** QML/Quickshell (Omarchy plugin), JavaScript `.pragma library`, Python 3 (`tests/run.py`, `play-notes.py`, agent CLI), Node only as the JS test VM

**Feature map:** `.features/music_theory.yaml`, `.features/circle_of_fifths.yaml`, `.features/song_structure.yaml`, `.features/chord_slots.yaml`, `.features/row_repeats.yaml`, `.features/playback.yaml`, `.features/piano_keyboard.yaml`, `.features/instruments.yaml`, `.features/laptop_keys.yaml`, `.features/region_focus.yaml`, `.features/agent_api.yaml`, `.features/audio_device.yaml`

**PRD:** `docs/prds/prd-chords-and-tabs-omarchy-plugin.md` (used by **ship-plan** when Progress is 100%)

**C++ source of truth (when this plan or the PRD is silent):** https://github.com/markschellhas/chords-and-tabs — maps first, then `src/` and tests. Do not commit to that repo.

**UI:** Reuse existing Omarchy/Quickshell tokens already in this plugin (`Color.menu`, `Style.space`, `Style.font`, `qs.Ui` `Button`). Do not add typed chord fields, tap tempo, or Space-as-sustain.

## Progress

**Status:** `████████████████████` 12/12 done (100%) · 0 in flight

| # | Task | Status | Next |
|---|------|--------|------|
| 1 | Music theory JS | `done` | — |
| 2 | LaptopKeys JS | `done` | — |
| 3 | Song document + slots | `done` | — |
| 4 | Timeline + row repeats | `done` | — |
| 5 | Agent JSON | `done` | — |
| 6 | Circle of fifths UI | `done` | — |
| 7 | Song structure + slots + :\|\| UI | `done` | — |
| 8 | Playback + transport | `done` | — |
| 9 | Piano C3–C5 + instruments + PipeWire | `done` | — |
| 10 | Region focus + laptop toggle | `done` | — |
| 11 | chords-agent HTTP + CLI | `done` | — |
| 12 | Remove non-parity paths + maps | `done` | — |

---

### [x] Task 1: Music theory JS

**Status:** `done`
**Resume:** Complete
**Commits:** d05b530

**Files:**
- Modify: `js/Model.js` (replace symbol/wedge helpers with source `MusicTheory` port)
- Modify: `tests/js_tests.js` (theory cases first; leave old Chords/Song assertions until later tasks delete them)
- Modify: `tests/run.py` (keep loading `Model.js`)

**Step 1: Write the failing test**

Prepend these assertions at the top of `tests/js_tests.js` (keep existing tests until Task 12; they will fail as Model.js changes — migrate or gate them in this task so only theory tests run against the new API):

```javascript
assertEq(PC_NAMES.join(" "), "C Db D Eb E F F# G Ab A Bb B")
assertEq(station(0).major, "C")
assertEq(station(0).relativeMinor, "Am")
assertEq(station(1).major, "G")
assertEq(station(11).major, "F")
assertEq(chordName(0, "major"), "C")
assertEq(chordName(0, "minor"), "Cm")
assertEq(chordName(0, "diminished"), "Cdim")
assertEq(chordName(0, "augmented"), "Caug")
assertEq(qualityInt("major"), 0)
assertEq(qualityInt("minor"), 1)
assertEq(qualityInt("diminished"), 2)
assertEq(qualityInt("augmented"), 3)
assertEq(encodeChord({ rootPc: 0, quality: "major" }), "chord|C|0|0")
assertEq(decodeChord("chord|Dm|2|1").rootPc, 2)
assertEq(decodeChord("chord|Dm|2|1").quality, "minor")
var dia = diatonicTriads(0)
assertEq(dia.length, 7)
assertEq(chordName(dia[0].rootPc, dia[0].quality), "C")
assertEq(chordName(dia[1].rootPc, dia[1].quality), "Dm")
assertEq(chordName(dia[6].rootPc, dia[6].quality), "Bdim")
assertEq(numeralFor(dia[0], 0), "I")
assertEq(maxSlots({ numerator: 4, denominator: 4 }), 4)
assertEq(maxSlots({ numerator: 3, denominator: 4 }), 3)
assertEq(maxSlots({ numerator: 2, denominator: 4 }), 2)
assertEq(maxSlots({ numerator: 6, denominator: 8 }), 6)
assertEq(beatsPerBar({ numerator: 4, denominator: 4 }), 4)
assertEq(beatsPerBar({ numerator: 6, denominator: 8 }), 3)
var midi = triadMidi({ rootPc: 0, quality: "major" })
assertEq(midi.length, 3)
assert(midi[0] >= 48 && midi[2] <= 72, "voiced in C3–C5")
```

If any name disagrees with C++ `MusicTheoryTest`, match C++.

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: FAIL (`diatonicTriads` / `encodeChord` / `PC_NAMES` undefined, or existing `diatonic(0).I` tests if you replaced those functions first)

**Step 3: Write minimal implementation**

Replace `js/Model.js` with a `.pragma library` port of source `src/theory/MusicTheory.h` / `.cpp`:

- Stations clockwise fifths, index 0 = C / Am (table in the PRD).
- Pitch-class names: `C Db D Eb E F F# G Ab A Bb B` (C=0).
- Chord `{ rootPc, quality }` with qualities `major|minor|diminished|augmented`.
- `encodeChord` / `decodeChord`: `chord|<name>|<rootPc>|<qualityInt>`.
- `diatonicTriads(keyIndex)`: `I ii iii IV V vi vii°` (M m m M M m dim), major and relative minor share the set.
- `maxSlots(ts) = ts.numerator`; `beatsPerBar = 4 * numerator / denominator`.
- `triadMidi(chord)`: three MIDI notes voiced inside 48–72.
- Keep polar/hit-test helpers used by `CircleOfFifths.qml` **or** update the circle in Task 6 in the same commit if you drop them. Prefer keeping `wrap`, `sectorMidDeg`, `hitTest` so QML still loads until Task 6.

Do **not** keep `tonicIndexForSymbol` as a chord-entry API.

**Step 4: Run test to verify it passes**

Run: `python3 tests/run.py`

Expected: `js tests ok` and `all tests passed` (temporarily comment or rewrite old `diatonic(0).I` / `parseChord` blocks if they still target the deleted API — rewriting those blocks to the new API in this task is OK; deleting `Chords.js` tests belongs in Task 12).

**Step 5: Commit**

```bash
git add js/Model.js tests/js_tests.js tests/run.py
git commit -m "$(cat <<'EOF'
feat(music_theory): port triad naming and payloads

Match source MusicTheory so circle, slots, and agent share one chord model.
EOF
)"
```

---

### [x] Task 2: LaptopKeys JS

**Status:** `done`
**Resume:** Complete
**Commits:** 06e7dbf

**Files:**
- Modify: `js/Keyboard.js` (replace multi-layout sliding map with source `LaptopKeys.h`)
- Modify: `tests/js_tests.js`

**Step 1: Write the failing test**

```javascript
assertEq(semitoneForKey("a"), 0)
assertEq(semitoneForKey("w"), 1)
assertEq(semitoneForKey("s"), 2)
assertEq(semitoneForKey("j"), 11)
assertEq(semitoneForKey("k"), 12)
assertEq(semitoneForKey("z"), -1)
assertEq(midiForLaptopKey("a", 4), 60)
assertEq(midiForLaptopKey("w", 4), 61)
assertEq(midiForLaptopKey("k", 4), 72)
assertEq(shiftOctave(4, 1), 5)
assertEq(shiftOctave(8, 1), 8)
assertEq(shiftOctave(0, -1), 0)
assertEq(clampMidi(midiForLaptopKey("a", 0)), midiForLaptopKey("a", 0))
```

Map (semitone from C; default octave 4 → C4 = 60): A=0, W=1, S=2, E=3, D=4, F=5, T=6, G=7, Y=8, H=9, U=10, J=11, K=12, O=13, L=14, P=15, `;`=16, `'`=17.

MIDI = `(clamp(octave, 0, 8) + 1) * 12 + semitone`, then clamp 0–127.

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: FAIL (`semitoneForKey` undefined, or `midiForKey("a", 4, "qwerty")` no longer exists)

**Step 3: Write minimal implementation**

Replace layout tables in `js/Keyboard.js` with `LaptopKeys.h`. Provide `pianoKeysC3C5()` returning MIDI 48–72 (white/black metadata for QML). Keep `midiToHz`. Drop dvorak/colemak and `twoOctaveKeys` unless Task 9 still needs a shim — delete shims in Task 9/12, not here if Piano.qml would break; if Piano still imports `twoOctaveKeys`, add a deprecated wrapper that Task 9 removes.

**Step 4: Run test to verify it passes**

Run: `python3 tests/run.py`

Expected: PASS

**Step 5: Commit**

```bash
git add js/Keyboard.js tests/js_tests.js
git commit -m "$(cat <<'EOF'
feat(laptop_keys): match LaptopKeys.h MIDI map

Keep H/J/K/L as notes only when the overlay toggle is on (wired in Task 10).
EOF
)"
```

---

### [x] Task 3: Song document + slots

**Status:** `done`
**Resume:** Complete
**Commits:** 0344a9e

**Files:**
- Modify: `js/Song.js` (replace string `chords[]` with source Song document)
- Modify: `tests/js_tests.js`
- Tests: port cases from source `tests/SongModelTest.cpp`

**Step 1: Write the failing test**

```javascript
var song = defaultSong()
assertEq(song.bpm, 120)
assertEq(song.sections.length, 2)
assertEq(song.sections[0].name, "Verse")
assertEq(song.sections[0].timeSig.numerator, 4)
assertEq(song.sections[0].measures.length, 4)
assertEq(song.sections[0].measures[0].slots.length, 1)
assertEq(song.sections[0].measures[0].slots[0].span, 4)
assertEq(chordName(song.sections[0].measures[0].slots[0].chord.rootPc, song.sections[0].measures[0].slots[0].chord.quality), "C")
assertEq(chordName(song.sections[0].measures[3].slots[0].chord.rootPc, song.sections[0].measures[3].slots[0].chord.quality), "Dm")
assertEq(chordName(song.sections[1].measures[0].slots[0].chord.rootPc, song.sections[1].measures[0].slots[0].chord.quality), "D")
assertEq(removeSection(song, 0).sections.length, 2)
assertEq(removeSection(song, 0).sections[0].name, "Verse")
var one = removeSection(removeSection(addSection(song, "Bridge"), 2), 1)
assertEq(one.sections.length, 1)
var s3 = setTimeSignature(cloneSong(song), 0, { numerator: 3, denominator: 4 })
assertEq(s3.sections[0].measures.length, 3)
assertEq(slotSpanSum(s3.sections[0].measures[0]), 3)
var placed = placeChord(cloneSong(song), 0, 0, 0, { rootPc: 7, quality: "major" }, false)
assert(placed.sections[0].measures[0].slots[0].chord.rootPc === 7)
var split = placeChord(cloneSong(song), 0, 0, 0, { rootPc: 7, quality: "major" }, true)
assert(split.sections[0].measures[0].slots.length >= 2)
assertEq(slotSpanSum(split.sections[0].measures[0]), 4)
var resized = resizeSlot(cloneSong(song), 0, 0, 0, 2, "right")
assertEq(slotSpanSum(resized.sections[0].measures[0]), 4)
var cleared = setChord(cloneSong(song), 0, 0, 0, null)
assertEq(cleared.sections[0].measures[0].slots[0].chord, null)
```

Port remaining `placeChord` / `resizeSlot` / meter cases from C++ if these miss an edge. C++ wins.

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: FAIL (default song still empty string slots)

**Step 3: Write minimal implementation**

`js/Song.js` document:

```
Song { bpm, keyIndex, sections[] }
  section { name, timeSig, measures[], rowRepeats[] }
    measure { slots[] }  // spans sum to maxSlots(timeSig)
      slot { chord?: {rootPc, quality}, span }
```

- `barsForTimeSignature` = numerator; `BARS_PER_ROW = 4`.
- `addSection(name)` uses `barsForTimeSignature` empty full-bar rests; names: Verse, Chorus, Pre-Chorus, Bridge, Intro, Outro, Solo, Custom (empty → `"Section"`).
- `removeSection`: no-op if last section.
- `placeChord` / `resizeSlot`: copy algorithms from `src/model/Song.cpp`. Drop on empty fills; drop on filled halves and inserts on drop side; at max capacity replace; edge-drag shrinks span and opens empty units.
- `setBpm` clamp 40–240.
- Key change is **not** `transposeSong`. Delete `transposeSong`.
- Stop using string symbols.

QML will break until Tasks 6–7. Keep `Songwriter.qml` loading by adding temporary adapters **only if** tests require the overlay to parse — prefer breaking QML until Task 6/7 in the same workstream order (do not ship a mixed model). If the overlay must still open mid-branch, `normalizeSong` may ignore unknown old JSON and reset to default.

**Step 4: Run test to verify it passes**

Run: `python3 tests/run.py`

Expected: PASS for Song tests (QML not executed here)

**Step 5: Commit**

```bash
git add js/Song.js tests/js_tests.js
git commit -m "$(cat <<'EOF'
feat(song_structure): port Song measures and slot spans

Place/split/resize/clear match source capacity rules; key change will not transpose.
EOF
)"
```

---

### [x] Task 4: Timeline + row repeats

**Status:** `done`
**Resume:** Complete
**Commits:** e75e55e

**Files:**
- Modify: `js/Song.js` (`setRowRepeat`, `buildTimeline`)
- Modify: `tests/js_tests.js`

**Step 1: Write the failing test**

```javascript
var song = defaultSong()
var tl = buildTimeline(song)
assertEq(tl.length, 8)
var beats = 0
for (var i = 0; i < tl.length; i++) beats += tl[i].durationBeats
assertEq(beats, 32)
var repeated = setRowRepeat(cloneSong(song), 0, 0, true)
var tl2 = buildTimeline(repeated)
assertEq(tl2.length, 12)
beats = 0
for (i = 0; i < tl2.length; i++) beats += tl2[i].durationBeats
assertEq(beats, 48)
assertEq(tl2[4].repeatPass, 1)
var six = setTimeSignature(cloneSong(song), 0, { numerator: 6, denominator: 8 })
assertEq(six.sections[0].rowRepeats.length, 2)
```

Events: `{ startBeat, durationBeats, chord, rest, sectionIndex, measureIndex, slotIndex, repeatPass }`. Empty slots `rest: true`. First pass `repeatPass=0`, second `1`. Only the toggled 4-bar row duplicates.

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: FAIL (`buildTimeline` undefined)

**Step 3: Write minimal implementation**

Port `src/model/Timeline.cpp`. `slotDurationBeats = span * (4 / denominator)`. 6/8 section with 6 bars → two rows and two flags.

**Step 4: Run test to verify it passes**

Run: `python3 tests/run.py`

Expected: PASS

**Step 5: Commit**

```bash
git add js/Song.js tests/js_tests.js
git commit -m "$(cat <<'EOF'
feat(row_repeats): build timeline with row :||

Playback can walk spans, meter, and repeatPass instead of flat string slots.
EOF
)"
```

---

### [x] Task 5: Agent JSON

**Status:** `done`
**Resume:** Complete
**Commits:** 4bf4fdd ace6ba1

**Files:**
- Create: `js/Agent.js` (progressions + song document serializers; port `src/api/SongJson.cpp`)
- Modify: `tests/js_tests.js`
- Modify: `tests/run.py` (load `js/Agent.js` into the VM)

**Step 1: Write the failing test**

```javascript
var song = defaultSong()
song.keyIndex = 0
var p = progressionsJson(song)
assertEq(p.key.major, "C")
assertEq(p.bpm, 120)
assert(p.sections[0].progression.indexOf("C") !== -1)
assertEq(p.sections[0].chords[0].numeral, "I")
var doc = songJson(song)
assertEq(doc.sections[0].measures[0].slots[0].rootPc, 0)
assertEq(songJson(setChord(cloneSong(song), 0, 0, 0, null)).sections[0].measures[0].slots[0], null)
```

`progressions`: omit empty slots from `chords`; show `-` in `progression`; `numeral` only when diatonic in current key.

`song`: every slot present; empty → `null`; chord objects omit `bar`/`slot` (index is position).

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: FAIL (`progressionsJson` undefined)

**Step 3: Write minimal implementation**

Match shapes in the PRD. If C++ `AgentApiTest` differs, match C++.

**Step 4: Run test to verify it passes**

Run: `python3 tests/run.py`

Expected: PASS

**Step 5: Commit**

```bash
git add js/Agent.js tests/js_tests.js tests/run.py
git commit -m "$(cat <<'EOF'
feat(agent_api): serialize progressions and song JSON

Live HTTP in Task 11 can reuse the same document shapes.
EOF
)"
```

---

### [x] Task 6: Circle of fifths UI

**Status:** `done`
**Resume:** Complete
**Commits:** dde7386 ae4c9be 3ea684d

**Files:**
- Modify: `CircleOfFifths.qml`
- Modify: `Songwriter.qml` (tonic change, preview, drag; **do not transpose** placed chords)

**Step 1: Write the failing test**

No QML runner in CI. Add a JS helper test if you extract `rotate(keyIndex, delta)` in `Model.js`:

```javascript
assertEq(wrap(0 + 1), 1)
assertEq(wrap(0 - 1), 11)
```

Manual parity (Task 12 / Omarchy box): rotate by click / wheel / h/l / arrows; active wedge at 12 o'clock; chips I–vii°; click chip = preview only; drag starts `chord|…`.

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: PASS for JS; overlay still wrong until this task's QML lands

**Step 3: Write minimal implementation**

- 12 stations; outer major, inner relative minor; **rotate** selected key to 12 o'clock (do not only highlight in place).
- Seven chips from `diatonicTriads`. Click → `onChordPreview` (piano highlight + short audition). Click does **not** insert or change key.
- Drag wedge or chip → `encodeChord` payload.
- Remove `toneMode` / 1–6 degree play (not in source maps).
- `Songwriter.qml`: `onTonicPicked` updates `keyIndex` / rotation / chips only — delete `transposeSong` / `insertSymbol` on preview.

Use existing `Color` / `Style` / `Button`. Title string **Chords & Tabs**.

**Step 4: Run test to verify it passes**

Run: `python3 tests/run.py`

Expected: PASS

**Step 5: Commit**

```bash
git add CircleOfFifths.qml Songwriter.qml js/Model.js tests/js_tests.js
git commit -m "$(cat <<'EOF'
feat(circle_of_fifths): rotate key and drag triad payloads

Key changes update chips only; placed chords stay put.
EOF
)"
```

---

### [x] Task 7: Song structure + slots + :|| UI

**Status:** `done`
**Resume:** Complete
**Commits:** 2d2129b 9914fc2 78b41eb

**Files:**
- Modify: `SongStructure.qml` (rewrite against measures/slots; drop `Chords.js` typing)
- Modify: `Songwriter.qml` (wire place/split/resize/clear, meter menu, append names)

**Step 1: Write the failing test**

JS already covers model. Overlay checklist (verify on Omarchy in Task 12): default Verse/Chorus not empty; append names; cannot delete last; time-signature menu `4/4 (4 bars)` … `6/8 (6 bars)`; drop/split/edge-resize/hover-×; `:||` per row.

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: PASS (JS); QML still string-based until this change

**Step 3: Write minimal implementation**

Replace section `chords[]` Repeater with rows of 4 measures, each measure a row of slots sized by `span`. Drop target calls `Song.placeChord` with `insertAfter` from drop X. Edge handles call `resizeSlot`. Hover × calls `setChord(..., null)`. Click filled slot → audition signal (playback wired in Task 8). Repeat control at row end calls `setRowRepeat`.

Remove `beginEdit` / `TextInput` chord entry and suggestion chips.

Append control: Verse, Chorus, Pre-Chorus, Bridge, Intro, Outro, Solo, Custom.

**Step 4: Run test to verify it passes**

Run: `python3 tests/run.py`

Expected: PASS

**Step 5: Commit**

```bash
git add SongStructure.qml Songwriter.qml
git commit -m "$(cat <<'EOF'
feat(chord_slots): drop, split, resize, and clear in QML

Section meter and :|| follow the Song document instead of typed symbols.
EOF
)"
```

---

### [x] Task 8: Playback + transport

**Status:** `done`
**Resume:** Complete
**Commits:** b1b3624 54ba6de 94ddc72 029d4b9

**Files:**
- Modify: `Songwriter.qml` (playhead walks `buildTimeline`; Space play/stop)
- Modify: `Transport.qml` (remove tap tempo)
- Test: `tests/js_tests.js` (optional: `durationBeats` vs BPM seconds helper)

**Step 1: Write the failing test**

```javascript
var song = defaultSong()
var tl = buildTimeline(song)
assertEq(tl[0].durationBeats, 4)
assertEq(tl[0].rest, false)
```

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: FAIL only if duration helper missing; otherwise FAIL is behavioral in QML

**Step 3: Write minimal implementation**

- Play / Stop / Loop / BPM 40–240.
- Timer: advance `currentBeat` from timeline `startBeat`/`durationBeats` (quarter-note beats at `song.bpm`), not “every slot is one bar of 4”.
- Loop wraps `currentBeat` to 0.
- Playhead on current slot; `soundingNotes = triadMidi(event.chord)` for piano.
- Audition: play one slot for `slotDurationBeats` then cancel scheduled song play for that voice.
- Remove `tapTempo`, `tapTimes`, Transport tap button, Space-as-sustain.
- Space toggles play/stop when laptop mapping is off.

**Step 4: Run test to verify it passes**

Run: `python3 tests/run.py`

Expected: PASS

**Step 5: Commit**

```bash
git add Songwriter.qml Transport.qml tests/js_tests.js
git commit -m "$(cat <<'EOF'
feat(playback): walk timeline events at BPM

Playhead and sounding notes follow span, meter, and repeats; no tap tempo.
EOF
)"
```

---

### [x] Task 9: Piano C3–C5 + instruments + PipeWire

**Status:** `done`
**Resume:** Complete
**Commits:** a15026a

**Files:**
- Modify: `Piano.qml` (fixed C3–C5; SoundPicker; laptop glyph placeholder)
- Modify: `Songwriter.qml` / persist instrument
- Modify: `play-notes.py` (`--instrument` 0–4; sine stand-ins with slight timbre differences OK)
- Modify: `tests/run.py` (wav still writes; optional instrument flag)

**Step 1: Write the failing test**

In `tests/js_tests.js`:

```javascript
var keys = pianoKeysC3C5()
assertEq(keys[0].midi, 48)
assertEq(keys[keys.length - 1].midi, 72)
```

Python: `python3 play-notes.py --write /tmp/x.wav --midi 60 64 67 --instrument 1 --seconds 0.12` must succeed (extend `test_play_notes` in `tests/run.py`).

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: FAIL (`pianoKeysC3C5` missing and/or unknown `--instrument`)

**Step 3: Write minimal implementation**

- Piano MIDI 48–72 inclusive; click note on while held.
- Highlight union of playback, circle preview, selected slot.
- Instruments wrap: Piano, Electric Piano, Organ, Pad, Strings. Chevrons on piano row. Persist `instrument` with song prefs (`write-json.py` path can stay until Task 11 snapshots).
- Same timbre for play, audition, preview, live notes.
- `play-notes.py`: accept `--instrument`; still `pw-play` / `paplay` / `aplay`. No Device button.

**Step 4: Run test to verify it passes**

Run: `python3 tests/run.py`

Expected: `play-notes wav bytes …` and `all tests passed`

**Step 5: Commit**

```bash
git add Piano.qml Songwriter.qml js/Keyboard.js play-notes.py tests/run.py tests/js_tests.js
git commit -m "$(cat <<'EOF'
feat(piano_keyboard): fix C3–C5 range and five timbres

PipeWire remains the only output path; sine stand-ins are enough.
EOF
)"
```

---

### [x] Task 10: Region focus + laptop toggle

**Status:** `done`
**Resume:** Complete
**Commits:** 63e6887 08efeb5 48b35dd

**Files:**
- Modify: `Songwriter.qml` (j/k/h/l, hint, focus frame)
- Modify: `Piano.qml` (glyph toggle; Z/X octave when map on)
- Optional: `js/Focus.js` if it keeps QML thin — otherwise keep cycle in the host

**Step 1: Write the failing test**

```javascript
assertEq(cycleNavRegion(0, 1), 1)
assertEq(cycleNavRegion(2, 1), 0)
assertEq(cycleNavRegion(0, -1), 2)
assertEq(regionName(0), "Circle of fifths")
assertEq(regionName(1), "Song structure")
assertEq(regionName(2), "Keyboard")
```

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: FAIL (`cycleNavRegion` undefined)

**Step 3: Write minimal implementation**

- Regions 0 Circle, 1 Song, 2 Keyboard; j down, k up; wrap.
- Header hint = current region name (and laptop-on warning if needed).
- Focus frame around the active region.
- h/l: Circle → previous/next key; Keyboard → previous/next instrument; Song → no-op.
- ←/→ and wheel still rotate the circle in any region.
- Laptop glyph **off by default**. When on, `handleComputerKey` uses `midiForLaptopKey`; Z/X `shiftOctave`; H/J/K/L are notes. When off, those keys are nav. Space is never sustain.

**Step 4: Run test to verify it passes**

Run: `python3 tests/run.py`

Expected: PASS

**Step 5: Commit**

```bash
git add Songwriter.qml Piano.qml js/Focus.js tests/js_tests.js tests/run.py
git commit -m "$(cat <<'EOF'
feat(region_focus): vim regions and optional laptop map

h/l follow focus; laptop mapping off until the piano glyph is enabled.
EOF
)"
```

---

### [x] Task 11: chords-agent HTTP + CLI

**Status:** `done`
**Resume:** Complete
**Commits:** cd08441 fb1b3eb

**Files:**
- Create: `chords-agent` (Python CLI: `progressions`, `song`, `health`; `--live`)
- Create: `agent-server.py` (or embed in overlay) — loopback HTTP GET `/progressions`, `/song`, `/health`
- Modify: `Songwriter.qml` (bind 127.0.0.1:17891 or `$CHORDS_AGENT_PORT` or `agent-api.json`; always write snapshots)
- Modify: `write-json.py` if snapshot paths need create-dirs (already creates)
- Modify: `tests/run.py` (CLI against a fixture snapshot; optional live skip)
- Modify: `AGENTS.md` (how agents call the CLI)

**Step 1: Write the failing test**

Add `tests/agent_tests.py` invoked from `tests/run.py`:

- Write a snapshot dir with `progressions.json` / `song.json` from `progressionsJson`/`songJson` fixtures.
- `CHORDS_AGENT_HOME=<tmp> python3 ./chords-agent song` prints JSON with `sections`.
- `CHORDS_AGENT_HOME=<tmp> python3 ./chords-agent health` exits 2 without a live server.
- `--live` with nothing bound exits 2.

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: FAIL (missing `chords-agent`)

**Step 3: Write minimal implementation**

- Port: 17891, else `$CHORDS_AGENT_PORT`, else `agent-api.json`.
- Snapshots: `$CHORDS_AGENT_HOME` or `~/.config/chords-and-tabs/` (PRD). Overlay still writes if bind fails.
- Do not infer the song from defaults when reading — use live GET or last snapshot.
- Persist last song + key in source JSON shape (not the old `title`/`chords[]` file only). Migrate: if old `~/.local/state/omarchy/songwriter/song.json` cannot normalize, ignore and use default.

**Step 4: Run test to verify it passes**

Run: `python3 tests/run.py`

Expected: PASS including agent tests. Live overlay check is Task 12 on Omarchy.

**Step 5: Commit**

```bash
git add chords-agent agent-server.py Songwriter.qml tests/run.py tests/agent_tests.py AGENTS.md write-json.py
git commit -m "$(cat <<'EOF'
feat(agent_api): add chords-agent loopback and snapshots

Agents read progressions, song, and health without inferring defaults.
EOF
)"
```

---

### [x] Task 12: Remove non-parity paths + maps

**Status:** `done`
**Resume:** Complete
**Commits:** 1d5cf70

**Files:**
- Delete: `js/Chords.js` if unused
- Modify: `Songwriter.qml` (no `import js/Chords.js`; title **Chords & Tabs**; Esc closes; clicks outside pass through — already masked)
- Modify: `tests/js_tests.js` / `tests/run.py` (drop parseChord / transpose / Cmaj7 cases)
- Modify: `.features/*.yaml` `notes` (remove “not implemented” once true)
- Modify: `README.md` (status + spec link already to PRD; install still valid)
- Modify: `LICENSE` / `manifest.json` only if product already decided GPLv3 vs MIT (PRD open question — do not change license without an explicit owner decision)

**Step 1: Write the failing test**

`tests/js_tests.js` must not reference `parseChord`, `transposeChord`, `getChordSuggestions`, `twoOctaveKeys` as product APIs.

Grep:

```bash
rg -n "parseChord|transposeSong|tapTempo|Cmaj7|toneMode" --glob '!docs/**' --glob '!.git/**'
```

Expected after this task: no product-path hits (tests/docs/PRD mentions OK).

**Step 2: Run test to verify it fails**

Run the grep before deleting — it should still list Chords.js / tap / toneMode if leftover.

**Step 3: Write minimal implementation**

Delete dead code. Patch feature-map `notes` to remaining caveats only (e.g. Omarchy box not in CI).

Run:

```bash
./bin/feature-map validate
./bin/feature-map check
python3 tests/run.py
```

On a real Omarchy machine (not required for CI green):

```bash
omarchy plugin validate ~/.config/omarchy/plugins/io.github.markschellhas.songwriter
```

Checklist: bar chip toggle, overlay, Esc, drag chord, play, `chords-agent progressions|song|health`.

**Step 4: Run test to verify it passes**

Run: `python3 tests/run.py && ./bin/feature-map validate && ./bin/feature-map check`

Expected: `all tests passed`; `Validated 12 feature maps: all passed.`; `No stale paths detected.`

**Step 5: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
refactor: drop typed chords and document parity maps

The overlay follows the twelve source capabilities only.
EOF
)"
```

---

## Test commands (this repo)

```bash
python3 tests/run.py
./bin/feature-map validate
./bin/feature-map check
omarchy plugin validate ~/.config/omarchy/plugins/io.github.markschellhas.songwriter
```

`omarchy plugin validate` needs Omarchy; CI uses the first three.

## Related skills

- **verification-before-completion** — run the commands above before claiming a task `done`
- **git-commit** — conventional commits as in each Step 5
- **web-app-design** — existing QML `Style` / `Color` / `qs.Ui`; no new visual system
- **subagent-driven-development** — execute this plan task-by-task
