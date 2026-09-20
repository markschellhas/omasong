#!/usr/bin/env python3
"""Songwriter audio adapter.

Transport, sample banks, drum voices, and the PipeWire command come from the
vendored drywet package (see drywet/UPSTREAM). This process keeps the overlay
protocol — warmup / play / play-midi / note-on / note-off — and the paced
stdin clock. drywet's PipeWireSink writes a block and closes on stop, which
restarts pw-cat and underruns the preview path.

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

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import drywet
from drywet.limits import PIPEWIRE_LATENCY_MS

_LOAD_WAV = drywet.instrument.load_wav
_WAV_CACHE: dict[tuple[str, int], list[float]] = {}
_WAV_LOCK = threading.Lock()


def _cached_load_wav(path, sample_rate):
    key = (os.path.abspath(path), int(sample_rate))
    with _WAV_LOCK:
        cached = _WAV_CACHE.get(key)
        if cached is None:
            cached = _LOAD_WAV(path, sample_rate)
            _WAV_CACHE[key] = cached
        return cached


drywet.instrument.load_wav = _cached_load_wav

RATE = drywet.limits.DEFAULT_SAMPLE_RATE
WRITE_CHUNK_MS = 20
OUTPUT_LATENCY_MS = PIPEWIRE_LATENCY_MS
PREFILL_CHUNKS = max(1, int(math.ceil(OUTPUT_LATENCY_MS / WRITE_CHUNK_MS)))
DEFAULT_SECONDS = 0.9
MAX_SECONDS = 30.0
MIN_SECONDS = 0.05
MAX_VOICES = 8
LIVE_RELEASE_SECONDS = 0.08
MIN_BPM = float(drywet.limits.BPM_MIN)
MAX_BPM = float(drywet.limits.BPM_MAX)
MAX_DRUM_STEPS = 128
DRUM_TAIL_SECONDS = 0.32
MAX_MEASURE_JSON = 16384
MAX_MEASURE_CHORDS = 16
MIDI_MIN = drywet.limits.MIDI_MIN
MIDI_MAX = drywet.limits.MIDI_MAX
HZ_MIN = drywet.limits.HZ_MIN
HZ_MAX = drywet.limits.HZ_MAX
PAD = 0.02
PIANO_INSTRUMENT = 0
ELECTRIC_PIANO_INSTRUMENT = 1
ORGAN_INSTRUMENT = 2
INSTRUMENT_COUNT = 3
PIANO_MIDI_MIN = 48
PIANO_MIDI_MAX = 72
SAMPLE_ROOT = _ROOT / "samples"
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
# drywet Synth harmonics (k=1..4). Live sine fallback uses the same series.
_SYNTH_HARMONICS = ((1.0, 1.0), (2.0, 0.35), (3.0, 0.18), (4.0, 0.08))
_SAMPLER_CACHE: dict[int, object] = {}
_SAMPLER_LOCK = threading.Lock()

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
    if n > INSTRUMENT_COUNT - 1:
        return INSTRUMENT_COUNT - 1
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


def synth(freqs: list[float], seconds: float, instrument: int = 0, amplitude: float | None = None) -> list[int]:
    """Additive fallback. Samples, when present, are drywet.Sampler — not this."""
    del instrument
    seconds = clamp_seconds(seconds)
    voices = [hz for hz in freqs if hz and hz > 0]
    n = max(1, int(round(RATE * seconds)))
    mix = [0.0] * n
    if not voices:
        voices = [0.0]
    for hz in voices:
        if hz <= 0:
            continue
        rendered = drywet.instrument.render_additive(hz, seconds, RATE)
        for i, sample in enumerate(rendered[:n]):
            mix[i] += sample
    scale = 1.0
    if amplitude is not None:
        scale = float(amplitude) / 0.18 if amplitude else 1.0
    frames = [int(max(-1.0, min(1.0, sample * scale)) * 32767) for sample in mix]
    if frames:
        frames[0] = 0
        frames[-1] = 0
    return frames


def sample_bank(instrument: int) -> dict | None:
    return SAMPLE_BANKS.get(clamp_instrument(instrument))


def sample_bank_ready(instrument: int) -> bool:
    bank = sample_bank(instrument)
    if not bank:
        return False
    return (bank["dir"] / bank["ready"]).is_file()


def piano_samples_ready() -> bool:
    return sample_bank_ready(PIANO_INSTRUMENT)


def electric_piano_samples_ready() -> bool:
    return sample_bank_ready(ELECTRIC_PIANO_INSTRUMENT)


def organ_samples_ready() -> bool:
    return sample_bank_ready(ORGAN_INSTRUMENT)


def _cached_sampler(instrument: int):
    instrument = clamp_instrument(instrument)
    with _SAMPLER_LOCK:
        if instrument in _SAMPLER_CACHE:
            return _SAMPLER_CACHE[instrument]
        bank = SAMPLE_BANKS[instrument]
        if not (bank["dir"] / bank["ready"]).is_file():
            _SAMPLER_CACHE[instrument] = None
            return None
        ctx = drywet.Context(sample_rate=RATE, channels=1)
        sampler = drywet.Sampler.from_directory(
            ctx, str(bank["dir"]), loop=bool(bank["loop"])
        )
        _SAMPLER_CACHE[instrument] = sampler
        return sampler


def warmup_samples(instrument: int) -> None:
    _cached_sampler(instrument)


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
        if (
            not math.isfinite(offset)
            or not math.isfinite(duration)
            or offset < 0
            or duration <= 0
            or offset >= measure_beats
        ):
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


def _finish_mix(mix: array, loop: bool = False) -> array:
    if not loop:
        fade_frames = min(len(mix), max(1, int(RATE * 0.01)))
        fade_start = len(mix) - fade_frames
        for i in range(fade_start, len(mix)):
            mix[i] *= (len(mix) - 1 - i) / fade_frames
        if mix:
            mix[-1] = 0.0
    peak = max((abs(sample) for sample in mix), default=0.0)
    scale = 0.94 / peak if peak > 0.94 else 1.0
    return array("h", (int(max(-1.0, min(1.0, sample * scale)) * 32767) for sample in mix))


def _floats_to_pcm(frames: list[float], nominal: int, tail: int, loop: bool) -> array:
    mix = array("f", (float(sample) for sample in frames))
    if loop:
        if nominal < 1:
            return array("h")
        if len(mix) < nominal:
            mix.extend([0.0] * (nominal - len(mix)))
        extra = mix[nominal:]
        base = array("f", mix[:nominal])
        for i, sample in enumerate(extra):
            base[i % nominal] += sample
        return _finish_mix(base, loop=True)
    target = max(1, nominal + tail)
    if len(mix) < target:
        mix.extend([0.0] * (target - len(mix)))
    if len(mix) > target:
        mix = mix[:target]
    return _finish_mix(mix, loop=False)


def _mix_note(ctx, sampler, midi: int, dur: float, time: float, gain: float) -> None:
    n = max(1, int(round(float(dur) * RATE)))
    at = int(round(float(time) * RATE))
    if sampler is None:
        drywet.Synth(ctx).trigger_attack_release(int(midi), float(dur), float(time))
        return
    try:
        _src, frames = sampler._nearest(int(midi))
    except (OSError, ValueError):
        drywet.Synth(ctx).trigger_attack_release(int(midi), float(dur), float(time))
        return
    if sampler.loop and n > len(frames):
        out = [looped_sample(frames, i) * gain for i in range(n)]
    else:
        out = [0.0] * n
        limit = min(n, len(frames))
        for i in range(limit):
            out[i] = frames[i] * gain
    release = min(n, max(1, int(RATE * 0.012)))
    if release < n:
        for i in range(n - release, n):
            out[i] *= (n - 1 - i) / float(release)
    ctx.sink.mix(out, at_sample=at)


def _schedule_chords(ctx, spec: dict, cursor: float) -> None:
    chords = spec["chords"]
    if not chords:
        return
    sampler = _cached_sampler(spec["instrument"])
    bank = SAMPLE_BANKS[spec["instrument"]]
    beat = 60.0 / spec["bpm"]
    for chord in chords:
        when = cursor + chord["offsetBeats"] * beat
        dur = chord["durationBeats"] * beat
        midis = [int(round(note)) for note in chord["midis"]]
        voice_gain = float(bank["gain"]) / math.sqrt(len(midis))
        for midi in midis:
            ctx.transport.schedule(
                lambda time, sampler=sampler, midi=midi, dur=dur, voice_gain=voice_gain: _mix_note(
                    ctx, sampler, midi, dur, time, voice_gain
                ),
                when,
            )


def schedule_measures(specs: list[object], loop: bool = False) -> array:
    """Place each measure on drywet's Transport. Tails mix forward; loop wraps them."""
    normalized = [normalize_measure_spec(spec) for spec in specs]
    if not normalized:
        return array("h")
    ctx = drywet.Context(sample_rate=RATE, channels=1)
    ctx.transport.bpm = normalized[0]["bpm"]
    drum = drywet.Drum(ctx)
    cursor = 0.0
    nominal_frames = 0
    for spec in normalized:
        nominal, _tail = measure_frame_counts(spec["steps"], spec["bpm"])
        nominal_frames += nominal
        step_sec = 60.0 / spec["bpm"] / 4.0
        for lane in ("kick", "snare", "hihat"):
            for step, hit in enumerate(spec["drums"][lane]):
                if hit != "1":
                    continue
                when = cursor + step * step_sec
                ctx.transport.schedule(
                    lambda time, lane=lane: drum.trigger(lane, time),
                    when,
                )
        _schedule_chords(ctx, spec, cursor)
        cursor += spec["steps"] * step_sec
    if cursor <= 0:
        return array("h")
    duration = cursor if loop else cursor + DRUM_TAIL_SECONDS
    floats = ctx.transport.render(duration)
    tail_frames = 0 if loop else int(round(RATE * DRUM_TAIL_SECONDS))
    return _floats_to_pcm(floats, nominal_frames, tail_frames, loop)


