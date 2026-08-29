.pragma library

var WHITE_OFFSETS = [0, 2, 4, 5, 7, 9, 11]
var BLACK_OFFSETS = [1, 3, 6, 8, 10]

var LAYOUTS = {
  qwerty: {
    white: ["a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'"],
    black: ["w", "e", "r", "t", "y", "u", "i", "o", "p", "["]
  },
  dvorak: {
    white: ["a", "o", "e", "u", "i", "d", "h", "t", "n", "s", "-"],
    black: [",", ".", "p", "y", "f", "g", "c", "r", "l", "/"]
  },
  colemak: {
    white: ["a", "r", "s", "t", "d", "h", "n", "e", "i", "o", "'"],
    black: ["w", "f", "p", "g", "j", "l", "u", "y", ";", "["]
  }
}

var NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

function layoutNames() {
  return ["qwerty", "dvorak", "colemak"]
}

function getLayout(name) {
  return LAYOUTS[name] || LAYOUTS.qwerty
}

function midiForPc(octave, pc) {
  return (octaveBase(octave) + 1) * 12 + pc
}

function midiForWhite(octave, index) {
  if (index < 7)
    return midiForPc(octave, WHITE_OFFSETS[index])
  return midiForPc(octave + 1, WHITE_OFFSETS[index - 7])
}

function midiForBlack(octave, index) {
  if (index < 5)
    return midiForPc(octave, BLACK_OFFSETS[index])
  return midiForPc(octave + 1, BLACK_OFFSETS[index - 5])
}

function keyToMidiMap(octave, layoutName) {
  var layout = getLayout(layoutName)
  var map = {}
  var i
  for (i = 0; i < layout.white.length; i++)
    map[layout.white[i]] = midiForWhite(octave, i)
  for (i = 0; i < layout.black.length; i++)
    map[layout.black[i]] = midiForBlack(octave, i)
  return map
}

function midiForKey(key, octave, layoutName) {
  if (!key) return -1
  var map = keyToMidiMap(octave, layoutName)
  var k = String(key).toLowerCase()
  if (map[k] !== undefined)
    return map[k]
  if (map[key] !== undefined)
    return map[key]
  return -1
}

function noteName(midi) {
  if (midi < 0) return ""
  var pc = ((midi % 12) + 12) % 12
  var oct = Math.floor(midi / 12) - 1
  return NOTE_NAMES[pc] + oct
}

function isBlack(midi) {
  var pc = ((midi % 12) + 12) % 12
  return pc === 1 || pc === 3 || pc === 6 || pc === 8 || pc === 10
}

function computerKeyForMidi(midi, octave, layoutName) {
  var map = keyToMidiMap(octave, layoutName)
  for (var key in map) {
    if (map[key] === midi)
      return key
  }
  return ""
}

function octaveBase(baseOctave) {
  var n = Number(baseOctave)
  if (!isFinite(n)) return 4
  return Math.max(1, Math.min(7, Math.floor(n)))
}

function twoOctaveKeys(baseOctave) {
  var start = octaveBase(baseOctave)
  var keys = []
  var names = [
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
  var offsets = { "C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11 }
  for (var oct = 0; oct < 2; oct++) {
    for (var i = 0; i < names.length; i++) {
      var key = names[i]
      var midi = midiForPc(start + oct, offsets[key.note])
      keys.push({
        note: key.note,
        type: key.type,
        keyIndex: key.keyIndex,
        octave: start + oct,
        midi: midi,
        label: key.note + (start + oct)
      })
    }
  }
  return keys
}

function pianoKeys(octave) {
  return twoOctaveKeys(octave)
}

function blackKeyLeftPercent(keyIndex, octaveOffset) {
  var positions = {
    "0.5": 7.14,
    "1.5": 14.28,
    "3.5": 35.71,
    "4.5": 42.85,
    "5.5": 50.0
  }
  var base = positions[String(keyIndex)] || 0
  return base + octaveOffset * (100 / 14)
}

function clampOctave(octave) {
  return octaveBase(octave)
}

function midiToHz(midi) {
  return 440 * Math.pow(2, (midi - 69) / 12)
}
