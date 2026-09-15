#!/usr/bin/env python3
"""Play notes as a chord or single pitch.

Piano (instrument 0) uses Salamander Grand Piano samples when present.
Electric Piano (instrument 1) uses Wurlitzer EP200 samples when present.
Organ (instrument 2) uses VSCO 2 CE chapel organ samples when present.
If a sample bank is missing, that timbre falls back to additive sines.

Usage:
  play-notes.py hz1 [hz2 ...] [seconds]
  play-notes.py --midi n1 [n2 ...] [seconds]
  play-notes.py --write out.wav --midi 60 64 67 --instrument 1 --seconds 0.4
  play-notes.py --drums 1000 0010 1111 --steps 4 --bpm 120
  play-notes.py --measure '{"steps":4,"bpm":120,"drums":{},"chords":[]}'
  play-notes.py --engine
"""

from __future__ import annotations

import argparse
import json
import math
import os
import queue
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import wave
from array import array
from pathlib import Path

RATE = 44100
OUTPUT_LATENCY_MS = 20
DEFAULT_SECONDS = 0.9
MAX_SECONDS = 30.0
MIN_SECONDS = 0.05
MAX_VOICES = 8
MIN_BPM = 40.0
MAX_BPM = 240.0
MAX_DRUM_STEPS = 128
DRUM_TAIL_SECONDS = 0.32
MAX_MEASURE_JSON = 16384
MAX_MEASURE_CHORDS = 16
MIDI_MIN = 0
MIDI_MAX = 127
HZ_MIN = 20.0
HZ_MAX = 20000.0
AMPLITUDE = 0.18
PAD = 0.02
PIANO_INSTRUMENT = 0
ELECTRIC_PIANO_INSTRUMENT = 1
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
)