def render_drums(kick: str, snare: str, hihat: str, steps: int, bpm: float) -> array:
    spec = {
        "steps": steps,
        "bpm": bpm,
        "instrument": 0,
        "drums": {"kick": kick, "snare": snare, "hihat": hihat},
        "chords": [],
    }
    return schedule_measures([spec])


def render_measure(value: object) -> array:
    return schedule_measures([normalize_measure_spec(value)])


def render_midi_notes(midis: list[float], seconds: float, instrument: int) -> array:
    seconds = clamp_seconds(seconds)
    instrument = clamp_instrument(instrument)
    notes = [int(round(note)) for note in midis if clamp_midi(note) is not None][:MAX_VOICES]
    n = max(1, int(round(RATE * seconds)))
    if not notes:
        return _floats_to_pcm([0.0] * n, n, 0, loop=False)
    ctx = drywet.Context(sample_rate=RATE, channels=1)
    sampler = _cached_sampler(instrument)
    gain = float(SAMPLE_BANKS[instrument]["gain"]) / math.sqrt(len(notes))
    for midi in notes:
        ctx.transport.schedule(
            lambda time, midi=midi: _mix_note(ctx, sampler, midi, seconds, time, gain),
            0.0,
        )
    floats = ctx.transport.render(seconds)
    return _floats_to_pcm(floats, n, 0, loop=False)


