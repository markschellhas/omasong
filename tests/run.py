#!/usr/bin/env python3
"""Run songwriter plugin unit tests (JS libraries + Python helpers)."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import wave
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SONG_LIBRARY = ROOT / "song-library"


def _song_library_env(data: Path, runtime: Path) -> dict[str, str]:
    return {**os.environ, "XDG_DATA_HOME": str(data), "XDG_RUNTIME_DIR": str(runtime)}


def _run_song_library(env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SONG_LIBRARY), *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def _stage_save(runtime: Path, payload: dict) -> None:
    stage_dir = runtime / "omarchy-songwriter"
    stage_dir.mkdir(parents=True, exist_ok=True)
    (stage_dir / "save-selection.json").write_text(json.dumps(payload))


def load_pragma_js(path: Path) -> str:
    text = path.read_text()
    lines = [line for line in text.splitlines() if not line.startswith(".pragma library")]
    return "\n".join(lines) + "\n"


def run_node(script: str) -> None:
    proc = subprocess.run(
        ["node", "--input-type=commonjs"],
        input=script,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode or 1)
    if proc.stdout.strip():
        print(proc.stdout, end="")


def test_js() -> None:
    libs = [
        load_pragma_js(ROOT / "js" / "Model.js"),
        load_pragma_js(ROOT / "js" / "ParallelMode.js"),
        load_pragma_js(ROOT / "js" / "Song.js"),
        load_pragma_js(ROOT / "js" / "Agent.js"),
        load_pragma_js(ROOT / "js" / "Keyboard.js"),
        load_pragma_js(ROOT / "js" / "Focus.js"),
        load_pragma_js(ROOT / "js" / "Guitar.js"),
        load_pragma_js(ROOT / "js" / "BeatUi.js"),
    ]
    harness = r"""
