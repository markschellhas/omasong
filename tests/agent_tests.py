#!/usr/bin/env python3
"""CLI tests for chords-agent (snapshot + optional live loopback)."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "chords-agent"

# Matches js/Agent.js progressionsJson / songJson for defaultSong() in C.
PROGRESSIONS = {
    "key": {"index": 0, "major": "C", "relativeMinor": "Am"},
    "bpm": 120,
    "sections": [
        {
            "name": "Verse",
            "timeSignature": "4/4",
            "rowRepeats": [False],
            "progression": "C | G | F | Dm",
            "chords": [
                {
                    "name": "C",
                    "root": "C",
                    "rootPc": 0,
                    "quality": "major",
                    "bar": 0,
                    "slot": 0,
                    "numeral": "I",
                },
                {
                    "name": "G",
                    "root": "G",
                    "rootPc": 7,
                    "quality": "major",
                    "bar": 1,
                    "slot": 0,
                    "numeral": "V",
                },
                {
                    "name": "F",
                    "root": "F",
                    "rootPc": 5,
                    "quality": "major",
                    "bar": 2,
                    "slot": 0,
                    "numeral": "IV",
                },
                {
                    "name": "Dm",
                    "root": "D",
                    "rootPc": 2,
                    "quality": "minor",
                    "bar": 3,
                    "slot": 0,
                    "numeral": "ii",
                },
            ],
        },
        {
            "name": "Chorus",
            "timeSignature": "4/4",
            "rowRepeats": [False],
            "progression": "D | G | C | Em",
            "chords": [
                {"name": "D", "root": "D", "rootPc": 2, "quality": "major", "bar": 0, "slot": 0},
                {
                    "name": "G",
                    "root": "G",
                    "rootPc": 7,
                    "quality": "major",
                    "bar": 1,
                    "slot": 0,
                    "numeral": "V",
                },
                {
                    "name": "C",
                    "root": "C",
                    "rootPc": 0,
                    "quality": "major",
                    "bar": 2,
                    "slot": 0,
                    "numeral": "I",
                },
                {
                    "name": "Em",
                    "root": "E",
                    "rootPc": 4,
                    "quality": "minor",
                    "bar": 3,
                    "slot": 0,
                    "numeral": "iii",
                },
            ],
        },
    ],
}

SONG = {
    "key": {"index": 0, "major": "C", "relativeMinor": "Am"},
    "bpm": 120,
    "sections": [
        {
            "name": "Verse",
            "timeSignature": "4/4",
            "rowRepeats": [False],
            "measures": [
                {
                    "slots": [
                        {
                            "name": "C",
                            "root": "C",
                            "rootPc": 0,
                            "quality": "major",
                            "numeral": "I",
                        }
                    ]
                },
                {
                    "slots": [
                        {
                            "name": "G",
                            "root": "G",
                            "rootPc": 7,
                            "quality": "major",
                            "numeral": "V",
                        }
                    ]
                },
                {
                    "slots": [
                        {
                            "name": "F",
                            "root": "F",
                            "rootPc": 5,
                            "quality": "major",
                            "numeral": "IV",
                        }
                    ]
                },
                {
                    "slots": [
                        {
                            "name": "Dm",
                            "root": "D",
                            "rootPc": 2,
                            "quality": "minor",
                            "numeral": "ii",
                        }
                    ]
                },
            ],
        },
        {
            "name": "Chorus",
            "timeSignature": "4/4",
            "rowRepeats": [False],
            "measures": [
                {"slots": [{"name": "D", "root": "D", "rootPc": 2, "quality": "major"}]},
                {
                    "slots": [
                        {
                            "name": "G",
                            "root": "G",
                            "rootPc": 7,
                            "quality": "major",
                            "numeral": "V",
                        }
                    ]
                },
                {
                    "slots": [
                        {
                            "name": "C",
                            "root": "C",
                            "rootPc": 0,
                            "quality": "major",
                            "numeral": "I",
                        }
                    ]
                },
                {
                    "slots": [
                        {
                            "name": "Em",
                            "root": "E",
                            "rootPc": 4,
                            "quality": "minor",
                            "numeral": "iii",
                        }
                    ]
                },
            ],
        },
    ],
}


def unused_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = int(sock.getsockname()[1])
    sock.close()
    return port


def write_snapshots(home: Path) -> None:
    home.mkdir(parents=True, exist_ok=True)
    (home / "progressions.json").write_text(json.dumps(PROGRESSIONS))
    (home / "song.json").write_text(json.dumps(SONG))


def run_cli(home: Path, *args: str, port: int | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CHORDS_AGENT_HOME"] = str(home)
    env["CHORDS_AGENT_PORT"] = str(port if port is not None else unused_port())
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_song_from_snapshot() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        write_snapshots(home)
        proc = run_cli(home, "song")
        if proc.returncode != 0:
            raise SystemExit("song snapshot failed:\n" + proc.stdout + proc.stderr)
        doc = json.loads(proc.stdout)
        if "sections" not in doc:
            raise SystemExit("song JSON missing sections")
        if doc["sections"][0]["name"] != "Verse":
            raise SystemExit("song snapshot sections mismatch")
        print("agent song snapshot ok")


def test_progressions_from_snapshot() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        write_snapshots(home)
        proc = run_cli(home, "progressions")
        if proc.returncode != 0:
            raise SystemExit("progressions snapshot failed:\n" + proc.stdout + proc.stderr)
        doc = json.loads(proc.stdout)
        if "C | G | F | Dm" not in doc["sections"][0]["progression"]:
            raise SystemExit("progressions snapshot mismatch")
        print("agent progressions snapshot ok")


def test_health_without_server() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        write_snapshots(home)
        proc = run_cli(home, "health")
        if proc.returncode != 2:
            raise SystemExit(f"health without live server expected 2, got {proc.returncode}")
        print("agent health down ok")


def test_live_without_server() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        write_snapshots(home)
        proc = run_cli(home, "song", "--live")
        if proc.returncode != 2:
            raise SystemExit(f"--live with nothing bound expected 2, got {proc.returncode}")
        proc = run_cli(home, "--live", "progressions")
        if proc.returncode != 2:
            raise SystemExit(f"--live progressions expected 2, got {proc.returncode}")
        print("agent --live down ok")


def test_missing_snapshot_does_not_invent_defaults() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        proc = run_cli(home, "song")
        if proc.returncode == 0:
            raise SystemExit("song must not invent a default when snapshot is missing")
        print("agent missing snapshot ok")


def start_server(home: Path, port: int) -> subprocess.Popen[str] | None:
    server = ROOT / "agent-server.py"
    if not server.is_file():
        return None
    env = os.environ.copy()
    env["CHORDS_AGENT_HOME"] = str(home)
    env["CHORDS_AGENT_PORT"] = str(port)
    proc = subprocess.Popen(
        [sys.executable, str(server), "--home", str(home), "--port", str(port)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.2) as resp:
                if resp.status == 200:
                    return proc
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.05)
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
    return None


def stop_server(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=2)


def test_live_optional() -> None:
    if not CLI.is_file():
        print("agent live skip")
        return
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        write_snapshots(home)
        port = unused_port()
        proc = start_server(home, port)
        if proc is None:
            print("agent live skip")
            return
        try:
            live = run_cli(home, "--live", "song", port=port)
            if live.returncode != 0:
                raise SystemExit("live song failed:\n" + live.stdout + live.stderr)
            doc = json.loads(live.stdout)
            if "sections" not in doc:
                raise SystemExit("live song missing sections")
            health = run_cli(home, "health", port=port)
            if health.returncode != 0:
                raise SystemExit(f"health with live server expected 0, got {health.returncode}")
            print("agent live ok")
        finally:
            stop_server(proc)


def test_health_after_server_stop() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        write_snapshots(home)
        port = unused_port()
        proc = start_server(home, port)
        if proc is None:
            print("agent health-after-stop skip")
            return
        up = run_cli(home, "health", port=port)
        if up.returncode != 0:
            stop_server(proc)
            raise SystemExit(f"health with live server expected 0, got {up.returncode}")
        stop_server(proc)
        down = run_cli(home, "health", port=port)
        if down.returncode != 2:
            raise SystemExit(
                f"health after overlay/server stop expected 2, got {down.returncode}"
            )
        print("agent health after stop ok")


def run() -> int:
    if not CLI.is_file():
        raise SystemExit("missing chords-agent")
    test_song_from_snapshot()
    test_progressions_from_snapshot()
    test_health_without_server()
    test_live_without_server()
    test_missing_snapshot_does_not_invent_defaults()
    test_live_optional()
    test_health_after_server_stop()
    print("agent tests ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