def output_command() -> list[str]:
    """drywet PipeWire argv, plus the 80ms node latency the playhead offsets by.

    pw-cat's default latency is 100ms. The paced writer leads by OUTPUT_LATENCY_MS;
    a longer node underruns and the preview stutters.
    """
    try:
        cmd = list(drywet.PipeWireSink(sample_rate=RATE, channels=1)._cmd())
    except RuntimeError:
        return []
    if cmd and cmd[0] == "pw-cat":
        if cmd[-1] == "-":
            cmd = cmd[:-1] + ["--latency", "%sms" % OUTPUT_LATENCY_MS, "-"]
        else:
            cmd.append("--latency")
            cmd.append("%sms" % OUTPUT_LATENCY_MS)
    return cmd


def _s16_array(pcm) -> array:
    if isinstance(pcm, array) and pcm.typecode == "h":
        return pcm
    return array("h", (int(sample) for sample in pcm))


def _sat_s16(value: int) -> int:
    if value > 32767:
        return 32767
    if value < -32767:
        return -32767
    return value


def overlay_s16(existing: array, incoming: array) -> array:
    """Mix incoming onto existing at index 0 (now), extending if needed."""
    if not incoming:
        return existing if isinstance(existing, array) and existing.typecode == "h" else array("h")
    src = incoming if isinstance(incoming, array) and incoming.typecode == "h" else _s16_array(incoming)
    if not existing:
        return array("h", src)
    dst = existing if isinstance(existing, array) and existing.typecode == "h" else _s16_array(existing)
    n = len(dst)
    extra = len(src) - n
    if extra > 0:
        out = array("h", dst)
        out.extend(src[n:])
    else:
        out = array("h", dst)
    limit = n if extra > 0 else len(src)
    for i in range(limit):
        out[i] = _sat_s16(int(out[i]) + int(src[i]))
    return out


