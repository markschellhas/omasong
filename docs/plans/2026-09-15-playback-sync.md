# Playback Sync Implementation Plan

> **For agent:** REQUIRED SUB-SKILL: Use subagent-driven-development to implement this plan task-by-task.
> Update each task's **Status** as work advances (not only at the end). Progress bar counts only `done` tasks.
> On resume: read **Progress** + each task's **Status** / **Resume** — do not re-do completed phases.

**Goal:** Make kicks and chords start on beat 1 of each bar by playing from a persistent sample clock instead of spawning `play-notes.py` at the visual downbeat.

**Architecture:** `js/Song.js` already freezes a per-measure audio spec at the first slot of a drum bar. Extend that freeze to every bar, walk the playhead from wall clock, and let a long-lived `play-notes.py --engine` process pre-render those specs onto one PCM stream (`pw-cat --raw` at 20 ms latency). Drum tails mix into the next bar; they must not delay the next downbeat.

**Areas affected:** `js/Song.js`, `play-notes.py`, `Songwriter.qml`, tests, `.features/playback.yaml`, `.features/beats.yaml`, `.features/audio_device.yaml`

**Tech Stack:** Qt Quick/QML (Quickshell `Process` + `SplitParser`), QML JavaScript, Python WAV/PCM renderer, PipeWire `pw-cat`

**Feature map:** `.features/playback.yaml`, `.features/beats.yaml`, `.features/audio_device.yaml`

**PRD:** `docs/prds/prd-playback-sync.md`

## Progress

**Status:** `████████████████████` 5/5 done (100%) · 0 in flight

| # | Task | Status | Next |
|---|------|--------|------|
| 1 | Always-on measure specs + wall-clock beat | `done` | complete |
| 2 | Sample-accurate measure scheduler | `done` | complete |
| 3 | Persistent `--engine` protocol | `done` | complete |
| 4 | QML engine process and transport clock | `done` | complete |
| 5 | Feature maps and README | `done` | complete |

---

### Diagnosis (do not re-investigate)

Playback is late because audio work starts *after* the playhead is already on beat 1:

1. `Songwriter.qml` `applyPlayhead` → `Quickshell.execDetached(["python3", play-notes.py, "--measure"| "--midi", …])` at the moment the bar/slot changes (`Songwriter.qml` `playMeasureAudio` / `playMidiNotes`).
2. Cold Python + `_SAMPLE_CACHE` miss + render + temp WAV.
3. `pw-play` default node latency is **100 ms** (`pw-cat --help`).
4. Chained `transportTimer` intervals drift from wall clock; they are not the audio clock.
5. Unpatterned chords also prepend `PAD` (20 ms) of silence; combined-measure mixing strips that pad, so drums+chords and chord-only bars are late by different amounts.

Kick/snare/hi-hat *inside* a rendered WAV already sit on the correct sixteenth. The WAV itself starts late. Fix the clock; do not offset step indices.

---

### [x] Task 1: Always-on measure specs + wall-clock beat

**Status:** `done`
**Resume:** Complete
**Commits:** 9dd5f0af

**Files:**
- Modify: `js/Song.js`
- Modify: `tests/js_tests.js`

**Step 1: Write the failing tests**

In `tests/js_tests.js`, after the existing timeline assertions, replace the “unpatterned measure keeps per-chord audio” expectation and add clock helpers.

```javascript
assertEq(typeof beatAtWallClock, "function")
assertEq(beatAtWallClock(1000, 1000, 120), 0)
assertEq(beatAtWallClock(1000, 1500, 120), 1)
assertEq(beatAtWallClock(1000, 2000, 120), 2)
assertEq(beatAtWallClock(1000, 500, 120), 0, "before start stays at 0")
assertEq(beatAtWallClock(0, 1000, 60), 1)

var defaultTl = buildTimeline(defaultSong())
assert(defaultTl[0].measureAudio, "every measure freezes an audio spec")
assertEq(defaultTl[0].measureAudio.chords.length, 1)
assertEq(defaultTl[1].measureAudio, null, "only the measure start carries the spec")
assertEq(defaultTl[0].patternedMeasure, false)
assertEq(defaultTl[0].measureAudio.beats.kick.length, 16)

var launches = measureLaunchEvents(defaultTl)
assertEq(launches.length, 8)
assertEq(launches[0].startBeat, 0)
assertEq(launches[1].startBeat, 4)
assert(launches[0].measureAudio.chords[0].chord)

var restSong = setChord(cloneSong(defaultSong()), 0, 0, 0, null)
var restLaunch = measureLaunchEvents(buildTimeline(restSong))[0]
assertEq(restLaunch.measureAudio.chords.length, 0, "rest measure still launches silence")
assertEq(restLaunch.measureStart, true)
```

