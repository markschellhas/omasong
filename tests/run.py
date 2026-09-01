#!/usr/bin/env python3
"""Run songwriter plugin unit tests (JS libraries + Python helpers)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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

    with tempfile.TemporaryDirectory() as tmp:
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
        for path, instrument in ((piano, "0"), (sine, "1")):
            proc = subprocess.run(
                [sys.executable, str(ROOT / "play-notes.py"), "--write", str(path), "--midi", "60", "64", "67", "--instrument", instrument, "--seconds", "0.2"],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                sys.stderr.write(proc.stdout + proc.stderr)
                raise SystemExit(proc.returncode)
        if piano.read_bytes() == sine.read_bytes():
            raise SystemExit("piano samples should not match electric-piano sines")
        print("play-notes piano samples ok")

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
            raise SystemExit("organ samples should not match electric-piano sines")
        if organ.read_bytes() == piano.read_bytes():
            raise SystemExit("organ samples should not match piano samples")
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


def main() -> int:
    test_manifest()
    test_write_json()
    test_play_notes()
    test_js()
    test_agent()
    print("all tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
