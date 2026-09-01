#!/usr/bin/env python3
"""Play notes as a chord or single pitch.

Piano (instrument 0) uses Salamander Grand Piano samples when present.
Organ (instrument 2) uses Orgue Eglise Full samples when present.
Other timbres are additive sines.

Usage:
  play-notes.py hz1 [hz2 ...] [seconds]
  play-notes.py --midi n1 [n2 ...] [seconds]
  play-notes.py --write out.wav --midi 60 64 67 --instrument 1 --seconds 0.4
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
from pathlib import Path

RATE = 44100
DEFAULT_SECONDS = 0.9
MAX_SECONDS = 30.0
MIN_SECONDS = 0.05
MAX_VOICES = 8
MIDI_MIN = 0
MIDI_MAX = 127
HZ_MIN = 20.0
HZ_MAX = 20000.0
AMPLITUDE = 0.18
PAD = 0.02
PIANO_INSTRUMENT = 0
ORGAN_INSTRUMENT = 2
PIANO_MIDI_MIN = 48
PIANO_MIDI_MAX = 72
SAMPLE_ROOT = Path(__file__).resolve().parent / "samples"
SAMPLE_DIR = SAMPLE_ROOT / "piano"
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")

# Additive sines used when a sampled bank is missing.
INSTRUMENTS = (
    {  # 0 Piano
        "harmonics": ((1.0, 1.0), (2.0, 0.18), (3.0, 0.07)),
        "attack": 0.012,
        "release": 0.32,
        "amplitude": 0.20,
    },
    {  # 1 Electric Piano
        "harmonics": ((1.0, 1.0), (2.0, 0.35), (4.0, 0.12), (7.0, 0.06)),
        "attack": 0.008,
        "release": 0.22,
        "amplitude": 0.18,
    },
    {  # 2 Organ
        "harmonics": ((1.0, 0.85), (2.0, 0.45), (3.0, 0.35), (4.0, 0.2), (6.0, 0.12)),
        "attack": 0.02,
        "release": 0.08,
        "amplitude": 0.14,
    },
    {  # 3 Pad
        "harmonics": ((1.0, 1.0), (2.0, 0.22), (3.0, 0.12), (5.0, 0.08)),
        "attack": 0.18,
        "release": 0.40,
        "amplitude": 0.16,
    },
    {  # 4 Strings
        "harmonics": ((1.0, 1.0), (2.0, 0.4), (3.0, 0.25), (4.0, 0.15), (5.0, 0.1)),
        "attack": 0.14,
        "release": 0.36,
        "amplitude": 0.15,
    },
)

_SAMPLE_CACHE: dict[tuple[str, int], list[float]] = {}
SAMPLE_BANKS = {
    PIANO_INSTRUMENT: {
        "dir": SAMPLE_ROOT / "piano",
        "ready": "C4.wav",
        "loop": False,
        "gain": 0.62,
    },
    ORGAN_INSTRUMENT: {
        "dir": SAMPLE_ROOT / "organ",
        "ready": "C4.wav",
        "loop": True,
        "gain": 0.48,
    },
}


def clamp_instrument(value: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return 0
    if n < 0:
        return 0
    if n > 4:
        return 4
    return n


def clamp_seconds(value: float) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return DEFAULT_SECONDS
    if not math.isfinite(n):
        return DEFAULT_SECONDS
    if n < MIN_SECONDS:
        return MIN_SECONDS
    if n > MAX_SECONDS:
        return MAX_SECONDS
    return n


def clamp_midi(value: float) -> float | None:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(n) or n < MIDI_MIN or n > MIDI_MAX:
        return None
    return n


def clamp_hz(value: float) -> float | None:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(n) or n < HZ_MIN or n > HZ_MAX:
        return None
    return n


def midi_to_hz(midi: float) -> float:
    return 440.0 * (2.0 ** ((float(midi) - 69.0) / 12.0))


def hz_to_midi(hz: float) -> float:
    return 69.0 + 12.0 * math.log2(float(hz) / 440.0)


def midi_note_name(midi: int) -> str:
    n = int(midi)
    return f"{NOTE_NAMES[n % 12]}{n // 12 - 1}"


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


def synth(freqs: list[float], seconds: float, instrument: int = 0, amplitude: float | None = None) -> list[int]:
    spec = INSTRUMENTS[clamp_instrument(instrument)]
    if amplitude is None:
        amplitude = spec["amplitude"]
    n = max(1, int(RATE * seconds))
    attack = max(1, int(RATE * spec["attack"]))
    release = max(1, int(RATE * spec["release"]))
    pad = max(0, int(RATE * PAD))
    if attack + release >= n:
        attack = max(1, n // 5)
        release = max(1, n - attack - 1)
    frames = [0] * pad
    voices = [hz for hz in freqs if hz > 0]
    if not voices:
        voices = [0.0]
    harm_sum = sum(gain for _, gain in spec["harmonics"]) or 1.0
    for i in range(n):
        env = envelope(i, n, attack, release)
        sample = 0.0
        t = i / RATE
        for hz in voices:
            if hz <= 0:
                continue
            for mult, gain in spec["harmonics"]:
                sample += math.sin(2.0 * math.pi * hz * mult * t) * gain
        val = max(-1.0, min(1.0, sample / harm_sum * amplitude * env))
        frames.append(int(val * 32767))
    frames.extend([0] * pad)
    frames[0] = 0
    frames[-1] = 0
    return frames


def piano_samples_ready() -> bool:
    return sample_bank_ready(PIANO_INSTRUMENT)


def organ_samples_ready() -> bool:
    return sample_bank_ready(ORGAN_INSTRUMENT)


def sample_bank(instrument: int) -> dict | None:
    return SAMPLE_BANKS.get(clamp_instrument(instrument))


def sample_bank_ready(instrument: int) -> bool:
    bank = sample_bank(instrument)
    if not bank:
        return False
    return (bank["dir"] / bank["ready"]).is_file()


def sample_path(midi: int, bank: dict | None = None) -> Path:
    folder = SAMPLE_DIR if bank is None else bank["dir"]
    return folder / f"{midi_note_name(midi)}.wav"


def load_sample_mono(midi: int, max_source_frames: int | None, bank: dict | None = None) -> list[float]:
    folder = str(SAMPLE_DIR if bank is None else bank["dir"])
    cache_key = (folder, midi)
    cached = _SAMPLE_CACHE.get(cache_key)
    if cached is not None and (max_source_frames is None or len(cached) >= max_source_frames):
        return cached
    path = sample_path(midi, bank)
    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        width = wav.getsampwidth()
        rate = wav.getframerate()
        nframes = wav.getnframes()
        if max_source_frames is None:
            need = nframes
        else:
            need = min(nframes, max(1, max_source_frames))
        if rate != RATE and rate > 0 and max_source_frames is not None:
            need = min(nframes, int(need * rate / float(RATE)) + 2)
        raw = wav.readframes(need)
    if width != 2 or channels < 1:
        raise ValueError("samples must be 16-bit PCM")
    count = len(raw) // 2
    samples = struct.unpack("<" + "h" * count, raw)
    if channels == 1:
        mono = [s / 32768.0 for s in samples]
    else:
        frames = count // channels
        mono = [0.0] * frames
        for i in range(frames):
            acc = 0.0
            base = i * channels
            for c in range(channels):
                acc += samples[base + c]
            mono[i] = acc / channels / 32768.0
    if rate != RATE and rate > 0:
        mono = resample(mono, rate / float(RATE))
    _SAMPLE_CACHE[cache_key] = mono
    return mono


def resample(samples: list[float], ratio: float) -> list[float]:
    if ratio <= 0 or not samples:
        return []
    if abs(ratio - 1.0) < 1e-9:
        return list(samples)
    n = max(1, int(round(len(samples) / ratio)))
    last = len(samples) - 1
    out = [0.0] * n
    for i in range(n):
        src = i * ratio
        j = int(src)
        frac = src - j
        a = samples[j] if j <= last else 0.0
        b = samples[j + 1] if j + 1 <= last else 0.0
        out[i] = a + (b - a) * frac
    return out


def nearest_piano_midi(midi: float) -> int:
    n = int(round(float(midi)))
    if n < PIANO_MIDI_MIN:
        return PIANO_MIDI_MIN
    if n > PIANO_MIDI_MAX:
        return PIANO_MIDI_MAX
    return n


def looped_sample(buf: list[float], index: int) -> float:
    if not buf:
        return 0.0
    if index < len(buf):
        return buf[index]
    start = min(int(RATE * 0.35), max(0, len(buf) // 5))
    loop_len = len(buf) - start
    if loop_len < 1:
        return buf[-1]
    return buf[start + (index - start) % loop_len]


def sample_for_midi(midi: float, max_output: int | None, bank: dict | None = None) -> list[float]:
    source = nearest_piano_midi(midi)
    semitones = float(midi) - source
    ratio = 2.0 ** (semitones / 12.0) if abs(semitones) >= 1e-6 else 1.0
    loop = bool(bank and bank.get("loop"))
    if loop or max_output is None:
        source_needed = None
    else:
        source_needed = int(max_output * ratio) + 2
    buf = load_sample_mono(source, source_needed, bank)
    if abs(ratio - 1.0) < 1e-9:
        return buf
    return resample(buf, ratio)


def render_piano(midis: list[float], seconds: float) -> list[int]:
    return render_samples(midis, seconds, PIANO_INSTRUMENT)


def render_samples(midis: list[float], seconds: float, instrument: int) -> list[int]:
    bank = sample_bank(instrument)
    if not bank:
        return synth([midi_to_hz(m) for m in midis], seconds, instrument=instrument)
    n = max(1, int(RATE * seconds))
    pad = max(0, int(RATE * PAD))
    loop = bool(bank.get("loop"))
    voices = [sample_for_midi(m, None if loop else n, bank) for m in midis if math.isfinite(m)]
    if not voices:
        return synth([midi_to_hz(60)], seconds, instrument=instrument)
    mix = [0.0] * n
    gain = float(bank.get("gain", 0.62)) / math.sqrt(len(voices))
    release = max(1, min(int(RATE * 0.12), n // 4))
    for buf in voices:
        for i in range(n):
            env = 1.0
            tail = n - 1 - i
            if tail < release:
                env = cosine_ramp(tail / release)
            if loop:
                val = looped_sample(buf, i)
            elif i < len(buf):
                val = buf[i]
            else:
                val = 0.0
            mix[i] += val * gain * env
    peak = max((abs(x) for x in mix), default=0.0)
    if peak > 0.95:
        scale = 0.95 / peak
        mix = [x * scale for x in mix]
    frames = [0] * pad
    for sample in mix:
        val = max(-1.0, min(1.0, sample))
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
    parser = argparse.ArgumentParser(description="Play sampled piano/organ or sine-wave notes")
    parser.add_argument("--midi", action="store_true", help="treat values as MIDI note numbers")
    parser.add_argument("--write", metavar="PATH", help="write WAV instead of playing")
    parser.add_argument("--seconds", type=float, help="override duration in seconds")
    parser.add_argument("--instrument", type=int, default=0, help="timbre 0–4")
    parser.add_argument("values", nargs="+", help="Hz values, or MIDI notes with --midi")
    return parser


def render(args: argparse.Namespace, nums: list[float], seconds: float) -> list[int]:
    instrument = clamp_instrument(args.instrument)
    use_samples = sample_bank_ready(instrument)
    if args.midi:
        midis = [n for n in nums if clamp_midi(n) is not None][:MAX_VOICES]
        if not midis:
            return []
        freqs = [midi_to_hz(n) for n in midis]
        if use_samples:
            try:
                return render_samples(midis, seconds, instrument)
            except OSError:
                pass
        return synth(freqs, seconds, instrument=instrument)
    freqs = [hz for hz in (clamp_hz(n) for n in nums) if hz is not None][:MAX_VOICES]
    if not freqs:
        return []
    if use_samples:
        try:
            return render_samples([hz_to_midi(hz) for hz in freqs], seconds, instrument)
        except OSError:
            pass
    return synth(freqs, seconds, instrument=instrument)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        nums, seconds = parse_values(args.values)
    except ValueError as exc:
        sys.stderr.write("play-notes: %s\n" % exc)
        return 2
    if args.seconds is not None:
        seconds = clamp_seconds(args.seconds)
    else:
        seconds = clamp_seconds(seconds)
    frames = render(args, nums, seconds)
    if not frames:
        sys.stderr.write("play-notes: no valid pitches\n")
        return 2
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
