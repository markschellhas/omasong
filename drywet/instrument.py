import math
import os
import re
import struct
import wave

from drywet.limits import DEFAULT_MAX_VOICES
from drywet.pitch import midi_to_hz, note_to_midi
from drywet.time import to_seconds

_WAV_NAME = re.compile(r"^([A-Ga-g][#b]?\d+)\.wav$", re.IGNORECASE)


def _envelope(index, n, attack, release):
    if n <= 1:
        return 0.0
    if index < attack:
        return index / float(attack) if attack else 1.0
    tail = n - 1 - index
    if tail < release:
        return tail / float(release) if release else 1.0
    return 1.0


def render_additive(freq, duration, sample_rate, harmonics=(1.0, 0.35, 0.18, 0.08)):
    n = max(1, int(round(duration * sample_rate)))
    attack = max(1, int(0.01 * sample_rate))
    release = max(1, int(0.05 * sample_rate))
    if attack + release >= n:
        attack = max(1, n // 5)
        release = max(1, n - attack - 1)
    frames = []
    for i in range(n):
        env = _envelope(i, n, attack, release)
        sample = 0.0
        t = i / float(sample_rate)
        for k, amp in enumerate(harmonics, 1):
            sample += amp * math.sin(2.0 * math.pi * freq * k * t)
        frames.append(sample * env * 0.18)
    return frames


class _VoiceCounter:
    def __init__(self, max_voices=DEFAULT_MAX_VOICES):
        self.max_voices = max_voices
        self.active_voices = 0

    def acquire(self):
        if self.active_voices >= self.max_voices:
            raise ValueError("voice limit exceeded")
        self.active_voices += 1

    def release(self):
        if self.active_voices:
            self.active_voices -= 1


class Synth:
    def __init__(self, context, max_voices=DEFAULT_MAX_VOICES):
        self.context = context
        self._voices = _VoiceCounter(max_voices)

    @property
    def active_voices(self):
        return self._voices.active_voices

    def _duration(self, duration):
        return to_seconds(
            duration,
            bpm=self.context.transport.bpm,
            time_signature=self.context.transport.time_signature,
            now=self.context.transport.seconds,
            ppq=self.context.transport.PPQ,
        )

    def _at_sample(self, time):
        if time is None:
            return self.context.sink.write_cursor
        seconds = to_seconds(
            time,
            bpm=self.context.transport.bpm,
            time_signature=self.context.transport.time_signature,
            now=self.context.transport.seconds,
            ppq=self.context.transport.PPQ,
        )
        return int(round(seconds * self.context.sample_rate))

    def trigger_attack(self, note, time=None):
        self._voices.acquire()
        freq = midi_to_hz(note_to_midi(note))
        frames = render_additive(freq, 1.0, self.context.sample_rate)
        self.context.sink.mix(frames, at_sample=self._at_sample(time))
        return self

    def trigger_release(self, note, time=None):
        del note, time
        self._voices.release()
        return self

    def trigger_attack_release(self, note, duration, time=None):
        self._voices.acquire()
        try:
            freq = midi_to_hz(note_to_midi(note))
            frames = render_additive(
                freq, self._duration(duration), self.context.sample_rate
            )
            self.context.sink.mix(frames, at_sample=self._at_sample(time))
        finally:
            self._voices.release()
        return self

    def release_all(self, time=None):
        del time
        self._voices.active_voices = 0
        return self


def render_kick(sample_rate, duration=0.22):
    n = max(1, int(round(duration * sample_rate)))
    frames = []
    for i in range(n):
        t = i / float(sample_rate)
        env = 1.0 - (i / float(n))
        freq = 150.0 * (40.0 / 150.0) ** (i / float(n))
        frames.append(math.sin(2.0 * math.pi * freq * t) * env * 0.7)
    return frames


def render_snare(sample_rate, duration=0.16):
    n = max(1, int(round(duration * sample_rate)))
    frames = []
    seed = 1234567
    for i in range(n):
        t = i / float(sample_rate)
        env = 1.0 - (i / float(n))
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        noise = (seed / 0x7FFFFFFF) * 2.0 - 1.0
        tone = math.sin(2.0 * math.pi * 180.0 * t)
        frames.append((0.65 * noise + 0.35 * tone) * env * 0.45)
    return frames


def render_hat(sample_rate, duration=0.05):
    n = max(1, int(round(duration * sample_rate)))
    frames = []
    seed = 7654321
    for i in range(n):
        env = 1.0 - (i / float(n))
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        noise = (seed / 0x7FFFFFFF) * 2.0 - 1.0
        frames.append(noise * env * 0.28)
    return frames


_DRUM_RENDERERS = {
    "kick": render_kick,
    "snare": render_snare,
    "hat": render_hat,
    "hi-hat": render_hat,
    "hihat": render_hat,
}


class Drum:
    def __init__(self, context, max_voices=DEFAULT_MAX_VOICES):
        self.context = context
        self._synth = Synth(context, max_voices=max_voices)

    @staticmethod
    def steps_per_bar(time_signature):
        num, den = time_signature
        return int(num * 16 / den)

    def trigger(self, name, time=None):
        key = str(name).lower()
        if key not in _DRUM_RENDERERS:
            raise ValueError("unknown drum: %r" % (name,))
        frames = _DRUM_RENDERERS[key](self.context.sample_rate)
        self.context.sink.mix(frames, at_sample=self._synth._at_sample(time))
        return self

    def trigger_attack(self, note, time=None):
        return self.trigger(note, time=time)

    def trigger_release(self, note, time=None):
        del note, time
        return self

    def trigger_attack_release(self, note, duration, time=None):
        del duration
        return self.trigger(note, time=time)

    def release_all(self, time=None):
        del time
        return self


def _resample(frames, src_rate, dst_rate):
    if src_rate == dst_rate:
        return list(frames)
    if not frames:
        return []
    ratio = float(src_rate) / float(dst_rate)
    n = int(round(len(frames) / ratio))
    out = []
    for i in range(n):
        pos = i * ratio
        lo = int(pos)
        hi = min(lo + 1, len(frames) - 1)
        frac = pos - lo
        out.append(frames[lo] * (1.0 - frac) + frames[hi] * frac)
    return out


def _pitch_shift(frames, semitones):
    if semitones == 0:
        return list(frames)
    ratio = 2.0 ** (semitones / 12.0)
    n = max(1, int(round(len(frames) / ratio)))
    out = []
    last = len(frames) - 1
    for i in range(n):
        pos = i * ratio
        lo = min(int(pos), last)
        hi = min(lo + 1, last)
        frac = pos - int(pos)
        out.append(frames[lo] * (1.0 - frac) + frames[hi] * frac)
    return out


def load_wav(path, sample_rate):
    with wave.open(path, "rb") as handle:
        channels = handle.getnchannels()
        width = handle.getsampwidth()
        rate = handle.getframerate()
        raw = handle.readframes(handle.getnframes())
    if width != 2:
        raise ValueError("WAV must be 16-bit")
    samples = list(struct.unpack("<%dh" % (len(raw) // 2), raw))
    if channels == 2:
        samples = [(samples[i] + samples[i + 1]) / 2.0 for i in range(0, len(samples), 2)]
    frames = [s / 32767.0 for s in samples]
    return _resample(frames, rate, sample_rate)


class Sampler:
    def __init__(self, context, urls=None, max_voices=DEFAULT_MAX_VOICES, loop=False):
        self.context = context
        self.loop = loop
        self._voices = _VoiceCounter(max_voices)
        self._samples = {}
        for note, path in (urls or {}).items():
            self.add(note, path)

    @classmethod
    def from_directory(cls, context, directory, **kwargs):
        sampler = cls(context, **kwargs)
        for name in os.listdir(directory):
            match = _WAV_NAME.match(name)
            if match:
                sampler.add(match.group(1), os.path.join(directory, name))
        return sampler

    def add(self, note, path):
        self._samples[note_to_midi(note)] = load_wav(path, self.context.sample_rate)
        return self

    def _nearest(self, midi):
        if not self._samples:
            raise ValueError("sampler has no samples")
        if midi in self._samples:
            return midi, self._samples[midi]
        nearest = min(self._samples, key=lambda key: abs(key - midi))
        return nearest, _pitch_shift(self._samples[nearest], midi - nearest)

    def trigger_attack(self, note, time=None):
        self._voices.acquire()
        midi = note_to_midi(note)
        _src, frames = self._nearest(midi)
        at = Synth(self.context)._at_sample(time)
        self.context.sink.mix(frames, at_sample=at)
        return self

    def trigger_release(self, note, time=None):
        del note, time
        self._voices.release()
        return self

    def trigger_attack_release(self, note, duration, time=None):
        self._voices.acquire()
        try:
            midi = note_to_midi(note)
            _src, frames = self._nearest(midi)
            synth = Synth(self.context)
            n = int(round(synth._duration(duration) * self.context.sample_rate))
            if n < len(frames):
                frames = frames[:n]
            at = synth._at_sample(time)
            self.context.sink.mix(frames, at_sample=at)
        finally:
            self._voices.release()
        return self

    def release_all(self, time=None):
        del time
        self._voices.active_voices = 0
        return self