class LiveVoice:
    """Freeform held note mixed a chunk at a time. Not a prerendered one-shot.

    Sample bytes come from drywet.Sampler. The voice still advances one chunk
    per clock tick so note-off, not a fixed duration, ends the note.
    """

    def __init__(self, midi: float, instrument: int) -> None:
        self.midi = int(midi)
        self.instrument = clamp_instrument(instrument)
        self.pos = 0
        self.releasing = False
        self.release_i = 0
        self.release_n = max(1, int(RATE * LIVE_RELEASE_SECONDS))
        self.done = False
        self.attack = max(1, int(RATE * 0.01))
        self.harmonics = _SYNTH_HARMONICS
        self.amp = 0.18
        bank = sample_bank(self.instrument)
        self.loop = bool(bank and bank.get("loop"))
        self.gain = float((bank or {}).get("gain", 0.62))
        self.buf: list[float] | None = None
        self.hz = midi_to_hz(self.midi)
        sampler = _cached_sampler(self.instrument)
        if sampler is not None:
            try:
                _src, frames = sampler._nearest(self.midi)
                self.buf = frames
            except (OSError, ValueError):
                self.buf = None

    def release(self) -> None:
        if not self.releasing:
            self.releasing = True
            self.release_i = 0

    def mix_into(self, chunk: array) -> bool:
        if self.done or not chunk:
            return not self.done
        n = len(chunk)
        harm_sum = sum(gain for _, gain in self.harmonics) or 1.0
        for i in range(n):
            env = 1.0
            if self.buf is None and self.pos < self.attack:
                env = cosine_ramp(self.pos / self.attack)
            if self.releasing:
                if self.release_i >= self.release_n:
                    self.done = True
                    return False
                env *= cosine_ramp(1.0 - self.release_i / float(self.release_n))
                self.release_i += 1
            if self.buf is not None:
                if self.loop:
                    val = looped_sample(self.buf, self.pos)
                elif self.pos < len(self.buf):
                    val = self.buf[self.pos]
                else:
                    self.done = True
                    return False
                sample = val * self.gain * env
            else:
                t = self.pos / float(RATE)
                acc = 0.0
                for mult, gain in self.harmonics:
                    acc += math.sin(2.0 * math.pi * self.hz * mult * t) * gain
                sample = acc / harm_sum * self.amp * env
            chunk[i] = _sat_s16(int(chunk[i]) + int(sample * 32767))
            self.pos += 1
        return True


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

    def note_on(self, midi: float, instrument: int = 0) -> None:
        return

    def note_off(self, midi: float) -> None:
        return

    def stop(self) -> None:
        return

    def close(self) -> None:
        return


