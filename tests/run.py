#!/usr/bin/env python3
"""Run songwriter plugin unit tests (JS libraries + Python helpers)."""

from __future__ import annotations

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
    libs = {
        "Model": load_pragma_js(ROOT / "js" / "Model.js"),
        "Chords": load_pragma_js(ROOT / "js" / "Chords.js"),
        "Song": load_pragma_js(ROOT / "js" / "Song.js"),
        "Agent": load_pragma_js(ROOT / "js" / "Agent.js"),
        "Keyboard": load_pragma_js(ROOT / "js" / "Keyboard.js"),
        "Focus": load_pragma_js(ROOT / "js" / "Focus.js"),
    }
    harness = r"""
function assert(cond, msg) {
  if (!cond) throw new Error(msg || "assertion failed");
}
function assertEq(a, b, msg) {
  if (a !== b) throw new Error((msg || "assertEq") + ": " + JSON.stringify(a) + " !== " + JSON.stringify(b));
}
"""
    body = (ROOT / "tests" / "js_tests.js").read_text()
    script = (
        "const Model = {};\nconst Chords = {};\nconst Song = {};\nconst Keyboard = {};\nconst Agent = {};\n"
        + "void Model; void Chords; void Song; void Keyboard; void Agent;\n"
        + libs["Model"].replace("function ", "function ")
        + "Object.assign(Model, {PC_NAMES, station, chordName, qualityInt, encodeChord, decodeChord, diatonicTriads, numeralFor, maxSlots, beatsPerBar, triadMidi, FIFTHS, wrap, keyAt, label, diatonic, inKeyWedge, wedgeChords, triad, hitTest, PITCH_CLASS});\n"
        + libs["Chords"]
        + "Object.assign(Chords, {parseChord, isValidChord, getChordSuggestions, transposeChord, midiToHz, midiToNoteName});\n"
        + libs["Song"]
        + "Object.assign(Song, {defaultSong, normalizeSong, setChord, addSection, removeSection, flattenSlots, nextFilledSlot, transposeSong});\n"
        + libs["Agent"]
        + "Object.assign(Agent, {progressionsJson, songJson});\n"
        + libs["Keyboard"]
        + "Object.assign(Keyboard, {midiForKey, twoOctaveKeys, midiToHz, clampOctave, computerKeyForMidi});\n"
        + harness
        + body
        + "\nconsole.log('js tests ok');\n"
    )
    # The above Object.assign after function declarations copies globals.
    # Functions declared at top level in the eval'd script become locals in
    # CommonJS -e, so copy via eval in a Function wrapper instead.
    wrapped = (
        "const vm = require('vm');\n"
        "const sandbox = { console, Math, Date, JSON, Object, Array, String, Number, isFinite };\n"
        "vm.createContext(sandbox);\n"
        + json.dumps(harness + libs["Model"] + libs["Chords"] + libs["Song"] + libs["Agent"] + libs["Keyboard"] + libs["Focus"] + body + "\nconsole.log('js tests ok');\n")
        + ".split('').length;\n"
        "vm.runInContext("
        + json.dumps(harness + libs["Model"] + libs["Chords"] + libs["Song"] + libs["Agent"] + libs["Keyboard"] + libs["Focus"] + body + "\nconsole.log('js tests ok');\n")
        + ", sandbox);\n"
    )
    run_node(wrapped)


def test_play_notes() -> None:
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


def main() -> int:
    test_manifest()
    test_write_json()
    test_play_notes()
    test_js()
    print("all tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