Keep the patterned-measure tests, but change the unpatterned line:

```javascript
assertEq(patternedTimeline[3].patternedMeasure, false, "empty beat pattern stays unpatterned")
assert(patternedTimeline[3].measureAudio, "unpatterned measure still freezes chords for the engine")
```

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: FAIL (`beatAtWallClock is not defined` and/or `every measure freezes an audio spec`).

**Step 3: Write minimal implementation**

In `js/Song.js` `appendMeasure`, always build `measureAudio` (chords may be empty; beats may be all false):

```javascript
var measureAudio = {
  steps: beatStepCount(section.timeSig),
  beats: normalizeBeatPattern(measure.beats, beatStepCount(section.timeSig)),
  chords: measureChords
}
```

Keep `patternedMeasure = !isBeatPatternEmpty(measure)` for UI / “has drums”, but do not use it to omit `measureAudio`.

Add:

```javascript
function beatAtWallClock(startMs, nowMs, bpm) {
  var start = Number(startMs)
  var now = Number(nowMs)
  if (!isFinite(start) || !isFinite(now))
    return 0
  var elapsed = (now - start) / 1000
  if (!(elapsed > 0))
    return 0
  return elapsed * (Number(bpm) > 0 ? Number(bpm) : 120) / 60
}

function measureLaunchEvents(events) {
  var launches = []
  if (!events)
    return launches
  for (var i = 0; i < events.length; i++) {
    if (events[i] && events[i].measureStart)
      launches.push(events[i])
  }
  return launches
}
```

**Step 4: Run tests and verify pass**

Run: `python3 tests/run.py`

Expected: `js tests ok` and the rest of the suite pass.

**Step 5: Commit**

```bash
git add js/Song.js tests/js_tests.js docs/prds/prd-playback-sync.md docs/plans/2026-09-15-playback-sync.md
git commit -m "$(cat <<'EOF'
fix(playback): freeze audio spec for every bar

Transport will queue chords and drums from the same
measure snapshot, including bars with no beat pattern.
EOF
)"
```

---

### [x] Task 2: Sample-accurate measure scheduler

**Status:** `done`
**Resume:** Complete
**Commits:** bf49ec6d

**Files:**
- Modify: `play-notes.py`
- Modify: `tests/run.py`

**Step 1: Write the failing tests**

In `test_play_notes()` after the combined-measure checks:

```python
    m0 = {
        "steps": 8,
        "bpm": 120,
        "instrument": 0,
        "drums": {"kick": "10000000", "snare": "00000000", "hihat": "00000000"},
        "chords": [{"offsetBeats": 0, "durationBeats": 0.5, "midis": [60, 64, 67]}],
    }
    m1 = {
        "steps": 8,
        "bpm": 120,
        "instrument": 0,
        "drums": {"kick": "10000000", "snare": "00000000", "hihat": "00000000"},
        "chords": [],
    }
    scheduled = play_notes.schedule_measures([m0, m1])
    nominal, _tail = play_notes.measure_frame_counts(8, 120)
    if len(scheduled) < nominal * 2:
        raise SystemExit("scheduled timeline is shorter than two nominal measures")
    window0 = scheduled[: int(play_notes.RATE * 0.04)]
    window1 = scheduled[nominal : nominal + int(play_notes.RATE * 0.04)]
    if max(abs(s) for s in window0) < 100:
        raise SystemExit("measure 0 downbeat is silent")
    if max(abs(s) for s in window1) < 100:
        raise SystemExit("measure 1 downbeat is not on the next bar")

    late = {
        "steps": 8,
        "bpm": 120,
        "instrument": 0,
        "drums": {"kick": "00000001", "snare": "00000000", "hihat": "00000000"},
        "chords": [],
    }
    overlapped = play_notes.schedule_measures([late, m1])
    # Last-step kick of bar 1 must be audible in bar 2 without delaying bar 2's kick.
    tail_into_next = overlapped[nominal : nominal + int(play_notes.RATE * 0.08)]
    if max(abs(s) for s in tail_into_next) < 100:
        raise SystemExit("drum tail was cut instead of mixed into the next bar")
    if max(abs(s) for s in overlapped[nominal : nominal + int(play_notes.RATE * 0.04)]) < 100:
        raise SystemExit("next-bar kick missing after tail mix")
```

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: FAIL (`module 'play_notes' has no attribute 'schedule_measures'`).

