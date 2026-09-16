# PRD: Playback Sync

**Status:** Draft
**Owner:** Songwriter plugin

---

## Overview

Song playback currently starts each measure by spawning `play-notes.py` at the visual downbeat, rendering a WAV, then handing it to `pw-play`. That work happens *after* the playhead has already moved, so kick, snare, hi-hat, and chords all sound late — often near beat two at typical BPMs. Chord-only bars take the same path per slot, so they feel laggy even without drums.

This work replaces fire-and-forget launches with a long-lived audio helper that pre-renders measures, writes a continuous PipeWire stream, and starts the visual playhead from the same clock as the first audible sample.

Grounded in `.features/playback.yaml`, `.features/beats.yaml`, and `.features/audio_device.yaml`.

## Goals / Non-Goals

**Goals:**

1. The first kick (step 0) and the first chord of a bar start on beat 1 of that bar, including loop, section play, rests, and row repeats.
2. Beats and chords share one sample clock, so they cannot drift apart within a measure or across measure boundaries.
3. Pressing Play starts audio and the playhead together; the highlight is not a beat ahead of what is heard.
4. Chord-only measures use the same scheduled path as drum measures (no per-slot process spawn during transport).
5. Preview, slot audition, and live laptop keys do not steal or restart the playback stream.

**Non-Goals:**

1. Velocity, swing, mixer, or sample import.
2. Changing the beat-lane editor, BPM range, or song document shape.
3. Switching the renderer from 44100 Hz to 48000 Hz.
4. A full in-process DAW or a second transport.
5. Making PipeWire itself part of CI.

## Current Implementation

`js/Song.js` `buildTimeline` / `buildSectionTimeline` emit slot events. The first event of a measure with a non-empty beat pattern carries a frozen `measureAudio` spec; later slots in that bar set `patternedMeasure` so QML will not spawn per-chord audio.

`Songwriter.qml` walks those events with a chained QML `Timer` (`transportTimer`, 8 ms floor). On each new event identity, `applyPlayhead` either:

- launches `Quickshell.execDetached(["python3", play-notes.py, "--measure", json])` for a patterned bar, or
- launches `play-notes.py --midi …` for an unpatterned chord.

`play-notes.py` then starts a cold interpreter, reloads piano samples (process-local `_SAMPLE_CACHE`), renders the whole bar plus a 0.32 s tail, writes a temp WAV, and runs `pw-play` / `paplay` / `aplay`. `pw-cat`/`pw-play` default node latency is 100 ms. Combined with spawn + render, the downbeat is typically 200–500 ms late. At 120 BPM that is 0.4–1.0 beats, which is why the groove feels like it misses beat 1.

Unpatterned chords also prepend `PAD` (20 ms) of silence in `synth` / `render_samples`. Combined measure mixing strips that pad; chord-only playback does not.

The playhead uses chained timer intervals (`Math.round` of beat duration in ms), so it can drift from wall clock independently of audio.

## Proposed Implementation

Keep `play-notes.py` as the renderer. Add a persistent `--engine` mode started with the overlay (same lifetime pattern as `agent-server`).

On Play:

1. QML sends the frozen timeline as a list of measure specs (chords ± drums, every bar, including rests).
2. The engine warms samples if needed, renders measures onto one sample clock, and writes raw s16le to a long-lived `pw-cat --playback --raw` stream with an explicit ~20 ms node latency (not the 100 ms default).
3. Measure *n* starts at sample `sum(nominal_frames[:n])`. Drum tails mix into the next bar instead of delaying it.
4. The engine replies `started` when the first PCM is written. QML starts a wall-clock playhead from that timestamp plus the same output latency, so highlight and kick line up.
5. Loop re-queues the same sequence before the last bar ends. Stop flushes the queue and returns to silence without closing the process.

Preview, audition, and live notes become immediate `play-midi` commands on the same stream so they mix instead of launching a second `pw-play`.

If the engine exits while the overlay is open, restart it (mirror `agent-server`). Do not fall back to per-measure `execDetached`; that is the bug.

## Technical Details

- `js/Song.js`: always attach `measureAudio` on the first slot of every measure/pass, even when the beat pattern is empty. Add `beatAtWallClock(startMs, nowMs, bpm)` and `measureLaunchEvents(timeline)`.
- `play-notes.py`: `schedule_measures(specs)` concatenates bars on the nominal clock; `--engine` reads NDJSON on stdin and writes NDJSON on stdout; output via `pw-cat -p -a --format s16 --rate 44100 --channels 1 --latency 20ms`, with `paplay --raw` / `aplay` fallbacks.
- `Songwriter.qml`: long-lived `Process` with `stdinEnabled: true` and `SplitParser` on stdout; `startPlayback` queues then waits for `started`; `transportTimer` at 16 ms reads wall-clock beat instead of chaining intervals; `applyPlayhead` no longer spawns audio.
- Tests in `tests/js_tests.js` and `tests/run.py` cover clock math, always-on measure specs, sample-accurate downbeats across two bars, tail overlap, and the NDJSON protocol with a buffer sink (no PipeWire in CI).
- Feature maps: `playback`, `beats`, `audio_device`.

## Effort Estimates

- Timeline + wall-clock helpers: S
- Sample-accurate measure scheduler: M
- Persistent engine protocol and output stream: M
- QML transport wiring: L
- Tests and feature maps: M

## Open Questions

- 20 ms is the chosen node latency (low enough to feel on the downbeat, high enough to avoid PipeWire underruns on this host). If underruns appear, raise it in one constant shared by engine and playhead — do not invent a per-machine calibration UI.
- Live laptop keys stay on the engine stream. If a key-down must wait for a measure render, the engine mixes the note at the current write cursor; it does not stop the song.

## Related Docs

- `.features/playback.yaml`
- `.features/beats.yaml`
- `.features/audio_device.yaml`
- `.features/chord_slots.yaml`
- `docs/prds/prd-beat-sequencer.md` (original non-goal of keeping detached helpers; this PRD replaces that for transport)
- `docs/plans/2026-09-08-beat-sequencer.md`
- `AGENTS.md`
- `README.md`
