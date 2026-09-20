import re

from drywet.limits import DEFAULT_PPQ, HZ_MAX, HZ_MIN
from drywet.pitch import midi_to_hz, note_to_midi

_NOTE_RE = re.compile(r"^(\+)?(\d+)([nmt])([.])?$")
_BBS_RE = re.compile(r"^(\d+):(\d+):(\d+(?:\.\d+)?)$")


def _quarter_seconds(bpm):
    return 60.0 / float(bpm)


def to_seconds(value, *, bpm, time_signature, now=0.0, ppq=DEFAULT_PPQ):
    del ppq
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, str):
        raise ValueError("invalid time: %r" % (value,))
    text = value.strip()
    num, den = time_signature
    quarter = _quarter_seconds(bpm)
    beat = quarter * (4.0 / den)
    bar = num * beat
    sixteenth = quarter / 4.0

    match = _BBS_RE.match(text)
    if match:
        bars = int(match.group(1))
        beats = int(match.group(2))
        sixteenths = float(match.group(3))
        return bars * bar + beats * beat + sixteenths * sixteenth

    match = _NOTE_RE.match(text)
    if match is None:
        raise ValueError("invalid time: %r" % (value,))
    relative = match.group(1) == "+"
    count = int(match.group(2))
    unit = match.group(3)
    suffix = match.group(4)
    if unit == "m":
        seconds = count * bar
    elif unit == "t":
        if count <= 0:
            raise ValueError("invalid time: %r" % (value,))
        seconds = (4.0 / count) * quarter * (2.0 / 3.0)
    else:
        if count <= 0:
            raise ValueError("invalid time: %r" % (value,))
        seconds = (4.0 / count) * quarter
        if suffix == ".":
            seconds *= 1.5
    if relative:
        seconds += float(now)
    return seconds


def to_ticks(value, *, bpm, time_signature, now=0.0, ppq=DEFAULT_PPQ):
    seconds = to_seconds(
        value, bpm=bpm, time_signature=time_signature, now=now, ppq=ppq
    )
    ticks_per_second = (float(bpm) / 60.0) * float(ppq)
    return int(round(seconds * ticks_per_second))


def to_frequency(value, *, bpm, time_signature, now=0.0, ppq=DEFAULT_PPQ):
    del bpm, time_signature, now, ppq
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        hz = float(value)
        if hz < HZ_MIN or hz > HZ_MAX:
            raise ValueError("Hz must be 20–20000")
        return hz
    return midi_to_hz(note_to_midi(value))