**Step 3: Write minimal implementation**

In `play-notes.py`, add `schedule_measures` next to `render_measure`. Render each spec with the existing drum mix + chord mix, but place measure *n* at `sum(nominal_frames[:n])`. Allocate `sum(nominal) + max(tails)` frames so the last bar’s decay still fits. Mix into the shared buffer; do not concatenate `nominal+tail` WAVs end-to-end (that would delay the next downbeat by `DRUM_TAIL_SECONDS`).

```python
def schedule_measures(specs: list[object]) -> array:
    normalized = [normalize_measure_spec(spec) for spec in specs]
    if not normalized:
        return array("h")
    placements: list[tuple[dict, int, int]] = []
    cursor = 0
    max_end = 0
    for spec in normalized:
        nominal, tail = measure_frame_counts(spec["steps"], spec["bpm"])
        placements.append((spec, cursor, nominal))
        max_end = max(max_end, cursor + nominal + tail)
        cursor += nominal
    mix = array("f", [0.0]) * max(1, max_end)
    for spec, start, _nominal in placements:
        rendered, _ = _drum_mix(
            spec["drums"]["kick"],
            spec["drums"]["snare"],
            spec["drums"]["hihat"],
            spec["steps"],
            spec["bpm"],
        )
        pad_frames = int(RATE * PAD)
        for chord in spec["chords"]:
            chord_start = int(round(RATE * chord["offsetBeats"] * 60.0 / spec["bpm"]))
            seconds = chord["durationBeats"] * 60.0 / spec["bpm"]
            pcm = render_midi_notes(chord["midis"], seconds, spec["instrument"])
            audio = pcm[pad_frames : max(pad_frames, len(pcm) - pad_frames)]
            for i, sample in enumerate(audio):
                idx = start + chord_start + i
                if 0 <= idx < len(mix):
                    mix[idx] += sample / 32767.0
        for i, sample in enumerate(rendered):
            idx = start + i
            if 0 <= idx < len(mix):
                mix[idx] += sample
    return _finish_mix(mix)
```

Refactor `render_measure` to `return schedule_measures([value])` so one-bar `--write --measure` stays identical in clock (plus the existing tail). If `_finish_mix` peak scaling makes a one-bar render differ by a few LSBs, keep `render_measure` as today’s single-bar path and only use `schedule_measures` for 2+ bars / engine play — but then add a one-bar `schedule_measures([spec])` assertion that downbeat 0 is still non-silent.

**Step 4: Run tests and verify pass**

Run: `python3 tests/run.py`

Expected: `play-notes combined measure ok` and the new scheduler checks pass.

**Step 5: Commit**

```bash
git add play-notes.py tests/run.py
git commit -m "$(cat <<'EOF'
fix(playback): schedule bars on one sample clock

Next downbeat starts at the previous bar's nominal length.
Drum tails mix forward instead of delaying beat 1.
EOF
)"
```

---

### [x] Task 3: Persistent `--engine` protocol

**Status:** `done`
**Resume:** Complete
**Commits:** 96ab7287, 7e441b6e

**Files:**
- Modify: `play-notes.py`
- Modify: `tests/run.py`

**Step 1: Write the failing tests**

Protocol is one JSON object per line on stdin; one JSON object per line on stdout. Tests use a buffer sink so CI does not need PipeWire.