function assert(cond, msg) {
  if (!cond) throw new Error(msg || "assertion failed");
}
function assertEq(a, b, msg) {
  if (a !== b) throw new Error((msg || "assertEq") + ": " + JSON.stringify(a) + " !== " + JSON.stringify(b));
}
"""
    body = (ROOT / "tests" / "js_tests.js").read_text()
    source = harness + "".join(libs) + body + "\nconsole.log('js tests ok');\n"
    wrapped = (
        "const vm = require('vm');\n"
        "const sandbox = { console, Math, Date, JSON, Object, Array, String, Number, isFinite };\n"
        "vm.createContext(sandbox);\n"
        "vm.runInContext("
        + json.dumps(source)
        + ", sandbox);\n"
    )
    run_node(wrapped)


def test_play_notes() -> None:
    spec = importlib.util.spec_from_file_location("play_notes", ROOT / "play-notes.py")
    play_notes = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(play_notes)
    if play_notes.clamp_seconds(100) != play_notes.MAX_SECONDS:
        raise SystemExit("play-notes must cap long durations")
    if play_notes.clamp_seconds(float("nan")) != play_notes.DEFAULT_SECONDS:
        raise SystemExit("play-notes must reject non-finite durations")
    if play_notes.clamp_midi(200) is not None:
        raise SystemExit("play-notes must reject out-of-range MIDI")
    if play_notes.clamp_hz(1) is not None:
        raise SystemExit("play-notes must reject inaudible Hz")
    if play_notes.clamp_instrument(4) != 2:
        raise SystemExit("play-notes must clamp retired Pad/Strings to Organ")
    if play_notes.clamp_instrument(2) != 2:
        raise SystemExit("play-notes must keep Organ")
    if play_notes.clamp_drum_steps(0) != 1 or play_notes.clamp_drum_steps(999) != play_notes.MAX_DRUM_STEPS:
        raise SystemExit("play-notes must bound drum step counts")
    if play_notes.clamp_bpm(1) != play_notes.MIN_BPM or play_notes.clamp_bpm(999) != play_notes.MAX_BPM:
        raise SystemExit("play-notes must bound drum BPM")
    if play_notes.parse_drum_pattern("10x1" + "1" * 200, 4) != [True, False, False, True]:
        raise SystemExit("play-notes must safely parse and bound drum patterns")

    steps = 8
    bpm = 120
    nominal_frames = round(play_notes.RATE * steps * 60 / bpm / 4)
    expected_frames = nominal_frames + round(play_notes.RATE * play_notes.DRUM_TAIL_SECONDS)
    lane_patterns = (
        ("kick", "10000000", "00000000", "00000000"),
        ("snare", "00000000", "00100000", "00000000"),
        ("hihat", "00000000", "00000000", "00001000"),
    )
    for lane, kick, snare, hihat in lane_patterns:
        frames = play_notes.render_drums(kick, snare, hihat, steps, bpm)
        if len(frames) != expected_frames:
            raise SystemExit(f"{lane} drum measure duration is not transport-aligned")
        hit_step = {"kick": 0, "snare": 2, "hihat": 4}[lane]
        offset = round(play_notes.RATE * hit_step * 60 / bpm / 4)
        window = frames[offset : min(len(frames), offset + int(play_notes.RATE * 0.04))]
        if not window or max(abs(sample) for sample in window) < 100:
            raise SystemExit(f"{lane} drum transient is silent")
        if frames != play_notes.render_drums(kick, snare, hihat, steps, bpm):
            raise SystemExit(f"{lane} drum rendering is not deterministic")
        if frames[-1] != 0:
            raise SystemExit(f"{lane} drum render must end at zero")

    late_kick = play_notes.render_drums("00000001", "00000000", "00000000", steps, bpm)
    tail = late_kick[nominal_frames : nominal_frames + int(play_notes.RATE * 0.08)]
    if not tail or max(abs(sample) for sample in tail) < 100:
        raise SystemExit("last-step kick tail was cut at the measure boundary")
    try:
        play_notes.render_drums("1" * 128, "0" * 128, "0" * 128, 128, 40)
    except ValueError:
        pass
    else:
        raise SystemExit("oversized drum duration must be rejected before rendering")

    measure_spec = {
        "steps": 8,
        "bpm": 120,
        "instrument": 0,
        "drums": {"kick": "00001000", "snare": "00000000", "hihat": "00000000"},
        "chords": [{"offsetBeats": 0, "durationBeats": 0.5, "midis": [60, 64, 67]}],
    }
    combined = play_notes.render_measure(measure_spec)
    if len(combined) != expected_frames or combined[-1] != 0:
        raise SystemExit("combined measure render has wrong bounded tail duration")
    chord_window = combined[: int(play_notes.RATE * 0.20)]
    drum_offset = round(play_notes.RATE * 4 * 60 / bpm / 4)
    drum_window = combined[drum_offset : drum_offset + int(play_notes.RATE * 0.08)]
    if max(abs(sample) for sample in chord_window) < 100:
        raise SystemExit("combined measure omitted chord audio")
    if max(abs(sample) for sample in drum_window) < 100:
        raise SystemExit("combined measure omitted drum audio")

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
    one_bar = play_notes.schedule_measures([m0])
    if max(abs(s) for s in one_bar[: int(play_notes.RATE * 0.04)]) < 100:
        raise SystemExit("one-bar schedule is silent at downbeat 0")
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

    if len(scheduled) <= nominal * 2:
        raise SystemExit("one-shot schedule must keep a tail after the last bar")
    one_shot_late = play_notes.schedule_measures([late])
    if len(one_shot_late) <= nominal:
        raise SystemExit("one-shot last-step kick must ring past the bar")
    looped = play_notes.schedule_measures([late], loop=True)
    if len(looped) != nominal:
        raise SystemExit("looped schedule must be exactly the nominal bar")
    if max(abs(s) for s in looped[: int(play_notes.RATE * 0.08)]) < 100:
        raise SystemExit("last-step kick tail must wrap into the loop downbeat")
    looped_two = play_notes.schedule_measures([m1, late], loop=True)
    if len(looped_two) != nominal * 2:
        raise SystemExit("looped two-bar schedule must be exactly two nominal bars")
    looped_engine = play_notes.AudioEngine(sink=play_notes.BufferSink())
    looped_started = looped_engine.handle({
        "cmd": "play",
        "loop": True,
        "measures": [m1, late],
    })
    if looped_started.get("frames") != nominal * 2:
        raise SystemExit("engine loop play must queue the nominal timeline")

    engine = play_notes.AudioEngine(sink=play_notes.BufferSink())
    ready = engine.handle({"cmd": "warmup", "instrument": 0})
    if not ready.get("ok"):
        raise SystemExit("warmup must succeed without PipeWire")
    started = engine.handle({
        "cmd": "play",
        "id": 7,
        "loop": False,
        "latencyMs": 20,
        "measures": [m0, m1],
    })
    if started.get("event") != "started":
        raise SystemExit("play must emit started")
    if started.get("id") != 7:
        raise SystemExit("play must echo id on started")
    slow = dict(m0)
    slow["bpm"] = 40
    slow_started = engine.handle({
        "cmd": "play",
        "id": 8,
        "loop": False,
        "measures": [slow],
    })
    if slow_started.get("event") != "started" or slow_started.get("id") != 8:
        raise SystemExit("play must emit started at a slow BPM")
    too_long = {
        "steps": 128,
        "bpm": 40,
        "instrument": 0,
        "drums": {"kick": "1" * 128, "snare": "0" * 128, "hihat": "0" * 128},
        "chords": [],
    }
    failed_play = engine.handle({"cmd": "play", "id": 9, "measures": [too_long]})
    if failed_play.get("ok") is not False:
        raise SystemExit("oversized play must return ok false, not started")
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
    print("play-notes engine ok")

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
    print("play-notes engine protocol ok")

    if shutil.which("pw-cat"):
        if play_notes.output_command() != [
            "pw-cat", "-p", "-a", "--format", "s16", "--rate", "44100",
            "--channels", "1", "--latency", "%sms" % play_notes.OUTPUT_LATENCY_MS, "-",
        ]:
            raise SystemExit("output_command must prefer pw-cat reading stdin at engine latency")

    class RecordingStdin:
        def __init__(self) -> None:
            self._buf = bytearray()
            self._lock = threading.Lock()

        def write(self, data: bytes) -> int:
            with self._lock:
                self._buf.extend(data)
            return len(data)

        def flush(self) -> None:
            return

        def close(self) -> None:
            return

        def snapshot(self) -> bytes:
            with self._lock:
                return bytes(self._buf)

    class FakeProc:
        def __init__(self, stdin: RecordingStdin) -> None:
            self.stdin = stdin

        def poll(self) -> None:
            return None

        def wait(self, timeout: float | None = None) -> int:
            return 0

        def kill(self) -> None:
            return

    def count_marker(data: bytes, marker: int) -> int:
        samples = array("h")
        samples.frombytes(data)
        if sys.byteorder != "little":
            samples.byteswap()
        return sum(1 for sample in samples if sample == marker)

    marker = 12345
    chunk_n = max(1, int(play_notes.RATE * play_notes.WRITE_CHUNK_MS / 1000.0))
    pcm = array("h", [marker]) * play_notes.RATE
    recorder = RecordingStdin()
    pipe = play_notes.PipeSink(proc=FakeProc(recorder))
    try:
        pipe.write(pcm, loop=True)
        deadline = time.monotonic() + 1.0
        while count_marker(recorder.snapshot(), marker) == 0:
            if time.monotonic() > deadline:
                raise SystemExit("paced pipe sink wrote nothing")
            time.sleep(0.001)
        time.sleep(play_notes.WRITE_CHUNK_MS / 1000.0)
        t0 = time.monotonic()
        pipe.stop()
        if time.monotonic() - t0 > 0.5:
            raise SystemExit("pipe sink stop hung")
        time.sleep(0.05)
        after_stop = count_marker(recorder.snapshot(), marker)
        if after_stop >= len(pcm):
            raise SystemExit("stop did not prevent dumping the whole play buffer")
        if after_stop > chunk_n * 10:
            raise SystemExit("pipe writer got more than one chunk ahead")
        time.sleep(0.15)
        later = count_marker(recorder.snapshot(), marker)
        if later > after_stop:
            raise SystemExit("play PCM continued after stop")
    finally:
        pipe.close()
    print("play-notes pipe stop ok")

    def peak_after(data: bytes, skip_bytes: int = 0) -> int:
        samples = array("h")
        samples.frombytes(data)
        if sys.byteorder != "little":
            samples.byteswap()
        rest = samples[skip_bytes // 2 :]
        return max((abs(sample) for sample in rest), default=0)

    def wait_peak(stdin: RecordingStdin, skip_bytes: int, timeout: float = 1.0) -> int:
        deadline = time.monotonic() + timeout
        peak = 0
        while time.monotonic() < deadline:
            peak = peak_after(stdin.snapshot(), skip_bytes)
            if peak >= 100:
                return peak
            time.sleep(0.01)
        return peak

    idle_rec = RecordingStdin()
    idle_pipe = play_notes.PipeSink(proc=FakeProc(idle_rec))
    try:
        idle_engine = play_notes.AudioEngine(sink=idle_pipe)
        idle_engine.handle({
            "cmd": "play-midi",
            "midis": [60, 64, 67],
            "seconds": 0.12,
            "instrument": 0,
        })
        if wait_peak(idle_rec, 0) < 100:
            raise SystemExit("play-midi on an idle pipe sink was silent")
    finally:
        idle_pipe.close()

    stopped_rec = RecordingStdin()
    stopped_pipe = play_notes.PipeSink(proc=FakeProc(stopped_rec))
    try:
        stopped_engine = play_notes.AudioEngine(sink=stopped_pipe)
        stopped_engine.handle({"cmd": "play", "measures": [m0]})
        time.sleep(0.05)
        stopped_engine.handle({"cmd": "stop"})
        time.sleep(0.05)
        after_stop_bytes = len(stopped_rec.snapshot())
        time.sleep(0.12)
        keepalive_bytes = len(stopped_rec.snapshot())
        if keepalive_bytes - after_stop_bytes < play_notes.RATE * 0.08 * 2:
            raise SystemExit("pipe went idle after stop; preview restarts with a buffer stutter")
        stopped_engine.handle({"cmd": "warmup", "instrument": 0})
        stopped_engine.handle({
            "cmd": "play-midi",
            "midis": [60],
            "seconds": 0.05,
            "instrument": 0,
        })
        time.sleep(0.08)
        at_return_start = len(stopped_rec.snapshot())
        stopped_engine.handle({
            "cmd": "play-midi",
            "midis": [60, 64, 67],
            "seconds": 0.4,
            "instrument": 0,
        })
        at_return = len(stopped_rec.snapshot())
        time.sleep(0.015)
        burst = stopped_rec.snapshot()[at_return:]
        burst_samples = array("h")
        burst_samples.frombytes(burst)
        if sys.byteorder != "little":
            burst_samples.byteswap()
        burst_sec = sum(1 for sample in burst_samples if abs(sample) >= 100) / play_notes.RATE
        if burst_sec > 0.05:
            raise SystemExit("play-midi after stop dumped a prefill burst")
        if wait_peak(stopped_rec, at_return_start) < 100:
            raise SystemExit("play-midi after stop was silent")
    finally:
        stopped_pipe.close()
    print("play-notes play-midi pipe ok")

    warmed_rec = RecordingStdin()
    warmed_pipe = play_notes.PipeSink(proc=FakeProc(warmed_rec))
    try:
        warmed_engine = play_notes.AudioEngine(sink=warmed_pipe)
        warmed_engine.handle({"cmd": "warmup", "instrument": 0})
        first = None
        deadline = time.monotonic() + 2.0
        while True:
            if warmed_rec.snapshot():
                if first is None:
                    first = time.monotonic()
                if time.monotonic() - first >= 0.20:
                    break
            if time.monotonic() > deadline:
                raise SystemExit("warmup must start the output clock so preview is not a cold pw-cat")
            time.sleep(0.01)
        elapsed = time.monotonic() - first
        samples = len(warmed_rec.snapshot()) // 2
        ahead = samples / float(play_notes.RATE) - elapsed
        min_ahead = (play_notes.OUTPUT_LATENCY_MS / 1000.0) * 0.5
        if ahead < min_ahead:
            raise SystemExit("keepalive queued less than PipeWire latency; preview underruns and stutters")
        before_mix = len(warmed_rec.snapshot())
        warmed_engine.handle({
            "cmd": "play-midi",
            "midis": [60, 64, 67],
            "seconds": 0.4,
            "instrument": 0,
        })
        time.sleep(0.015)
        burst = warmed_rec.snapshot()[before_mix:]
        burst_samples = array("h")
        burst_samples.frombytes(burst)
        if sys.byteorder != "little":
            burst_samples.byteswap()
        burst_sec = sum(1 for sample in burst_samples if abs(sample) >= 100) / play_notes.RATE
        if burst_sec > 0.05:
            raise SystemExit("play-midi on a warmed sink dumped a prefill burst")
        if wait_peak(warmed_rec, before_mix) < 100:
            raise SystemExit("play-midi on a warmed sink was silent")
        warmed_engine.handle({"cmd": "stop"})
        time.sleep(0.05)
        before_play = len(warmed_rec.snapshot())
        warmed_engine.handle({"cmd": "play", "measures": [m0]})
        time.sleep(0.015)
        play_burst = warmed_rec.snapshot()[before_play:]
        play_samples = array("h")
        play_samples.frombytes(play_burst)
        if sys.byteorder != "little":
            play_samples.byteswap()
        play_burst_sec = sum(1 for sample in play_samples if abs(sample) >= 100) / play_notes.RATE
        if play_burst_sec > 0.05:
            raise SystemExit("play on a warmed sink dumped a prefill burst")
    finally:
        warmed_pipe.close()
    print("play-notes preview clock ok")

    stacked = play_notes.overlay_s16(array("h", [1000, 1000, 0]), array("h", [1000, 0, 1000, 500]))
    if list(stacked) != [2000, 1000, 1000, 500]:
        raise SystemExit("overlay_s16 must mix at the cursor and extend, not concatenate")
    same_len = play_notes.overlay_s16(array("h", [3000] * 4), array("h", [3000] * 4))
    if len(same_len) != 4 or same_len[0] < 5000:
        raise SystemExit("equal-length overlay must chord, not queue a second note")

    live_rec = RecordingStdin()
    live_pipe = play_notes.PipeSink(proc=FakeProc(live_rec))
    try:
        live_engine = play_notes.AudioEngine(sink=live_pipe)
        live_engine.handle({"cmd": "warmup", "instrument": 0})
        first = None
        deadline = time.monotonic() + 2.0
        while True:
            if live_rec.snapshot():
                if first is None:
                    first = time.monotonic()
                if time.monotonic() - first >= 0.20:
                    break
            if time.monotonic() > deadline:
                raise SystemExit("warmup must start the output clock so live notes are not a cold pw-cat")
            time.sleep(0.01)

        t_cmd = time.monotonic()
        on = live_engine.handle({"cmd": "note-on", "midi": 60, "instrument": 0})
        if not on.get("ok"):
            raise SystemExit("note-on must succeed")
        if time.monotonic() - t_cmd > 0.05:
            raise SystemExit("note-on must not prerender a one-shot before mixing")
        before = len(live_rec.snapshot())
        if wait_peak(live_rec, before) < 100:
            raise SystemExit("note-on on a warmed sink was silent")

        time.sleep(0.04)
        t_second = time.monotonic()
        live_engine.handle({"cmd": "note-on", "midi": 64, "instrument": 0})
        if time.monotonic() - t_second > 0.05:
            raise SystemExit("second note-on must not wait on a queued one-shot")
        at_second = len(live_rec.snapshot())
        if wait_peak(live_rec, at_second, timeout=0.2) < 100:
            raise SystemExit("overlapping live note was silent")

        time.sleep(0.50)
        still = len(live_rec.snapshot())
        time.sleep(0.06)
        if peak_after(live_rec.snapshot()[still:]) < 100:
            raise SystemExit("held live note stopped at a fixed one-shot length")

        live_engine.handle({"cmd": "note-off", "midi": 60})
        live_engine.handle({"cmd": "note-off", "midi": 64})
        time.sleep(play_notes.LIVE_RELEASE_SECONDS + 0.05)
        after_off = len(live_rec.snapshot())
        time.sleep(0.12)
        if peak_after(live_rec.snapshot()[after_off:]) >= 100:
            raise SystemExit("note-off must release the live voice")

        tap_start = len(live_rec.snapshot())
        live_engine.handle({"cmd": "note-on", "midi": 67, "instrument": 0})
        time.sleep(0.08)
        live_engine.handle({"cmd": "note-off", "midi": 67})
        time.sleep(play_notes.LIVE_RELEASE_SECONDS + 0.08)
        tap = live_rec.snapshot()[tap_start:]
        tap_samples = array("h")
        tap_samples.frombytes(tap)
        if sys.byteorder != "little":
            tap_samples.byteswap()
        audible = [i for i, sample in enumerate(tap_samples) if abs(sample) >= 100]
        if not audible:
            raise SystemExit("staccato live note was silent")
        tap_sec = (audible[-1] - audible[0]) / float(play_notes.RATE)
        if tap_sec > 0.35:
            raise SystemExit("live note duration was quantized instead of following note-off")

        before_burst = len(live_rec.snapshot())
        live_engine.handle({"cmd": "note-on", "midi": 69, "instrument": 0})
        time.sleep(0.015)
        burst = live_rec.snapshot()[before_burst:]
        burst_samples = array("h")
        burst_samples.frombytes(burst)
        if sys.byteorder != "little":
            burst_samples.byteswap()
        burst_sec = sum(1 for sample in burst_samples if abs(sample) >= 100) / play_notes.RATE
        if burst_sec > 0.05:
            raise SystemExit("note-on dumped a prefill burst")
        live_engine.handle({"cmd": "note-off", "midi": 69})
        bad = live_engine.handle({"cmd": "note-on", "midi": 200})
        if bad.get("ok") is not False:
            raise SystemExit("note-on must reject an invalid midi")
    finally:
        live_pipe.close()
    print("play-notes live notes ok")

    proto = subprocess.run(
        [sys.executable, str(ROOT / "play-notes.py"), "--engine"],
        input=json.dumps({"cmd": "warmup", "instrument": 0}) + "\n"
        + json.dumps({"cmd": "note-on", "midi": 60, "instrument": 0}) + "\n"
        + json.dumps({"cmd": "note-off", "midi": 60}) + "\n"
        + json.dumps({"cmd": "shutdown"}) + "\n",
        capture_output=True,
        text=True,
        timeout=20,
    )
    if proto.returncode != 0:
        sys.stderr.write(proto.stdout + proto.stderr)
        raise SystemExit("engine note-on protocol failed")
    proto_lines = [json.loads(line) for line in proto.stdout.splitlines() if line.strip()]
    if len(proto_lines) < 3 or not all(line.get("ok") for line in proto_lines[:3]):
        raise SystemExit("engine stdin protocol did not ACK note-on/note-off")
    print("play-notes live note protocol ok")

    class SlowStdin(RecordingStdin):
        def write(self, data: bytes) -> int:
            time.sleep(0.005)
            return super().write(data)

    audio_s = 0.4
    slow_pcm = array("h", [2000]) * int(play_notes.RATE * audio_s)
    slow = SlowStdin()
    slow_pipe = play_notes.PipeSink(proc=FakeProc(slow))
    try:
        t0 = time.monotonic()
        slow_pipe.write(slow_pcm, loop=False)
        want = len(slow_pcm) * 2
        deadline = t0 + audio_s + 1.0
        while len(slow.snapshot()) < want and time.monotonic() < deadline:
            time.sleep(0.005)
        elapsed = time.monotonic() - t0
        if len(slow.snapshot()) < want:
            raise SystemExit("slow pipe sink did not finish the buffer")
        if elapsed > audio_s * 1.15:
            raise SystemExit("pipe writer fell behind realtime under emit cost")
    finally:
        slow_pipe.close()
    print("play-notes pipe realtime ok")

    with tempfile.TemporaryDirectory() as tmp:
        drums = Path(tmp) / "drums.wav"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "play-notes.py"), "--write", str(drums), "--drums", "10000000", "00100000", "00001000", "--steps", "8", "--bpm", "120"],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            raise SystemExit(proc.returncode)
        with wave.open(str(drums), "rb") as drum_wav:
            if drum_wav.getnchannels() != 1 or drum_wav.getframerate() != play_notes.RATE:
                raise SystemExit("drum mode must write a mono transport-rate WAV")
            if drum_wav.getnframes() != expected_frames:
                raise SystemExit("drum CLI wrote the wrong measure duration")
        print("play-notes drums ok")

        combined_wav = Path(tmp) / "combined.wav"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "play-notes.py"), "--write", str(combined_wav), "--measure", json.dumps(measure_spec, separators=(",", ":"))],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            raise SystemExit(proc.returncode)
        with wave.open(str(combined_wav), "rb") as measure_wav:
            if measure_wav.getnframes() != expected_frames:
                raise SystemExit("combined CLI did not use the shared measure renderer")
            cli_samples = array("h")
            cli_samples.frombytes(measure_wav.readframes(measure_wav.getnframes()))
            if sys.byteorder != "little":
                cli_samples.byteswap()
        if max(abs(sample) for sample in cli_samples[: int(play_notes.RATE * 0.20)]) < 100:
            raise SystemExit("combined CLI WAV omitted chord audio")
        if max(abs(sample) for sample in cli_samples[drum_offset : drum_offset + int(play_notes.RATE * 0.08)]) < 100:
            raise SystemExit("combined CLI WAV omitted drum audio")
        print("play-notes combined measure ok")

        oversized = Path(tmp) / "oversized.wav"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "play-notes.py"), "--write", str(oversized), "--drums", "1" * 128, "0" * 128, "0" * 128, "--steps", "128", "--bpm", "40"],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 or oversized.exists():
            raise SystemExit("oversized drum CLI request must fail before writing")

        wav = Path(tmp) / "cmaj.wav"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "play-notes.py"), "--write", str(wav), "--midi", "60", "64", "67", "--instrument", "1", "--seconds", "0.12"],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            raise SystemExit(proc.returncode)
        if wav.stat().st_size < 1000:
            raise SystemExit("play-notes wrote a tiny wav")
        print("play-notes wav bytes", wav.stat().st_size)

        huge = Path(tmp) / "huge.wav"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "play-notes.py"), "--write", str(huge), "--midi", "60", "--seconds", "100"],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            raise SystemExit(proc.returncode)
        max_bytes = int(play_notes.RATE * play_notes.MAX_SECONDS * 2 * 1.2) + 1024
        if huge.stat().st_size > max_bytes:
            raise SystemExit("play-notes did not cap --seconds")

        bad = subprocess.run(
            [sys.executable, str(ROOT / "play-notes.py"), "--write", str(Path(tmp) / "bad.wav"), "--midi", "200"],
            capture_output=True,
            text=True,
        )
        if bad.returncode == 0:
            raise SystemExit("play-notes accepted invalid MIDI")

        missing = [
            midi
            for midi in range(48, 73)
            if not (ROOT / "samples" / "piano" / (play_notes.midi_note_name(midi) + ".wav")).is_file()
        ]
        if missing:
            raise SystemExit("missing piano samples: " + ",".join(play_notes.midi_note_name(m) for m in missing))
        if not play_notes.piano_samples_ready():
            raise SystemExit("C4 piano sample missing")

        piano = Path(tmp) / "piano-c4.wav"
        sine = Path(tmp) / "sine-c4.wav"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "play-notes.py"), "--write", str(piano), "--midi", "60", "64", "67", "--instrument", "0", "--seconds", "0.2"],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            raise SystemExit(proc.returncode)
        play_notes.write_wav(
            str(sine),
            play_notes.synth(
                [play_notes.midi_to_hz(m) for m in (60, 64, 67)],
                0.2,
                instrument=0,
            ),
        )
        if piano.read_bytes() == sine.read_bytes():
            raise SystemExit("piano samples should not match additive sines")
        print("play-notes piano samples ok")

        missing_epiano = [
            midi
            for midi in range(48, 73)
            if not (ROOT / "samples" / "epiano" / (play_notes.midi_note_name(midi) + ".wav")).is_file()
        ]
        if missing_epiano:
            raise SystemExit("missing epiano samples: " + ",".join(play_notes.midi_note_name(m) for m in missing_epiano))
        if not play_notes.electric_piano_samples_ready():
            raise SystemExit("C4 electric piano sample missing")

        epiano = Path(tmp) / "epiano-c4.wav"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "play-notes.py"), "--write", str(epiano), "--midi", "60", "64", "67", "--instrument", "1", "--seconds", "0.2"],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            raise SystemExit(proc.returncode)
        if epiano.read_bytes() == sine.read_bytes():
            raise SystemExit("electric piano samples should not match additive sines")
        if epiano.read_bytes() == piano.read_bytes():
            raise SystemExit("electric piano samples should not match piano samples")
        print("play-notes electric piano samples ok")

        missing_organ = [
            midi
            for midi in range(48, 73)
            if not (ROOT / "samples" / "organ" / (play_notes.midi_note_name(midi) + ".wav")).is_file()
        ]
        if missing_organ:
            raise SystemExit("missing organ samples: " + ",".join(play_notes.midi_note_name(m) for m in missing_organ))
        if not play_notes.organ_samples_ready():
            raise SystemExit("C4 organ sample missing")

        organ = Path(tmp) / "organ-c4.wav"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "play-notes.py"), "--write", str(organ), "--midi", "60", "64", "67", "--instrument", "2", "--seconds", "0.2"],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            raise SystemExit(proc.returncode)
        if organ.read_bytes() == sine.read_bytes():
            raise SystemExit("organ samples should not match additive sines")
        if organ.read_bytes() == piano.read_bytes():
            raise SystemExit("organ samples should not match piano samples")
        if organ.read_bytes() == epiano.read_bytes():
            raise SystemExit("organ samples should not match electric piano samples")
        print("play-notes organ samples ok")


def test_write_json() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "nested" / "song.json"
        payload = '{"title":"Test"}'
        proc = subprocess.run(
            [sys.executable, str(ROOT / "write-json.py"), str(path), payload],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            raise SystemExit(proc.returncode)
        if path.read_text() != payload:
            raise SystemExit("write-json did not persist payload")
        a = Path(tmp) / "a.json"
        b = Path(tmp) / "b.json"
        batch = subprocess.run(
            [
                sys.executable,
                str(ROOT / "write-json.py"),
                str(a),
                '{"a":1}',
                str(b),
                '{"b":2}',
            ],
            capture_output=True,
            text=True,
        )
        if batch.returncode != 0:
            sys.stderr.write(batch.stdout + batch.stderr)
            raise SystemExit(batch.returncode)
        if a.read_text() != '{"a":1}' or b.read_text() != '{"b":2}':
            raise SystemExit("write-json batch failed")
        huge = "x" * 1_600_000
        over = subprocess.run(
            [sys.executable, str(ROOT / "write-json.py"), str(Path(tmp) / "big.json")],
            input=huge,
            capture_output=True,
            text=True,
        )
        if over.returncode == 0:
            raise SystemExit("write-json should reject oversized payloads")
        print("write-json ok")


def test_manifest() -> None:
    data = json.loads((ROOT / "manifest.json").read_text())
    required = ["schemaVersion", "id", "name", "version", "kinds", "entryPoints"]
    for key in required:
        if key not in data:
            raise SystemExit("manifest missing " + key)
    if data["schemaVersion"] != 1:
        raise SystemExit("schemaVersion must be 1")
    if data["id"].startswith("omarchy."):
        raise SystemExit("third-party id cannot use omarchy.*")
    for kind, key in (("overlay", "overlay"), ("bar-widget", "barWidget")):
        if kind in data["kinds"] and key not in data["entryPoints"]:
            raise SystemExit("missing entry point for " + kind)
        rel = data["entryPoints"][key]
        if not (ROOT / rel).is_file():
            raise SystemExit("entry point missing: " + rel)
    print("manifest ok")


def test_agent() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tests" / "agent_tests.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode or 1)
    if proc.stdout.strip():
        print(proc.stdout, end="")


def test_song_library() -> None:
    if not SONG_LIBRARY.is_file():
        raise SystemExit("song-library missing")
    sample_song = {"sections": [{"name": "Verse", "measures": [{"slots": []}]}]}

    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp) / "data"
        runtime = Path(tmp) / "runtime"
        env = _song_library_env(data, runtime)
        projects = data / "songwriter" / "projects"

        listed = _run_song_library(env, "list")
        if listed.returncode != 0:
            sys.stderr.write(listed.stdout + listed.stderr)
            raise SystemExit(listed.returncode or 1)
        payload = json.loads(listed.stdout)
        if payload != {"projects": []}:
            raise SystemExit("list should start empty")
        if not projects.is_dir():
            raise SystemExit("list did not create projects dir")

        _stage_save(runtime, {"id": "", "title": "Demo", "song": sample_song})
        saved = _run_song_library(env, "save")
        if saved.returncode != 0:
            sys.stderr.write(saved.stdout + saved.stderr)
            raise SystemExit(saved.returncode or 1)
        result = json.loads(saved.stdout)
        if result["id"] != "Demo" or result["title"] != "Demo":
            raise SystemExit("save id/title mismatch: " + saved.stdout)
        demo_path = projects / "Demo.json"
        if not demo_path.is_file():
            raise SystemExit("save did not write Demo.json")
        demo_doc = json.loads(demo_path.read_text())
        if demo_doc["title"] != "Demo" or demo_doc["id"] != "Demo":
            raise SystemExit("saved file missing title/id")
        if demo_doc["sections"][0]["name"] != "Verse":
            raise SystemExit("saved file dropped song body")

        _stage_save(
            runtime,
            {"id": "Demo", "title": "Demo", "song": {**sample_song, "bpm": 90}},
        )
        updated = _run_song_library(env, "save")
        if updated.returncode != 0:
            sys.stderr.write(updated.stdout + updated.stderr)
            raise SystemExit(updated.returncode or 1)
        if len(list(projects.glob("*.json"))) != 1:
            raise SystemExit("update should overwrite the same file")
        if json.loads(demo_path.read_text()).get("bpm") != 90:
            raise SystemExit("update did not write new song body")

        _stage_save(
            runtime,
            {"id": "Demo", "title": "Demo Renamed", "song": sample_song},
        )
        renamed = _run_song_library(env, "save")
        if renamed.returncode != 0:
            sys.stderr.write(renamed.stdout + renamed.stderr)
            raise SystemExit(renamed.returncode or 1)
        renamed_result = json.loads(renamed.stdout)
        if renamed_result["id"] != "Demo Renamed":
            raise SystemExit("rename did not adopt new filename id")
        if demo_path.exists():
            raise SystemExit("rename left the old file behind")
        renamed_path = projects / "Demo Renamed.json"
        if not renamed_path.is_file():
            raise SystemExit("rename did not write the new file")

        _stage_save(runtime, {"id": "", "title": "Minted", "song": sample_song})
        minted = _run_song_library(env, "save")
        if minted.returncode != 0:
            sys.stderr.write(minted.stdout + minted.stderr)
            raise SystemExit(minted.returncode or 1)
        minted_id = json.loads(minted.stdout)["id"]
        if minted_id != "Minted":
            raise SystemExit("fresh save should use the title as id")
        if len(list(projects.glob("*.json"))) != 2:
            raise SystemExit("fresh save should add a second project file")

        _stage_save(
            runtime,
            {"id": "", "title": "Minted", "song": {**sample_song, "bpm": 88}},
        )
        collision = _run_song_library(env, "save")
        if collision.returncode != 0:
            sys.stderr.write(collision.stdout + collision.stderr)
            raise SystemExit(collision.returncode or 1)
        collision_id = json.loads(collision.stdout)["id"]
        if collision_id != "Minted":
            raise SystemExit("fresh save with the same name should overwrite, got " + collision_id)
        if json.loads((projects / "Minted.json").read_text()).get("bpm") != 88:
            raise SystemExit("same-name save did not overwrite Minted.json")
        if len(list(projects.glob("*.json"))) != 2:
            raise SystemExit("same-name save should not create a second file")

        _stage_save(
            runtime,
            {"id": "stale-uuid", "title": "Minted", "song": {**sample_song, "bpm": 77}},
        )
        stale = _run_song_library(env, "save")
        if stale.returncode != 0:
            sys.stderr.write(stale.stdout + stale.stderr)
            raise SystemExit(stale.returncode or 1)
        if json.loads(stale.stdout)["id"] != "Minted":
            raise SystemExit("stale id should save by title")
        if json.loads((projects / "Minted.json").read_text()).get("bpm") != 77:
            raise SystemExit("stale id did not update Minted.json")
        if (projects / "stale-uuid.json").exists():
            raise SystemExit("stale id should not create a uuid-named file")

        _stage_save(
            runtime,
            {
                "id": "",
                "title": "Flat",
                "sections": [{"name": "Chorus", "measures": [{"slots": []}]}],
                "bpm": 100,
            },
        )
        flat = _run_song_library(env, "save")
        if flat.returncode != 0:
            sys.stderr.write(flat.stdout + flat.stderr)
            raise SystemExit(flat.returncode or 1)
        flat_id = json.loads(flat.stdout)["id"]
        flat_doc = json.loads((projects / f"{flat_id}.json").read_text())
        if flat_doc.get("bpm") != 100 or flat_doc["sections"][0]["name"] != "Chorus":
            raise SystemExit("flat song document was not saved")

        dropped = projects / "Hand Dropped.json"
        dropped.write_text(
            json.dumps({"title": "Hand Dropped", "sections": [{"name": "Bridge", "measures": [{}]}]})
        )
        listed_all = _run_song_library(env, "list")
        if listed_all.returncode != 0:
            sys.stderr.write(listed_all.stdout + listed_all.stderr)
            raise SystemExit(listed_all.returncode or 1)
        names = {item["id"] for item in json.loads(listed_all.stdout)["projects"]}
        expected = {"Demo Renamed", "Minted", "Flat", "Hand Dropped"}
        if names != expected:
            raise SystemExit(f"list missed project files: {names} vs {expected}")

        loaded = _run_song_library(env, "load", "Hand Dropped")
        if loaded.returncode != 0:
            sys.stderr.write(loaded.stdout + loaded.stderr)
            raise SystemExit(loaded.returncode or 1)
        loaded_doc = json.loads(loaded.stdout)
        if loaded_doc["title"] != "Hand Dropped" or loaded_doc["sections"][0]["name"] != "Bridge":
            raise SystemExit("load did not return the dropped file")

        deleted = _run_song_library(env, "delete", "Flat")
        if deleted.returncode != 0:
            sys.stderr.write(deleted.stdout + deleted.stderr)
            raise SystemExit(deleted.returncode or 1)
        remaining = {item["id"] for item in json.loads(deleted.stdout)["projects"]}
        if "Flat" in remaining:
            raise SystemExit("delete did not remove Flat")
        if (projects / "Flat.json").exists():
            raise SystemExit("delete left Flat.json on disk")

        (runtime / "omarchy-songwriter" / "save-selection.json").unlink(missing_ok=True)
        missing = _run_song_library(env, "save")
        if missing.returncode != 2:
            raise SystemExit("missing selection should exit 2, got " + str(missing.returncode))

        _stage_save(runtime, {"id": "bad", "title": "Bad"})
        invalid = _run_song_library(env, "save")
        if invalid.returncode != 2:
            raise SystemExit("invalid selection should exit 2, got " + str(invalid.returncode))

        no_id = _run_song_library(env, "delete")
        if no_id.returncode != 2:
            raise SystemExit("delete without id should exit 2, got " + str(no_id.returncode))

        missing_load = _run_song_library(env, "load", "no-such-project")
        if missing_load.returncode != 2:
            raise SystemExit("missing load should exit 2, got " + str(missing_load.returncode))

        # Migrate the old single-file library into per-project JSON files.
        other = Path(tmp) / "migrate"
        other_runtime = Path(tmp) / "migrate-runtime"
        other_env = _song_library_env(other, other_runtime)
        library_path = other / "songwriter" / "library.json"
        library_path.parent.mkdir(parents=True)
        library_path.write_text(
            json.dumps(
                {
                    "songs": [
                        {
                            "id": "old-uuid",
                            "title": "From Library",
                            "updatedAt": 1,
                            "song": sample_song,
                        }
                    ]
                }
            )
        )
        migrated = _run_song_library(other_env, "list")
        if migrated.returncode != 0:
            sys.stderr.write(migrated.stdout + migrated.stderr)
            raise SystemExit(migrated.returncode or 1)
        migrated_names = {item["id"] for item in json.loads(migrated.stdout)["projects"]}
        if migrated_names != {"From Library"}:
            raise SystemExit("library.json was not migrated to a project file")
        if library_path.exists():
            raise SystemExit("library.json should be renamed after migration")
        if not (other / "songwriter" / "library.json.bak").is_file():
            raise SystemExit("library.json.bak missing after migration")

        print("song-library ok")


def main() -> int:
    test_manifest()
    test_write_json()
    test_play_notes()
    test_js()
    test_agent()
    test_song_library()
    print("all tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
