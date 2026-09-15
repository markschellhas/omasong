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
    sample_song = {"sections": [{"name": "Verse", "measures": []}]}

    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp) / "data"
        runtime = Path(tmp) / "runtime"
        env = _song_library_env(data, runtime)

        got = _run_song_library(env, "get")
        if got.returncode != 0:
            sys.stderr.write(got.stdout + got.stderr)
            raise SystemExit(got.returncode or 1)
        library = json.loads(got.stdout)
        if library != {"songs": []}:
            raise SystemExit("get should create empty library")
        library_path = data / "songwriter" / "library.json"
        if not library_path.is_file():
            raise SystemExit("get did not create library.json")

        _stage_save(
            runtime,
            {"id": "song-1", "title": "Demo", "song": sample_song},
        )
        saved = _run_song_library(env, "save")
        if saved.returncode != 0:
            sys.stderr.write(saved.stdout + saved.stderr)
            raise SystemExit(saved.returncode or 1)
        library = json.loads(saved.stdout)
        if len(library["songs"]) != 1 or library["songs"][0]["id"] != "song-1":
            raise SystemExit("save did not upsert entry")
        if library["songs"][0]["title"] != "Demo":
            raise SystemExit("save title mismatch")
        if not isinstance(library["songs"][0]["updatedAt"], (int, float)):
            raise SystemExit("save missing updatedAt")

        _stage_save(
            runtime,
            {"id": "song-1", "title": "Demo Updated", "song": sample_song},
        )
        updated = _run_song_library(env, "save")
        if updated.returncode != 0:
            sys.stderr.write(updated.stdout + updated.stderr)
            raise SystemExit(updated.returncode or 1)
        library = json.loads(updated.stdout)
        if len(library["songs"]) != 1:
            raise SystemExit("upsert should keep single entry for same id")
        if library["songs"][0]["title"] != "Demo Updated":
            raise SystemExit("save did not update title")

        _stage_save(
            runtime,
            {"id": "", "title": "Minted", "song": sample_song},
        )
        minted = _run_song_library(env, "save")
        if minted.returncode != 0:
            sys.stderr.write(minted.stdout + minted.stderr)
            raise SystemExit(minted.returncode or 1)
        library = json.loads(minted.stdout)
        if len(library["songs"]) != 2:
            raise SystemExit("empty id should mint a new entry")
        minted_id = library["songs"][0]["id"]
        if not minted_id or minted_id == "song-1":
            raise SystemExit("minted id missing or colliding")
        if library["songs"][0]["title"] != "Minted":
            raise SystemExit("minted save title mismatch")

        _stage_save(
            runtime,
            {"id": "   ", "title": "Whitespace Id", "song": sample_song},
        )
        ws_id = _run_song_library(env, "save")
        if ws_id.returncode != 0:
            sys.stderr.write(ws_id.stdout + ws_id.stderr)
            raise SystemExit(ws_id.returncode or 1)
        library = json.loads(ws_id.stdout)
        if len(library["songs"]) != 3:
            raise SystemExit("whitespace id should mint a new entry")
        ws_minted = library["songs"][0]["id"]
        if not ws_minted or ws_minted in ("song-1", minted_id, "   "):
            raise SystemExit("whitespace id was not minted")

        _stage_save(
            runtime,
            {
                "id": "flat-1",
                "title": "Flat",
                "sections": [{"name": "Chorus", "measures": []}],
                "bpm": 100,
            },
        )
        flat = _run_song_library(env, "save")
        if flat.returncode != 0:
            sys.stderr.write(flat.stdout + flat.stderr)
            raise SystemExit(flat.returncode or 1)
        library = json.loads(flat.stdout)
        flat_entry = library["songs"][0]
        if flat_entry["id"] != "flat-1" or flat_entry["title"] != "Flat":
            raise SystemExit("flat hybrid id/title mismatch")
        if "id" in flat_entry["song"] or "title" in flat_entry["song"]:
            raise SystemExit("flat hybrid nested id/title into song")
        if flat_entry["song"].get("sections") != [{"name": "Chorus", "measures": []}]:
            raise SystemExit("flat hybrid did not preserve song body")
        if flat_entry["song"].get("bpm") != 100:
            raise SystemExit("flat hybrid dropped song fields")

        deleted = _run_song_library(env, "delete", minted_id)
        if deleted.returncode != 0:
            sys.stderr.write(deleted.stdout + deleted.stderr)
            raise SystemExit(deleted.returncode or 1)
        library = json.loads(deleted.stdout)
        if any(s["id"] == minted_id for s in library["songs"]):
            raise SystemExit("delete did not remove minted entry")

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

        # Restore a valid library, then corrupt and assert bytes unchanged.
        _stage_save(
            runtime,
            {"id": "song-1", "title": "Demo Updated", "song": sample_song},
        )
        restored = _run_song_library(env, "save")
        if restored.returncode != 0:
            sys.stderr.write(restored.stdout + restored.stderr)
            raise SystemExit(restored.returncode or 1)

        corrupt_bytes = b"not-json"
        library_path.write_bytes(corrupt_bytes)
        corrupt = _run_song_library(env, "get")
        if corrupt.returncode != 4:
            raise SystemExit("corrupt library should exit 4, got " + str(corrupt.returncode))
        if library_path.read_bytes() != corrupt_bytes:
            raise SystemExit("corrupt library was overwritten")

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