```python
    engine = play_notes.AudioEngine(sink=play_notes.BufferSink())
    ready = engine.handle({"cmd": "warmup", "instrument": 0})
    if not ready.get("ok"):
        raise SystemExit("warmup must succeed without PipeWire")
    started = engine.handle({
        "cmd": "play",
        "loop": False,
        "latencyMs": 20,
        "measures": [m0, m1],
    })
    if started.get("event") != "started":
        raise SystemExit("play must emit started")
    pcm = engine.sink.frames
    if max(abs(s) for s in pcm[: int(play_notes.RATE * 0.04)]) < 100:
        raise SystemExit("engine play did not write the first downbeat")
    stopped = engine.handle({"cmd": "stop"})
    if not stopped.get("ok"):
        raise SystemExit("stop must succeed")
    note = engine.handle({
        "cmd": "play-midi",
        "midis": [60, 64, 67],
        "seconds": 0.12,
        "instrument": 0,
    })
    if not note.get("ok"):
        raise SystemExit("play-midi must mix onto the engine sink")

    proc = subprocess.run(
        [sys.executable, str(ROOT / "play-notes.py"), "--engine"],
        input=json.dumps({"cmd": "warmup", "instrument": 0}) + "\n"
        + json.dumps({"cmd": "shutdown"}) + "\n",
        capture_output=True,
        text=True,
        timeout=20,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + proc.stderr)
        raise SystemExit("engine process failed")
    lines = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    if not lines or not lines[0].get("ok"):
        raise SystemExit("engine stdin protocol did not ACK warmup")
```

Also assert `play_notes.output_command()` prefers:

```
["pw-cat", "-p", "-a", "--format", "s16", "--rate", "44100", "--channels", "1", "--latency", "20ms"]
```

when `pw-cat` is on PATH. Do not run `pw-cat` in CI.

**Step 2: Run test to verify it fails**

Run: `python3 tests/run.py`

Expected: FAIL (`AudioEngine` missing).

**Step 3: Write minimal implementation**

In `play-notes.py`:

- `OUTPUT_LATENCY_MS = 20`
- `BufferSink` appends s16 frames to `self.frames`.
- `PipeSink` spawns `output_command()` once, writes raw little-endian s16, and keeps the process open. On idle after `stop`, write zeros in `OUTPUT_LATENCY_MS`-sized blocks on a short cadence *or* simply close stdin to pw-cat and reopen on next `play` — prefer **keep-open with silence** so Play does not pay a stream handshake. If keep-open is awkward in tests, BufferSink is enough for CI; PipeSink can lazy-open on first `play` as long as QML warms up with `warmup` then a silent `play` of empty measures is not required.
- `AudioEngine.handle(msg)`:
  - `warmup`: clamp instrument, touch `sample_bank_ready`, `{ok: true}`
  - `play`: `pcm = schedule_measures(msg["measures"])`; write to sink; `{event: "started", frames: len(pcm), latencyMs: 20}`
  - `stop`: drop queued PCM, `{ok: true}`
  - `play-midi`: render via `render_midi_notes`, mix at the current write cursor (or immediately into the sink), `{ok: true}`
  - `shutdown`: close sink, `{ok: true}` then the process exits
- `main`: if `--engine`, loop `sys.stdin.readline`, `json.loads`, `print(json.dumps(result), flush=True)`. Use `python3 -u`.
- `output_command()`: `pw-cat` as above, else `["paplay", "--raw", f"--rate={RATE}", "--channels=1", "--format=s16le"]`, else `["aplay", "-q", "-t", "raw", "-f", "S16_LE", "-r", str(RATE), "-c", "1"]`.

`play` of a long timeline may take tens/hundreds of ms to render. That is OK: QML must not start the playhead until `started`. Do not stream the first bar before the rest is rendered in v1 — the default song is eight bars. If render of a huge song is slow, still emit `started` only when the sink has the first chunk; a later optimization can render incrementally. For this task, render the whole `schedule_measures` then write.

Loop: if `msg.get("loop")` is true, the engine should be able to write the scheduled PCM more than once. Simplest v1: after writing, if loop, write it again until `stop`. That blocks stdin handling. **Do not block stdin.** Use a writer thread or a chunked iterator:

- Queue PCM bytes.
- A daemon thread writes chunks to the sink.
- `stop` clears the queue and sets a flag.
- `loop` re-enqueues the same PCM when remaining queued samples fall below one measure.

For CI `BufferSink`, `play` can write the PCM once (or twice if loop) synchronously; the thread is for PipeSink.

**Step 4: Run tests and verify pass**

Run: `python3 tests/run.py`

Expected: engine unit + subprocess protocol tests pass. Existing `--write` WAV tests still pass.

**Step 5: Commit**