_SAMPLE_CACHE: dict[tuple[str, int], list[float]] = {}
SAMPLE_BANKS = {
    PIANO_INSTRUMENT: {
        "dir": SAMPLE_ROOT / "piano",
        "ready": "C4.wav",
        "loop": False,
        "gain": 0.62,
    },
    ELECTRIC_PIANO_INSTRUMENT: {
        "dir": SAMPLE_ROOT / "epiano",
        "ready": "C4.wav",
        "loop": False,
        "gain": 0.70,
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
    last = len(INSTRUMENTS) - 1
    if n > last:
        return last
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


def clamp_bpm(value: float) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return 120.0
    if not math.isfinite(n):
        return 120.0
    return max(MIN_BPM, min(MAX_BPM, n))


def clamp_drum_steps(value: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError, OverflowError):
        return 16
    return max(1, min(MAX_DRUM_STEPS, n))


def parse_drum_pattern(value: str, steps: int) -> list[bool]:
    count = clamp_drum_steps(steps)
    text = value if isinstance(value, str) else ""
    return [i < len(text) and text[i] == "1" for i in range(count)]


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


def electric_piano_samples_ready() -> bool:
    return sample_bank_ready(ELECTRIC_PIANO_INSTRUMENT)


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


def _noise(seed: int):
    """Yield deterministic white noise in [-1, 1]."""
    state = seed & 0xFFFFFFFF
    while True:
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        yield state / 2147483647.5 - 1.0


def _mix_kick(mix: list[float], start: int) -> None:
    length = min(int(RATE * 0.30), len(mix) - start)
    phase = 0.0
    for i in range(max(0, length)):
        t = i / RATE
        frequency = 45.0 + 115.0 * math.exp(-t * 26.0)
        phase += 2.0 * math.pi * frequency / RATE
        env = math.exp(-t * 15.0)
        mix[start + i] += math.sin(phase) * env * 0.78


def _mix_snare(mix: list[float], start: int, seed: int) -> None:
    length = min(int(RATE * 0.20), len(mix) - start)
    noise = _noise(seed)
    previous = 0.0
    for i in range(max(0, length)):
        t = i / RATE
        raw = next(noise)
        high = raw - previous * 0.65
        previous = raw
        env = math.exp(-t * 24.0)
        body = math.sin(2.0 * math.pi * 185.0 * t) * 0.22
        mix[start + i] += (high * 0.52 + body) * env


def _mix_hihat(mix: list[float], start: int, seed: int) -> None:
    length = min(int(RATE * 0.075), len(mix) - start)
    noise = _noise(seed)
    previous = 0.0
    for i in range(max(0, length)):
        t = i / RATE
        raw = next(noise)
        high = raw - previous
        previous = raw
        mix[start + i] += high * math.exp(-t * 65.0) * 0.28


def measure_frame_counts(steps: int, bpm: float) -> tuple[int, int]:
    count = clamp_drum_steps(steps)
    tempo = clamp_bpm(bpm)
    step_seconds = 60.0 / tempo / 4.0
    nominal_seconds = count * step_seconds
    if nominal_seconds + DRUM_TAIL_SECONDS > MAX_SECONDS:
        raise ValueError("measure duration exceeds limit")
    return (
        max(1, int(round(RATE * nominal_seconds))),
        int(round(RATE * DRUM_TAIL_SECONDS)),
    )


def _drum_mix(kick: str, snare: str, hihat: str, steps: int, bpm: float) -> tuple[array, int]:
    count = clamp_drum_steps(steps)
    tempo = clamp_bpm(bpm)
    step_seconds = 60.0 / tempo / 4.0
    nominal_frames, tail_frames = measure_frame_counts(count, tempo)
    frame_count = nominal_frames + tail_frames
    patterns = (
        parse_drum_pattern(kick, count),
        parse_drum_pattern(snare, count),
        parse_drum_pattern(hihat, count),
    )
    mix = array("f", [0.0]) * frame_count
    for step in range(count):
        start = int(round(RATE * step * step_seconds))
        if patterns[0][step]:
            _mix_kick(mix, start)
        if patterns[1][step]:
            _mix_snare(mix, start, 0x534E0000 + step)
        if patterns[2][step]:
            _mix_hihat(mix, start, 0x48480000 + step)
    return mix, nominal_frames


def _finish_mix(mix: array) -> array:
    fade_frames = min(len(mix), max(1, int(RATE * 0.01)))
    fade_start = len(mix) - fade_frames
    for i in range(fade_start, len(mix)):
        mix[i] *= (len(mix) - 1 - i) / fade_frames
    if mix:
        mix[-1] = 0.0
    peak = max((abs(sample) for sample in mix), default=0.0)
    scale = 0.94 / peak if peak > 0.94 else 1.0
    return array("h", (int(max(-1.0, min(1.0, sample * scale)) * 32767) for sample in mix))


def render_drums(kick: str, snare: str, hihat: str, steps: int, bpm: float) -> array:
    """Render one measure plus a bounded natural-decay tail."""
    mix, _ = _drum_mix(kick, snare, hihat, steps, bpm)
    return _finish_mix(mix)


def _canonical_pattern(value: object, steps: int) -> str:
    return "".join("1" if hit else "0" for hit in parse_drum_pattern(value, steps))


def normalize_measure_spec(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("measure must be an object")
    steps = clamp_drum_steps(value.get("steps", 16))
    bpm = clamp_bpm(value.get("bpm", 120))
    measure_frame_counts(steps, bpm)
    raw_drums = value.get("drums") if isinstance(value.get("drums"), dict) else {}
    drums = {
        "kick": _canonical_pattern(raw_drums.get("kick", ""), steps),
        "snare": _canonical_pattern(raw_drums.get("snare", ""), steps),
        "hihat": _canonical_pattern(raw_drums.get("hihat", ""), steps),
    }
    measure_beats = steps / 4.0
    chords = []
    raw_chords = value.get("chords") if isinstance(value.get("chords"), list) else []
    for raw in raw_chords[:MAX_MEASURE_CHORDS]:
        if not isinstance(raw, dict):
            continue
        try:
            offset = float(raw.get("offsetBeats", 0))
            duration = float(raw.get("durationBeats", 0))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(offset) or not math.isfinite(duration) or offset < 0 or duration <= 0 or offset >= measure_beats:
            continue
        duration = min(duration, measure_beats - offset)
        raw_midis = raw.get("midis") if isinstance(raw.get("midis"), list) else []
        midis = [note for note in (clamp_midi(item) for item in raw_midis) if note is not None][:MAX_VOICES]
        if midis:
            chords.append({"offsetBeats": offset, "durationBeats": duration, "midis": midis})
    return {
        "steps": steps,
        "bpm": bpm,
        "instrument": clamp_instrument(value.get("instrument", 0)),
        "drums": drums,
        "chords": chords,
    }


def parse_measure_spec(raw: str) -> dict:
    if not isinstance(raw, str) or len(raw) > MAX_MEASURE_JSON or len(raw.encode("utf-8")) > MAX_MEASURE_JSON:
        raise ValueError("measure JSON exceeds limit")
    try:
        value = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("invalid measure JSON") from exc
    return normalize_measure_spec(value)


def render_midi_notes(midis: list[float], seconds: float, instrument: int) -> list[int]:
    instrument = clamp_instrument(instrument)
    use_samples = sample_bank_ready(instrument)
    freqs = [midi_to_hz(note) for note in midis]
    if use_samples:
        try:
            return render_samples(midis, seconds, instrument)
        except OSError:
            pass
    return synth(freqs, seconds, instrument=instrument)


def render_measure(value: object) -> array:
    spec = normalize_measure_spec(value)
    drums = spec["drums"]
    mix, _ = _drum_mix(drums["kick"], drums["snare"], drums["hihat"], spec["steps"], spec["bpm"])
    pad_frames = int(RATE * PAD)
    for chord in spec["chords"]:
        start = int(round(RATE * chord["offsetBeats"] * 60.0 / spec["bpm"]))
        seconds = chord["durationBeats"] * 60.0 / spec["bpm"]
        rendered = render_midi_notes(chord["midis"], seconds, spec["instrument"])
        audio = rendered[pad_frames : max(pad_frames, len(rendered) - pad_frames)]
        available = min(len(audio), len(mix) - start)
        for i in range(max(0, available)):
            mix[start + i] += audio[i] / 32767.0
    return _finish_mix(mix)


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


def output_command() -> list[str]:
    if shutil.which("pw-cat"):
        return [
            "pw-cat",
            "-p",
            "-a",
            "--format",
            "s16",
            "--rate",
            str(RATE),
            "--channels",
            "1",
            "--latency",
            "%sms" % OUTPUT_LATENCY_MS,
        ]
    if shutil.which("paplay"):
        return ["paplay", "--raw", "--rate=%s" % RATE, "--channels=1", "--format=s16le"]
    if shutil.which("aplay"):
        return ["aplay", "-q", "-t", "raw", "-f", "S16_LE", "-r", str(RATE), "-c", "1"]
    return []


def clamp_latency_ms(value) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return OUTPUT_LATENCY_MS
    if n <= 0:
        return OUTPUT_LATENCY_MS
    return n


def _s16_array(pcm) -> array:
    if isinstance(pcm, array) and pcm.typecode == "h":
        return pcm
    return array("h", (int(sample) for sample in pcm))


def _pcm_le_bytes(frames) -> bytes:
    samples = _s16_array(frames)
    if sys.byteorder == "little":
        return samples.tobytes()
    swapped = array("h", samples)
    swapped.byteswap()
    return swapped.tobytes()


class BufferSink:
    def __init__(self) -> None:
        self.frames = array("h")

    def write(self, pcm, loop: bool = False) -> None:
        if not pcm:
            return
        self.frames.extend(pcm)
        if loop:
            self.frames.extend(pcm)

    def mix(self, pcm) -> None:
        self.write(pcm)

    def stop(self) -> None:
        return

    def close(self) -> None:
        return


class PipeSink:
    def __init__(self) -> None:
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._queue: queue.Queue = queue.Queue()
        self._mix = array("h")
        self._generation = 0
        self._closed = False
        self._thread = threading.Thread(target=self._run, name="play-notes-pipe", daemon=True)
        self._thread.start()

    def write(self, pcm, loop: bool = False) -> None:
        with self._lock:
            if self._closed:
                return
            self._generation += 1
            gen = self._generation
        self._drain()
        self._queue.put(("play", gen, _s16_array(pcm) if pcm else array("h"), bool(loop)))

    def mix(self, pcm) -> None:
        if not pcm:
            return
        samples = _s16_array(pcm)
        with self._lock:
            if self._closed:
                return
            idle = self._proc is None and self._queue.empty() and not self._mix
            if idle:
                start = True
            else:
                self._mix.extend(samples)
                start = False
        if start:
            self.write(samples)

    def stop(self) -> None:
        with self._lock:
            self._generation += 1
            self._mix = array("h")
        self._drain()

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._generation += 1
            self._mix = array("h")
        self._drain()
        self._queue.put(("close", 0, None, False))
        self._thread.join(timeout=1.0)
        self._close_proc()

    def _drain(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                return

    def _close_proc(self) -> None:
        with self._lock:
            proc = self._proc
            self._proc = None
        if proc is None:
            return
        try:
            if proc.stdin:
                proc.stdin.close()
        except OSError:
            pass
        try:
            proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass

    def _ensure_open(self) -> bool:
        with self._lock:
            if self._closed:
                return False
            if self._proc is not None and self._proc.poll() is None:
                return self._proc.stdin is not None
            self._proc = None
        cmd = output_command()
        if not cmd:
            return False
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            return False
        with self._lock:
            self._proc = proc
            if not self._closed and proc.stdin is not None:
                return True
        self._close_proc()
        return False

    def _apply_mix(self, chunk: array) -> array:
        with self._lock:
            extra = self._mix
            if not extra:
                return chunk
            n = min(len(chunk), len(extra))
            out = array("h", chunk)
            for i in range(n):
                val = int(out[i]) + int(extra[i])
                if val > 32767:
                    val = 32767
                elif val < -32767:
                    val = -32767
                out[i] = val
            self._mix = extra[n:]
        return out

    def _emit(self, samples) -> None:
        if not samples:
            return
        chunk = samples if isinstance(samples, array) and samples.typecode == "h" else _s16_array(samples)
        chunk = self._apply_mix(chunk)
        if not self._ensure_open():
            return
        proc = self._proc
        if proc is None or proc.stdin is None:
            return
        try:
            proc.stdin.write(_pcm_le_bytes(chunk))
            proc.stdin.flush()
        except (BrokenPipeError, OSError):
            self._close_proc()

    def _current_gen(self) -> tuple[bool, int]:
        with self._lock:
            return self._closed, self._generation

    def _run(self) -> None:
        chunk_n = max(1, int(RATE * OUTPUT_LATENCY_MS / 1000.0))
        silence = array("h", [0] * chunk_n)
        idle_until = 0.0
        while True:
            closed, _gen = self._current_gen()
            if closed:
                break
            try:
                item = self._queue.get(timeout=OUTPUT_LATENCY_MS / 1000.0)
            except queue.Empty:
                proc_open = self._proc is not None
                if proc_open:
                    now = time.monotonic()
                    if now >= idle_until:
                        self._emit(silence)
                        idle_until = now + chunk_n / float(RATE)
                continue
            kind, gen, pcm, loop = item
            if kind == "close":
                break
            if kind != "play":
                continue
            while True:
                closed, current = self._current_gen()
                if closed or gen != current:
                    break
                i = 0
                n = len(pcm) if pcm is not None else 0
                aborted = False
                while i < n:
                    closed, current = self._current_gen()
                    if closed or gen != current:
                        aborted = True
                        break
                    self._emit(pcm[i : i + chunk_n])
                    i += chunk_n
                if aborted or not loop or n == 0:
                    break
        self._close_proc()


class AudioEngine:
    def __init__(self, sink=None) -> None:
        self.sink = sink if sink is not None else PipeSink()

    def handle(self, msg: object) -> dict:
        if not isinstance(msg, dict):
            return {"ok": False, "error": "invalid message"}
        cmd = msg.get("cmd")
        if cmd == "warmup":
            sample_bank_ready(clamp_instrument(msg.get("instrument", 0)))
            return {"ok": True}
        if cmd == "play":
            measures = msg.get("measures")
            if not isinstance(measures, list):
                measures = []
            try:
                pcm = schedule_measures(measures)
            except ValueError as exc:
                return {"ok": False, "error": str(exc)}
            self.sink.write(pcm, loop=bool(msg.get("loop")))
            return {
                "event": "started",
                "frames": len(pcm),
                "latencyMs": clamp_latency_ms(msg.get("latencyMs")),
            }
        if cmd == "stop":
            self.sink.stop()
            return {"ok": True}
        if cmd == "play-midi":
            raw = msg.get("midis") if isinstance(msg.get("midis"), list) else []
            midis = [note for note in (clamp_midi(item) for item in raw) if note is not None][:MAX_VOICES]
            if midis:
                seconds = clamp_seconds(msg.get("seconds", DEFAULT_SECONDS))
                pcm = render_midi_notes(midis, seconds, clamp_instrument(msg.get("instrument", 0)))
                mix = getattr(self.sink, "mix", self.sink.write)
                mix(pcm)
            return {"ok": True}
        if cmd == "shutdown":
            self.sink.close()
            return {"ok": True}
        return {"ok": False, "error": "unknown command"}


def run_engine() -> int:
    engine = AudioEngine()
    while True:
        line = sys.stdin.readline()
        if line == "":
            engine.handle({"cmd": "shutdown"})
            return 0
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"ok": False, "error": "invalid json"}), flush=True)
            continue
        if not isinstance(msg, dict):
            print(json.dumps({"ok": False, "error": "invalid message"}), flush=True)
            continue
        result = engine.handle(msg)
        print(json.dumps(result), flush=True)
        if msg.get("cmd") == "shutdown":
            return 0


def write_wav(path: str, frames: list[int]) -> None:
    with wave.open(path, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        if isinstance(frames, array) and frames.typecode == "h" and sys.byteorder == "little":
            wav.writeframes(frames.tobytes())
        else:
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
    parser = argparse.ArgumentParser(description="Play sampled piano, electric piano, or organ notes")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--midi", action="store_true", help="treat values as MIDI note numbers")
    mode.add_argument("--drums", nargs=3, metavar=("KICK", "SNARE", "HIHAT"), help="binary sixteenth-note lane patterns")
    mode.add_argument("--measure", metavar="JSON", help="bounded combined chord and drum measure")
    parser.add_argument("--engine", action="store_true", help="persistent NDJSON audio engine")
    parser.add_argument("--write", metavar="PATH", help="write WAV instead of playing")
    parser.add_argument("--seconds", type=float, help="override duration in seconds")
    parser.add_argument("--instrument", type=int, default=0, help="timbre 0–2 (Piano, Electric Piano, Organ)")
    parser.add_argument("--steps", type=int, default=16, help="drum-pattern length in sixteenth notes")
    parser.add_argument("--bpm", type=float, default=120, help="drum-pattern tempo")
    parser.add_argument("values", nargs="*", help="Hz values, or MIDI notes with --midi")
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
    if args.engine:
        return run_engine()
    if args.measure is not None:
        if args.values or args.seconds is not None:
            sys.stderr.write("play-notes: measure mode does not accept pitches or --seconds\n")
            return 2
        try:
            frames = render_measure(parse_measure_spec(args.measure))
        except ValueError as exc:
            sys.stderr.write("play-notes: %s\n" % exc)
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
    if args.drums is not None:
        if args.values or args.seconds is not None:
            sys.stderr.write("play-notes: drum mode does not accept pitches or --seconds\n")
            return 2
        try:
            frames = render_drums(args.drums[0], args.drums[1], args.drums[2], args.steps, args.bpm)
        except ValueError as exc:
            sys.stderr.write("play-notes: %s\n" % exc)
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
