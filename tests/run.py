#!/usr/bin/env python3
"""Run songwriter plugin unit tests (JS libraries + Python helpers)."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
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
        for path, instrument in ((piano, "0"), (sine, "3")):
            proc = subprocess.run(
                [sys.executable, str(ROOT / "play-notes.py"), "--write", str(path), "--midi", "60", "64", "67", "--instrument", instrument, "--seconds", "0.2"],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                sys.stderr.write(proc.stdout + proc.stderr)
                raise SystemExit(proc.returncode)
        if piano.read_bytes() == sine.read_bytes():
            raise SystemExit("piano samples should not match pad sines")
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
            raise SystemExit("electric piano samples should not match pad sines")
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
            raise SystemExit("organ samples should not match pad sines")
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