class PipeSink:
    def __init__(self, proc=None) -> None:
        self._owns_proc = proc is None
        self._proc = proc
        self._lock = threading.Lock()
        self._queue: queue.Queue = queue.Queue()
        self._mix = array("h")
        self._voices: list[LiveVoice] = []
        self._generation = 0
        self._closed = False
        self._clock = None
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

    def start(self) -> None:
        with self._lock:
            if self._closed or self._clock is not None:
                return
        self._queue.put(("run", 0, None, False))

    def mix(self, pcm) -> None:
        if not pcm:
            self.start()
            return
        samples = _s16_array(pcm)
        with self._lock:
            if self._closed:
                return
            # Overlay at the write cursor so overlapping notes chord instead of
            # queueing as a 0.45s monophonic series. Never write() the chord —
            # that restarts the clock and dumps OUTPUT_LATENCY_MS as a gulp.
            self._mix = overlay_s16(self._mix, samples)
            live = self._clock is not None
        if not live:
            self.start()

    def note_on(self, midi: float, instrument: int = 0) -> None:
        note = clamp_midi(midi)
        if note is None:
            return
        voice = LiveVoice(note, instrument)
        with self._lock:
            if self._closed:
                return
            kept = [v for v in self._voices if v.midi != voice.midi]
            kept.append(voice)
            if len(kept) > MAX_VOICES:
                kept = kept[-MAX_VOICES:]
            self._voices = kept
            live = self._clock is not None
        if not live:
            self.start()

    def note_off(self, midi: float) -> None:
        note = clamp_midi(midi)
        if note is None:
            return
        want = int(note)
        with self._lock:
            for voice in self._voices:
                if voice.midi == want:
                    voice.release()

    def stop(self) -> None:
        with self._lock:
            self._generation += 1
            self._mix = array("h")
        self._drain()
        self._queue.put(("run", 0, None, False))

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._generation += 1
            self._mix = array("h")
            self._voices = []
            self._clock = None
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
            if not self._owns_proc:
                return self._proc is not None and self._proc.stdin is not None
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
            voices = self._voices
            if not extra and not voices:
                return chunk
            out = array("h", chunk)
            if extra:
                n = min(len(out), len(extra))
                for i in range(n):
                    out[i] = _sat_s16(int(out[i]) + int(extra[i]))
                self._mix = extra[n:]
            if voices:
                alive = []
                for voice in voices:
                    if voice.mix_into(out):
                        alive.append(voice)
                self._voices = alive
        return out

    def _emit(self, samples, apply_mix: bool = True) -> None:
        if not samples:
            return
        chunk = samples if isinstance(samples, array) and samples.typecode == "h" else _s16_array(samples)
        if apply_mix:
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
        # Prefill OUTPUT_LATENCY_MS of silence, then pace from a steady clock so
        # emit cost is not added onto every chunk (that underruns after a few bars).
        # Keepalive must hold the same lead as play: one 20ms chunk is less than
        # pw-cat's latency, so the stream underruns and preview stutters.
        # Do not reset the clock on play — warmup already filled the node, and a
        # second prefill would make the downbeat (and the next chord) late.
        chunk_n = max(1, int(RATE * WRITE_CHUNK_MS / 1000.0))
        prefill = chunk_n * PREFILL_CHUNKS
        silence = array("h", [0] * chunk_n)
        origin = None
        written = 0
        play_pcm = None
        play_pos = 0
        play_loop = False
        play_gen = 0

        def begin_clock() -> None:
            nonlocal origin, written
            if origin is not None:
                return
            for _ in range(PREFILL_CHUNKS):
                self._emit(silence, apply_mix=False)
                written += chunk_n
            origin = time.monotonic()
            with self._lock:
                self._clock = origin

        def next_chunk(current_gen: int) -> array:
            nonlocal play_pcm, play_pos
            if play_pcm is None or play_gen != current_gen:
                return silence
            n = len(play_pcm)
            if n == 0:
                play_pcm = None
                return silence
            if play_pos >= n:
                if play_loop:
                    play_pos = 0
                else:
                    play_pcm = None
                    return silence
            chunk = play_pcm[play_pos : play_pos + chunk_n]
            play_pos += len(chunk)
            if not chunk:
                play_pcm = None
                return silence
            if len(chunk) < chunk_n:
                padded = array("h", chunk)
                padded.extend([0] * (chunk_n - len(chunk)))
                if not play_loop:
                    play_pcm = None
                return padded
            return chunk

        while True:
            closed, current = self._current_gen()
            if closed:
                break
            timeout = WRITE_CHUNK_MS / 1000.0
            if origin is not None:
                due = origin + max(0, written - prefill) / float(RATE)
                timeout = max(0.0, due - time.monotonic())
            try:
                item = self._queue.get(timeout=timeout)
            except queue.Empty:
                item = None
            if item is not None:
                kind, gen, pcm, loop = item
                if kind == "close":
                    break
                if kind == "run":
                    begin_clock()
                    continue
                if kind == "play":
                    begin_clock()
                    play_pcm = pcm
                    play_pos = 0
                    play_loop = loop
                    play_gen = gen
                    continue
            if origin is None:
                continue
            played = int((time.monotonic() - origin) * RATE)
            if written > played + prefill:
                continue
            closed, current = self._current_gen()
            if closed:
                break
            self._emit(next_chunk(current))
            written += chunk_n
        self._close_proc()



