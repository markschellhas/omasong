#!/usr/bin/env python3
"""Play one or more sine tones as a chord or single note.

Usage:
  play-notes.py hz1 [hz2 ...] [seconds]
  play-notes.py --midi n1 [n2 ...] [seconds]
  play-notes.py --write out.wav --midi 60 64 67 0.4
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import wave

RATE = 44100
DEFAULT_SECONDS = 0.9
AMPLITUDE = 0.18
ATTACK = 0.08
RELEASE = 0.28
PAD = 0.02


def midi_to_hz(midi: float) -> float:
    return 440.0 * (2.0 ** ((float(midi) - 69.0) / 12.0))


def cosine_ramp(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 0.5 - 0.5 * math.cos(math.pi * x)


def envelope(i: int, n: int, attack: int, release: int) -> float:
    if i < attack:
        return cosine_ramp(i / attack)
    tail = n - 1 - i
    if tail < release:
        return cosine_ramp(tail / release)
    return 1.0


def synth(freqs: list[float], seconds: float, amplitude: float = AMPLITUDE) -> list[int]:
    n = max(1, int(RATE * seconds))
    attack = max(1, int(RATE * ATTACK))
    release = max(1, int(RATE * RELEASE))
    pad = max(0, int(RATE * PAD))
    if attack + release >= n:
        attack = max(1, n // 5)
        release = max(1, n - attack - 1)
    frames = [0] * pad
    voices = [hz for hz in freqs if hz > 0]
    if not voices:
        voices = [0.0]
    for i in range(n):
        env = envelope(i, n, attack, release)
        sample = 0.0
        t = i / RATE
        for hz in voices:
            if hz > 0:
                sample += math.sin(2.0 * math.pi * hz * t)
        val = max(-1.0, min(1.0, sample * amplitude * env))
        frames.append(int(val * 32767))
    frames.extend([0] * pad)
    frames[0] = 0
    frames[-1] = 0
    return frames


def write_wav(path: str, frames: list[int]) -> None:
    with wave.open(path, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(b"".join(struct.pack("<h", sample) for sample in frames))


def play(path: str) -> None:
    for cmd in (
        ["pw-play", path],
        ["paplay", path],
        ["aplay", "-q", path],
    ):
        if shutil.which(cmd[0]):
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    sys.stderr.write("play-notes: no pw-play, paplay, or aplay\n")
    sys.exit(1)


def parse_values(values: list[str]) -> tuple[list[float], float]:
    if not values:
        raise ValueError("expected at least one frequency or MIDI note")
    nums = [float(v) for v in values]
    seconds = DEFAULT_SECONDS
    # A trailing value in a typical duration range is seconds, not a pitch.
    if len(nums) >= 2 and 0 < nums[-1] <= 8 and nums[-1] < 20:
        seconds = nums[-1]
        nums = nums[:-1]
    if not nums:
        raise ValueError("expected at least one frequency or MIDI note")
    return nums, seconds


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Play sine-wave notes or chords")
    parser.add_argument("--midi", action="store_true", help="treat values as MIDI note numbers")
    parser.add_argument("--write", metavar="PATH", help="write WAV instead of playing")
    parser.add_argument("--seconds", type=float, help="override duration in seconds")
    parser.add_argument("values", nargs="+", help="Hz values, or MIDI notes with --midi")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        nums, seconds = parse_values(args.values)
    except ValueError as exc:
        sys.stderr.write("play-notes: %s\n" % exc)
        return 2
    if args.seconds is not None:
        seconds = max(0.05, float(args.seconds))
    freqs = [midi_to_hz(n) for n in nums] if args.midi else nums
    frames = synth(freqs, seconds)
    if args.write:
        write_wav(args.write, frames)
        return 0
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        path = tmp.name
    try:
        write_wav(path, frames)
        play(path)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