```bash
git add play-notes.py tests/run.py
git commit -m "$(cat <<'EOF'
feat(playback): add persistent audio engine protocol

Keep samples warm and play queued measures on a
long-lived sink instead of one process per bar.
EOF
)"
```

---

### [x] Task 4: QML engine process and transport clock

**Status:** `done`
**Resume:** Complete
**Commits:** 2b5ce00c, a7dfa40c

**Files:**
- Modify: `Songwriter.qml`
- Test: `python3 tests/run.py` (JS helpers already in task 1; no QML runner in CI)
- Verify: overlay play/stop/loop with beats on and off (manual; see Step 4)

**Step 1: Add the engine Process**

Mirror `agentServer`. Start when the overlay opens; restart on exit; stop on destruction.

```qml
Process {
  id: audioEngine
  running: false
  stdinEnabled: true
  command: ["python3", "-u", root.playScript, "--engine"]
  stdout: SplitParser {
    onRead: data => root.onEngineMessage(String(data))
  }
  stderr: StdioCollector {
    waitForEnd: false
  }
  onExited: {
    if (root.opened)
      audioEngineRestart.restart()
  }
}
```

`onEngineMessage` parses JSON. On `event === "started"` while `playing` and `audioStartMs === 0`, set `audioStartMs = Date.now() + (msg.latencyMs || 20)` and start `transportTimer`. On unexpected parse errors, set `statusText` and `stopPlayback()`.

Helpers:

```javascript
function engineSend(obj) {
  if (!audioEngine.running)
    return
  audioEngine.write(JSON.stringify(obj) + "\n")
}

function engineMeasureSpec(event) {
  var frozen = event && event.measureAudio
  if (!frozen)
    return null
  var chords = []
  var frozenChords = frozen.chords || []
  for (var i = 0; i < frozenChords.length; i++) {
    var scheduled = frozenChords[i]
    if (scheduled && scheduled.chord) {
      chords.push({
        offsetBeats: scheduled.offsetBeats,
        durationBeats: scheduled.durationBeats,
        midis: Model.triadMidi(scheduled.chord)
      })
    }
  }
  return {
    steps: frozen.steps,
    bpm: song.bpm,
    instrument: currentInstrument(),
    drums: {
      kick: encodedBeatLane(frozen.beats && frozen.beats.kick, frozen.steps),
      snare: encodedBeatLane(frozen.beats && frozen.beats.snare, frozen.steps),
      hihat: encodedBeatLane(frozen.beats && frozen.beats.hihat, frozen.steps)
    },
    chords: chords
  }
}
```

Warmup on overlay open: `engineSend({ cmd: "warmup", instrument: currentInstrument() })`. Also send warmup when the instrument changes.

**Step 2: Queue the timeline at Play; stop spawning per bar**

`startPlayback` / `startSectionPlayback`:

1. Build the frozen timeline as today.
2. `playing = true`, reset `currentBeat` / `currentBar` / `playEvent`, **do not** call `applyPlayhead` yet.
3. `audioStartMs = 0`.
4. `engineSend({ cmd: "play", loop: !!song.loop, latencyMs: 20, measures: Song.measureLaunchEvents(tl).map(engineMeasureSpec) })`.
5. Wait for `started` (Step 1). If nothing arrives, keep the existing 2 s-scale user-visible failure: `statusText = "Audio engine failed"` and `stopPlayback()` from a short one-shot timer (e.g. 2 s).

`stopPlayback`: `engineSend({ cmd: "stop" })`, `audioStartMs = 0`, stop the timer, clear fill / sounding as today.

`applyPlayhead`: **remove** `playMeasureAudio(event)` and the `patternedMeasure` branch that skipped/spawned chord audio. During transport, only update highlight, status, and slot fill. `applySounding(event, false)` still lights the piano.

Delete or stop using `playMeasureAudio` for transport. Keep `playMidiNotes` for now only as a wrapper that sends `{ cmd: "play-midi", … }` to the engine when it is running (preview, audition, laptop keys). Do not `execDetached` `play-notes.py` for those if the engine is up — a second `pw-play` fights the persistent stream.

**Step 3: Wall-clock playhead**

Replace chained one-shot `transportTimer` with a 16 ms repeating timer:

```javascript
onTriggered: {
  if (!playing || !(audioStartMs > 0))
    return
  var beat = Song.beatAtWallClock(audioStartMs, Date.now(), song.bpm)
  var total = Song.timelineDurationBeats(timeline)
  if (beat >= total) {
    if (song.loop) {
      var cycle = Math.floor(beat / total)
      audioStartMs += cycle * Song.beatsToSeconds(total, song.bpm) * 1000
      beat = Song.beatAtWallClock(audioStartMs, Date.now(), song.bpm)
      currentBar = 1
      playEvent = null
    } else {
      stopPlayback()
      return
    }
  }
  currentBeat = beat
  applyPlayhead(Song.eventAtBeat(timeline, currentBeat))
}
```

`scheduleBeatTick` goes away. Slot fill can keep `fillClock` (already wall-clock).

BPM change while playing: stop and restart playback (simplest; in-flight PCM was rendered at the old BPM). Do not keep the old stream in tempo.

**Step 4: Verify**

Run: `python3 tests/run.py`

Expected: still green.

Manual (required; PipeWire is not in CI):

1. Overlay open, default song, Beats off: Play. Chord of bar 1 must start with the `1 : 1` highlight, not after a pause into beat 2.
2. Add a kick on step 0 of bar 1 (and optionally a four-on-the-floor). Play. Kick lands on beat 1 with the chord, every bar, including loop wrap.
3. Section play and a repeated row: first beat of each pass is a downbeat, not a late pickup.
4. Stop cuts audio immediately.
5. Click a filled slot (audition) and a circle wedge (preview) while stopped and while playing — no extra laggy `pw-play` pile-up.
6. If layout or styling of transport is untouched, skip viewport checks; this task is timing, not UI chrome.

If kick is still late by ~100 ms, the engine is not passing `--latency 20ms`. If kick is late by ~200–400 ms, QML is still using `execDetached` or starting the playhead before `started`.

**Step 5: Commit**

```bash
git add Songwriter.qml
git commit -m "$(cat <<'EOF'
fix(playback): drive playhead from the audio clock

Queue every bar on the persistent engine and start
the highlight only after the first sample is written.
EOF
)"
```

---

### [x] Task 5: Feature maps and README

**Status:** `done`
**Resume:** Complete
**Commits:** cb7d2944

**Files:**
- Modify: `.features/playback.yaml`
- Modify: `.features/beats.yaml`
- Modify: `.features/audio_device.yaml`
- Modify: `README.md`

**Step 1: Patch maps (fields, not essays)**

`playback.yaml`:

- `user_flow.primary`: `User → Play or Space → queue measureLaunchEvents on audio engine; playhead follows wall clock from started+latency`
- `user_flow.beats`: `Every measure/pass (drums optional) → one spec on the engine sample clock`
- `user_flow.audition`: keep slot fill wall-clock; audio via engine `play-midi`
- `core_components`: add engine protocol (`play-notes.py --engine`)
- `notes`: replace “Overlay playhead is not in CI” with: playhead is wall-clock from engine `started`; PipeWire still not in CI; no per-bar `execDetached`

`beats.yaml`:

- `user_flow.play`: `Transport → queue frozen measure with chords and drums; step 0 is sample 0 of that bar`
- `notes`: keep step counts; drop “detached audio helper” as the play path; tails mix into the next bar

`audio_device.yaml`:

- `user_flow.primary`: `Play/preview/live → play-notes.py --engine → pw-cat raw s16 44100 mono latency 20ms`
- `notes`: persistent process, sample cache lives across bars; `pw-play` is no longer the transport path

**Step 2: README**

In the Features table, playback line: mention Play starts on the downbeat with beats and chords sharing one clock.

**Step 3: Validate maps**

```bash
./bin/feature-map validate
./bin/feature-map check
python3 tests/run.py
omarchy plugin validate /home/ms/.config/omarchy/plugins/markschellhas.songwriter
```

Expected: maps valid, tests pass, host validator accepts QML (`Process`, `stdinEnabled`, `SplitParser`, `write`).

**Step 4: Commit**

```bash
git add .features/playback.yaml .features/beats.yaml .features/audio_device.yaml README.md
git commit -m "$(cat <<'EOF'
docs(playback): map persistent engine and downbeat clock
EOF
)"
```

---

## Out of scope (do not do in this plan)

- Velocity, swing, or a mixer
- Changing `RATE` from 44100 to 48000
- Per-machine latency calibration UI
- Falling back to `execDetached` play-notes on engine failure (restart the engine instead)
