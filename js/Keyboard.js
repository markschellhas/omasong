.pragma library

// Port of source LaptopKeys.h (QWERTY A=C …; Z/X octave).
// Piano.qml uses pianoKeysC3C5 (MIDI 48–72).

var DEFAULT_OCTAVE = 4
var MIN_OCTAVE = 0
var MAX_OCTAVE = 8

// Semitone from C. Z/X are octave keys, not notes.
var SEMITONE_FOR_KEY = {
  "a": 0,
  "w": 1,
  "s": 2,
  "e": 3,
  "d": 4,
  "f": 5,
  "t": 6,
  "g": 7,
  "y": 8,
  "h": 9,
  "u": 10,
  "j": 11,
  "k": 12,
  "o": 13,
  "l": 14,
  "p": 15,
  ";": 16,
  "'": 17
}

var KEY_FOR_SEMITONE = {
  0: "a",
  1: "w",
  2: "s",
  3: "e",
  4: "d",
  5: "f",
  6: "t",
  7: "g",
  8: "y",
  9: "h",
  10: "u",
  11: "j",
  12: "k",
  13: "o",
  14: "l",
  15: "p",
  16: ";",
  17: "'"
}

function normalizeLaptopKey(key) {
  if (key === undefined || key === null)
    return ""
  return String(key).toLowerCase()
}

function semitoneForKey(key) {
  var st = SEMITONE_FOR_KEY[normalizeLaptopKey(key)]
  return st === undefined ? -1 : st
}

function clampOctave(octave) {
  var n = Number(octave)
  if (!isFinite(n))
    return DEFAULT_OCTAVE
  n = Math.floor(n)
  if (n < MIN_OCTAVE)
    return MIN_OCTAVE
  if (n > MAX_OCTAVE)
    return MAX_OCTAVE
  return n
}

function clampMidi(midi) {
  var n = Number(midi)
  if (!isFinite(n))
    return 0
  n = Math.floor(n)
  if (n < 0)
    return 0
  if (n > 127)
    return 127
  return n
}

function sanitizeMidiNotes(notes, maxCount) {
  var cap = Number(maxCount)
  if (!isFinite(cap) || cap < 1)
    cap = 8
  cap = Math.floor(cap)
  if (cap > 16)
    cap = 16
  if (!notes || !notes.length)
    return []
  var out = []
  for (var i = 0; i < notes.length && out.length < cap; i++) {
    var n = Number(notes[i])
    if (!isFinite(n))
      continue
    n = Math.round(n)
    if (n < 0 || n > 127)
      continue
    if (out.indexOf(n) === -1)
      out.push(n)
  }
  return out
}

function clampSeconds(seconds, fallback) {
  var def = Number(fallback)
  if (!isFinite(def) || def <= 0)
    def = 0.7
  var n = Number(seconds)
  if (!isFinite(n) || n <= 0)
    return def
  if (n < 0.05)
    return 0.05
  if (n > 30)
    return 30
  return n
}

function shiftOctave(octave, delta) {
  return clampOctave(Number(octave) + Number(delta))
}

function midiForLaptopKey(key, octave) {
  var st = semitoneForKey(key)
  if (st < 0)
    return -1
  return clampMidi((clampOctave(octave) + 1) * 12 + st)
}

function midiForKey(key, octave, layoutName) {
  return midiForLaptopKey(key, octave)
}

function computerKeyForMidi(midi, octave, layoutName) {
  var cMidi = (clampOctave(octave) + 1) * 12
  var key = KEY_FOR_SEMITONE[midi - cMidi]
  return key || ""
}

function midiToHz(midi) {
  return 440 * Math.pow(2, (midi - 69) / 12)
}

var PIANO_KEY_META = [
  { note: "C", type: "white", keyIndex: 0 },
  { note: "C#", type: "black", keyIndex: 0.5 },
  { note: "D", type: "white", keyIndex: 1 },
  { note: "D#", type: "black", keyIndex: 1.5 },
  { note: "E", type: "white", keyIndex: 2 },
  { note: "F", type: "white", keyIndex: 3 },
  { note: "F#", type: "black", keyIndex: 3.5 },
  { note: "G", type: "white", keyIndex: 4 },
  { note: "G#", type: "black", keyIndex: 4.5 },
  { note: "A", type: "white", keyIndex: 5 },
  { note: "A#", type: "black", keyIndex: 5.5 },
  { note: "B", type: "white", keyIndex: 6 }
]

var NOTE_OFFSET = { "C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11 }

function pianoKeyAt(octave, meta) {
  var midi = (octave + 1) * 12 + NOTE_OFFSET[meta.note]
  return {
    note: meta.note,
    type: meta.type,
    keyIndex: meta.keyIndex,
    octave: octave,
    midi: midi,
    label: meta.note + octave
  }
}

function pianoKeysC3C5() {
  var keys = []
  var oct
  var i
  for (oct = 3; oct <= 4; oct++) {
    for (i = 0; i < PIANO_KEY_META.length; i++)
      keys.push(pianoKeyAt(oct, PIANO_KEY_META[i]))
  }
  keys.push(pianoKeyAt(5, PIANO_KEY_META[0]))
  return keys
}

var WHITE_KEYS_C3_C5 = 15

function blackKeyLeftPercent(keyIndex, octaveOffset) {
  var whitesBefore = {
    "0.5": 1,
    "1.5": 2,
    "3.5": 4,
    "4.5": 5,
    "5.5": 6
  }
  var n = whitesBefore[String(keyIndex)]
  if (n === undefined)
    n = 0
  return (n + octaveOffset) * (100 / WHITE_KEYS_C3_C5)
}

var INSTRUMENT_NAMES = ["Piano", "Electric Piano", "Organ", "Pad", "Strings"]

function clampInstrument(index) {
  var n = Number(index)
  if (!isFinite(n))
    return 0
  n = Math.floor(n)
  if (n < 0)
    return 0
  if (n > INSTRUMENT_NAMES.length - 1)
    return INSTRUMENT_NAMES.length - 1
  return n
}

function wrapInstrument(index) {
  var n = Number(index)
  if (!isFinite(n))
    n = 0
  n = Math.floor(n)
  var len = INSTRUMENT_NAMES.length
  n = n % len
  if (n < 0)
    n += len
  return n
}

function instrumentName(index) {
  return INSTRUMENT_NAMES[wrapInstrument(index)]
}
