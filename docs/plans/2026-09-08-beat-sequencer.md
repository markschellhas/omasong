# Beat Sequencer Implementation Plan

> **For agent:** REQUIRED SUB-SKILL: Use subagent-driven-development to implement this plan task-by-task.
> Update each task's **Status** as work advances (not only at the end). Progress bar counts only `done` tasks.
> On resume: read **Progress** + each task's **Status** / **Resume** — do not re-do completed phases.

**Goal:** Add optional per-measure kick, snare, and hi-hat sequencing synchronized with chord playback.

**Architecture:** `js/Song.js` remains the canonical normalized song and transport-event model. QML renders and edits beat patterns alongside chord measures, while `play-notes.py` pre-renders a complete measure of percussion launched at the measure boundary by the existing transport.

**Areas affected:** QML overlay, JavaScript song/agent libraries, Python audio helper, tests, documentation, feature maps

**Tech Stack:** Qt Quick/QML, QML JavaScript, Node test harness, Python WAV rendering, PipeWire/PulseAudio/ALSA helper playback

**Feature map:** `.features/beats.yaml`

**PRD:** `docs/prds/prd-beat-sequencer.md`

## Progress

**Status:** `█████████████████████` 3/3 done (100%) · 0 in flight

| # | Task | Status | Next |
|---|------|--------|------|
| 1 | Beat data model and serialization | `done` | complete |
| 2 | Percussion renderer and transport | `done` | complete |
| 3 | Beat lane, sequencer UI, and maps | `done` | complete |

---

### [x] Task 1: Beat data model and serialization

**Status:** `done`
**Resume:** Complete.
**Commits:** e76d663eb120ec4ef0cda665e0887c14f7fc5ad5

**Files:**
- Modify: `js/Song.js`
- Modify: `js/Agent.js`
- Modify: `tests/js_tests.js`

**Step 1: Write the failing tests**

Add JavaScript tests proving that 4/4, 3/4, and 6/8 measures normalize to 16, 12, and 12 steps; legacy songs receive empty patterns; invalid and oversized values become booleans within the correct length; `toggleBeat` changes only the requested measure/lane/step; clone, add-bars, remove-measure emptiness, and meter changes preserve valid patterns; and `Agent.songJson` includes patterns while progressions remain chord-focused.

**Step 2: Run tests to verify they fail**

Run: `python3 tests/run.py`
Expected: FAIL because beat-pattern helpers and serialized fields do not exist.

**Step 3: Write minimal implementation**

In `js/Song.js`, define `BEAT_LANES = ["kick", "snare", "hihat"]`, calculate sixteenth-note step count as `numerator * 16 / denominator` with safe bounds, normalize each lane to booleans, attach `beats` to every copied/created measure, add `getBeats`, `toggleBeat`, `hasBeat`, and `isBeatPatternEmpty`, resize patterns on time-signature changes, and treat percussion as measure content when trimming. Preserve a `beatsVisible` boolean through song normalization. In `js/Agent.js`, serialize each measure as `{ slots, beats }` in the full song document only.

**Step 4: Run tests and verify pass**

Run: `python3 tests/run.py`
Expected: all tests pass.

**Step 5: Commit**

```bash
git add js/Song.js js/Agent.js tests/js_tests.js docs/prds/prd-beat-sequencer.md docs/plans/2026-09-08-beat-sequencer.md
git commit -m "feat(beats): add beat pattern model"
```

### [x] Task 2: Percussion renderer and transport

**Status:** `done`
**Resume:** Complete.
**Commits:** f19d0eb12893f78983949ea38097b4d92b1b3fb5, 09dd9cd, bf2b8a7

**Files:**
- Modify: `play-notes.py`
- Modify: `Songwriter.qml`
- Modify: `tests/run.py`
- Modify: `tests/js_tests.js`

**Step 1: Write the failing tests**

Test bounded pattern parsing and a drum-mode WAV containing non-silent kick, snare, and hi-hat transients at requested steps. Add pure JavaScript coverage for detecting the first event of a measure/pass so a pattern launches exactly once per normal bar, section playback bar, loop pass, and row-repeat pass.

**Step 2: Run tests to verify they fail**

Run: `python3 tests/run.py`
Expected: FAIL because drum rendering and measure-boundary helpers do not exist.

**Step 3: Write minimal implementation**

Extend `play-notes.py` with mutually exclusive `--drums KICK SNARE HIHAT`, `--steps`, and `--bpm` inputs. Synthesize a bounded mono measure WAV with short kick pitch decay, deterministic snare noise, and hi-hat noise transients at sixteenth-note offsets. In `Songwriter.qml`, encode and launch a non-empty pattern at the first timeline event for each measure/repeat pass, using the same BPM and playhead transition as chord playback. Empty patterns launch nothing. Preserve `beatsVisible` in `seedSong`, `updateSong`, `applySongFields`, and named-library documents.

**Step 4: Run tests and verify pass**

Run: `python3 tests/run.py`
Expected: all tests pass and drum WAV checks report success.

**Step 5: Commit**

```bash
git add play-notes.py Songwriter.qml tests/run.py tests/js_tests.js
git commit -m "feat(beats): sync drums with transport"
```

### [x] Task 3: Beat lane, sequencer UI, and maps

**Status:** `done`
**Resume:** Complete.
**Commits:** 153a31d, PENDING_SHA

**Files:**
- Create: `BeatSequencer.qml`
- Modify: `Transport.qml`
- Modify: `SongStructure.qml`
- Modify: `Songwriter.qml`
- Create: `.features/beats.yaml`
- Modify: `.features/song_structure.yaml`
- Modify: `.features/playback.yaml`
- Modify: `.features/song_library.yaml`
- Modify: `.features/agent_api.yaml`
- Modify: `README.md`

**Step 1: Add the visibility control and lane**

Add a bordered `Beats` button beside Loop using the existing `Button` primitive. When enabled, each bar row grows to include a second lane beneath its chord measure. Match the chord measure's width, radius, faint border, spacing, playback highlight, and responsive four-bar layout. Summarize kick/snare/hi-hat hits without introducing new colors or typography.

**Step 2: Add the sequencer panel**

Create `BeatSequencer.qml` as a restrained overlay panel with bar context, Close/Clear controls, three labeled rows, quarter-beat separators, and one keyboard-focusable step button per sixteenth note. Toggle steps through a signal owned by `Songwriter.qml`; do not mutate model objects in place. Support Escape to close and keep every label readable with existing font and spacing tokens.

**Step 3: Wire integration behavior**

Pass `beatsVisible`, current playing measure, and pattern data through `SongStructure.qml`. Clicking any beat lane opens the editor for that exact section/measure. Pattern toggles call `Song.toggleBeat` and autosave. Closing, loading another song, and hiding beat lanes close the editor cleanly.

**Step 4: Update architectural documentation**

Create the dense `beats` feature map, connect all affected related features, and update the README feature table. Run `./bin/feature-map validate` and `./bin/feature-map check`.

**Step 5: Verify UI and full suite**

Run: `python3 tests/run.py`
Run: `./bin/feature-map validate`
Run: `./bin/feature-map check`
Run: `omarchy plugin validate /home/ms/.config/omarchy/plugins/markschellhas.songwriter`
Expected: automated suite and map checks pass; host validator accepts all QML components.

**Step 6: Commit**

```bash
git add BeatSequencer.qml Transport.qml SongStructure.qml Songwriter.qml .features README.md docs/plans/2026-09-08-beat-sequencer.md
git commit -m "feat(beats): add measure sequencer UI"
```