class AudioEngine:
    def __init__(self, sink=None) -> None:
        self.sink = sink if sink is not None else PipeSink()

    def handle(self, msg: object) -> dict:
        if not isinstance(msg, dict):
            return {"ok": False, "error": "invalid message"}
        cmd = msg.get("cmd")
        if cmd == "warmup":
            instrument = clamp_instrument(msg.get("instrument", 0))
            warmup_samples(instrument)
            start = getattr(self.sink, "start", None)
            if callable(start):
                start()
            return {"ok": True}
        if cmd == "play":
            measures = msg.get("measures")
            if not isinstance(measures, list):
                measures = []
            try:
                pcm = schedule_measures(measures, loop=bool(msg.get("loop")))
            except ValueError as exc:
                return {"ok": False, "error": str(exc)}
            self.sink.write(pcm, loop=bool(msg.get("loop")))
            started = {
                "event": "started",
                "frames": len(pcm),
                "latencyMs": OUTPUT_LATENCY_MS,
            }
            if "id" in msg:
                started["id"] = msg["id"]
            return started
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
        if cmd == "note-on":
            midi = clamp_midi(msg.get("midi"))
            if midi is None:
                return {"ok": False, "error": "invalid midi"}
            note_on = getattr(self.sink, "note_on", None)
            if callable(note_on):
                note_on(midi, clamp_instrument(msg.get("instrument", 0)))
            return {"ok": True}
        if cmd == "note-off":
            midi = clamp_midi(msg.get("midi"))
            if midi is None:
                return {"ok": False, "error": "invalid midi"}
            note_off = getattr(self.sink, "note_off", None)
            if callable(note_off):
                note_off(midi)
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
            wav.writeframes(b"".join(struct.pack("<h", int(sample)) for sample in frames))


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


def render(args: argparse.Namespace, nums: list[float], seconds: float):
    instrument = clamp_instrument(args.instrument)
    use_samples = sample_bank_ready(instrument)
    if args.midi:
        midis = [n for n in nums if clamp_midi(n) is not None][:MAX_VOICES]
        if not midis:
            return []
        if use_samples:
            try:
                return render_midi_notes(midis, seconds, instrument)
            except OSError:
                pass
        return synth([midi_to_hz(n) for n in midis], seconds, instrument=instrument)
    freqs = [hz for hz in (clamp_hz(n) for n in nums) if hz is not None][:MAX_VOICES]
    if not freqs:
        return []
    if use_samples:
        try:
            return render_midi_notes([hz_to_midi(hz) for hz in freqs], seconds, instrument)
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
