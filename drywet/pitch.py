import re

from drywet.limits import MIDI_MAX, MIDI_MIN

_NOTE_RE = re.compile(r"^([A-Ga-g])([#b]?)(-?\d+)$")
_SHARP = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_to_midi(note):
    if isinstance(note, int):
        if note < MIDI_MIN or note > MIDI_MAX:
            raise ValueError("MIDI must be 0–127")
        return note
    if not isinstance(note, str):
        raise ValueError("note must be str or int")
    match = _NOTE_RE.match(note.strip())
    if match is None:
        raise ValueError("invalid note: %r" % (note,))
    letter, acc, octave = match.group(1).upper(), match.group(2), int(match.group(3))
    pc = _SHARP[letter]
    if acc == "#":
        pc += 1
    elif acc == "b":
        pc -= 1
    midi = (octave + 1) * 12 + pc
    if midi < MIDI_MIN or midi > MIDI_MAX:
        raise ValueError("MIDI must be 0–127")
    return midi


def midi_to_hz(midi):
    midi = note_to_midi(midi)
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))
