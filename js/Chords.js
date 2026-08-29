.pragma library

// Port of the Chords & Tabs / songwriter chord parser for QML.
// Parses chord symbols and returns MIDI notes + display names.

var NOTE_NUMBERS = {
  "C": 60, "C#": 61, "Db": 61, "D": 62, "D#": 63, "Eb": 63,
  "E": 64, "F": 65, "F#": 66, "Gb": 66, "G": 67, "G#": 68,
  "Ab": 68, "A": 69, "A#": 70, "Bb": 70, "B": 71
}

var MIDI_TO_NOTE = [
  "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
]

var INTERVALS = {
  major: [0, 4, 7],
  minor: [0, 3, 7],
  diminished: [0, 3, 6],
  augmented: [0, 4, 8],
  sus2: [0, 2, 7],
  sus4: [0, 5, 7]
}

function midiToHz(midi) {
  return 440 * Math.pow(2, (midi - 69) / 12)
}

function midiToNoteName(midiNote) {
  var noteNumber = ((midiNote % 12) + 12) % 12
  var octave = Math.floor(midiNote / 12) - 1
  return MIDI_TO_NOTE[noteNumber] + octave
}

function normalizeAccidental(ch) {
  if (ch === "♯") return "#"
  if (ch === "♭") return "b"
  return ch
}

function isNoteLetter(ch) {
  return "ABCDEFG".indexOf(String(ch || "").toUpperCase()) !== -1
}

function isValidNoteName(name) {
  if (!name || typeof name !== "string")
    return false
  var trimmed = name.trim()
  if (!trimmed)
    return false
  if (!isNoteLetter(trimmed.charAt(0)))
    return false
  if (trimmed.length === 1)
    return true
  var acc = normalizeAccidental(trimmed.charAt(1))
  if (acc !== "#" && acc !== "b")
    return false
  return trimmed.length === 2
}

function eatPrefix(state, token, ignoreCase) {
  if (!token || state.text.length < token.length)
    return false
  var head = state.text.slice(0, token.length)
  if (ignoreCase) {
    if (head.toLowerCase() !== token.toLowerCase())
      return false
  } else if (head !== token) {
    return false
  }
  state.text = state.text.slice(token.length)
  return true
}

function pushUnique(list, value) {
  if (list.indexOf(value) === -1)
    list.push(value)
}

function parseQualityAndExtensions(raw) {
  var state = { text: raw || "" }
  var quality = "major"
  var extensions = []

  function eat(token) {
    return eatPrefix(state, token, true)
  }

  function eatExact(token) {
    return eatPrefix(state, token, false)
  }

  function eatExtensionToken() {
    if (eat("maj7") || eat("ma7") || eatExact("Δ7") || eatExact("Δ") || eatExact("M7")) {
      if (extensions.indexOf("7") !== -1)
        extensions = extensions.filter(function(e) { return e !== "7" })
      pushUnique(extensions, "maj7")
      return true
    }
    if (eat("add13")) { pushUnique(extensions, "add13"); return true }
    if (eat("add11")) { pushUnique(extensions, "add11"); return true }
    if (eat("add9")) { pushUnique(extensions, "add9"); return true }
    if (eat("sus4")) { quality = "sus4"; return true }
    if (eat("sus2")) { quality = "sus2"; return true }
    if (eat("sus")) { quality = "sus4"; return true }
    if (eat("13")) { pushUnique(extensions, "13"); return true }
    if (eat("11")) { pushUnique(extensions, "11"); return true }
    if (eat("9")) { pushUnique(extensions, "9"); return true }
    if (eat("7")) { pushUnique(extensions, "7"); return true }
    if (eat("6")) { pushUnique(extensions, "6"); return true }
    return false
  }

  if (state.text === "")
    return { isValid: true, quality: quality, extensions: extensions }

  if (eat("dim7") || eatExact("°7") || eat("o7")) {
    quality = "diminished"
    pushUnique(extensions, "7")
  } else if (eat("diminished") || eat("dim") || eatExact("°") || eatExact("o") || eat("o")) {
    quality = "diminished"
  } else if (eat("augmented") || eat("aug") || eatExact("+")) {
    quality = "augmented"
  } else if (eat("sus4")) {
    quality = "sus4"
  } else if (eat("sus2")) {
    quality = "sus2"
  } else if (eat("sus")) {
    quality = "sus4"
  } else if (eat("minmaj7") || eat("mmaj7") || eat("minmaj") || eat("mmaj")) {
    quality = "minor"
    pushUnique(extensions, "maj7")
  } else if (eat("maj7") || eat("ma7") || eatExact("Δ7") || eatExact("Δ") || eatExact("M7")) {
    quality = "major"
    pushUnique(extensions, "maj7")
  } else if (eat("min7") || eat("mi7") || eat("-7")) {
    quality = "minor"
    pushUnique(extensions, "7")
  } else if (eat("m7")) {
    quality = "minor"
    pushUnique(extensions, "7")
  } else if (eat("min9") || eat("m9")) {
    quality = "minor"
    pushUnique(extensions, "9")
  } else if (eat("minor") || eat("min") || eatExact("m") || eat("-")) {
    quality = "minor"
  } else if (eat("major") || eat("maj") || eatExact("M")) {
    quality = "major"
  }

  while (state.text.length > 0) {
    if (!eatExtensionToken())
      return { isValid: false, error: "Invalid chord quality" }
  }

  return { isValid: true, quality: quality, extensions: extensions }
}

function parseChordComponents(symbol) {
  var root = symbol.charAt(0).toUpperCase()
  if (!isNoteLetter(root)) {
    return { isValid: false, error: "Invalid root note" }
  }

  var remaining = symbol.slice(1)
  var accidental = ""

  if (remaining.length > 0) {
    var first = normalizeAccidental(remaining.charAt(0))
    if (first === "#" || first === "b") {
      accidental = first
      remaining = remaining.slice(1)
    }
  }

  var bass = null
  var slashIndex = remaining.indexOf("/")
  if (slashIndex !== -1) {
    bass = remaining.slice(slashIndex + 1)
    remaining = remaining.slice(0, slashIndex)
    if (!isValidNoteName(bass))
      return { isValid: false, error: "Invalid bass note" }
    var bassAcc = bass.length > 1 ? normalizeAccidental(bass.charAt(1)) : ""
    bass = bass.charAt(0).toUpperCase() + (bassAcc === "#" || bassAcc === "b" ? bassAcc : bass.slice(1))
  }

  var parsed = parseQualityAndExtensions(remaining)
  if (!parsed.isValid)
    return { isValid: false, error: parsed.error || "Invalid chord quality" }

  return {
    isValid: true,
    root: root,
    accidental: accidental,
    quality: parsed.quality,
    extensions: parsed.extensions,
    bass: bass
  }
}

function getChordIntervals(quality, extensions) {
  var intervals = []
  if (quality === "minor")
    intervals = INTERVALS.minor.slice()
  else if (quality === "diminished")
    intervals = INTERVALS.diminished.slice()
  else if (quality === "augmented")
    intervals = INTERVALS.augmented.slice()
  else if (quality === "sus2")
    intervals = INTERVALS.sus2.slice()
  else if (quality === "sus4")
    intervals = INTERVALS.sus4.slice()
  else
    intervals = INTERVALS.major.slice()

  for (var i = 0; i < extensions.length; i++) {
    var extension = extensions[i]
    if (extension === "7") {
      if (quality === "diminished")
        intervals.push(9)
      else
        intervals.push(10)
    } else if (extension === "maj7") {
      intervals.push(11)
    } else if (extension === "6") {
      intervals.push(9)
    } else if (extension === "9") {
      intervals.push(14)
      if (intervals.indexOf(10) === -1 && intervals.indexOf(11) === -1)
        intervals.push(10)
    } else if (extension === "add9") {
      intervals.push(14)
    } else if (extension === "11") {
      intervals.push(17)
      if (intervals.indexOf(10) === -1 && intervals.indexOf(11) === -1)
        intervals.push(10)
      if (intervals.indexOf(14) === -1)
        intervals.push(14)
    } else if (extension === "add11") {
      intervals.push(17)
    } else if (extension === "13") {
      intervals.push(21)
      if (intervals.indexOf(10) === -1 && intervals.indexOf(11) === -1)
        intervals.push(10)
      if (intervals.indexOf(14) === -1)
        intervals.push(14)
    } else if (extension === "add13") {
      intervals.push(21)
    }
  }

  return intervals
}

function noteLookup(name) {
  if (!name) return undefined
  var n = name.charAt(0).toUpperCase()
  var rest = name.slice(1)
  if (rest.length > 0)
    rest = normalizeAccidental(rest.charAt(0)) + rest.slice(1)
  return NOTE_NUMBERS[n + rest]
}

function applyVoicing(notes, voicing) {
  var copy = notes.slice()
  if (voicing === "inversion1" && copy.length > 1) {
    var root = copy.shift()
    copy.push(root + 12)
  } else if (voicing === "inversion2" && copy.length > 2) {
    var r = copy.shift()
    var third = copy.shift()
    copy.push(r + 12)
    copy.push(third + 12)
  } else if (voicing === "spread") {
    return copy.map(function(note, index) {
      return note + Math.floor(index / 3) * 12
    })
  }
  return copy
}

function generateChordNotes(components, octave, voicing) {
  var rootNote = components.root + (components.accidental || "")
  var rootMidi = NOTE_NUMBERS[rootNote]
  if (rootMidi === undefined)
    return []
  rootMidi = rootMidi + (octave - 4) * 12

  var intervals = getChordIntervals(components.quality, components.extensions)
  var notes = intervals.map(function(interval) { return rootMidi + interval })

  if (components.bass) {
    var bassMidi = noteLookup(components.bass)
    if (bassMidi !== undefined) {
      bassMidi = bassMidi + (octave - 4) * 12
      var bassClass = ((bassMidi % 12) + 12) % 12
      notes = notes.filter(function(note) { return ((note % 12) + 12) % 12 !== bassClass })
      notes.unshift(bassMidi - 12)
    }
  }

  notes = applyVoicing(notes, voicing)
  var unique = []
  for (var i = 0; i < notes.length; i++) {
    if (unique.indexOf(notes[i]) === -1)
      unique.push(notes[i])
  }
  unique.sort(function(a, b) { return a - b })
  return unique
}

function parseChord(symbol, octave, voicing) {
  octave = octave === undefined ? 4 : octave
  voicing = voicing || "root"

  if (!symbol || typeof symbol !== "string") {
    return { isValid: false, chord: null, error: "Invalid chord symbol" }
  }

  var cleanSymbol = symbol.trim().replace(/\s+/g, "")
  if (cleanSymbol.toLowerCase() === "n.c." || cleanSymbol === "-" || cleanSymbol === "%") {
    return {
      isValid: true,
      chord: {
        symbol: cleanSymbol,
        root: "",
        quality: "silent",
        extensions: [],
        notes: [],
        noteNames: [],
        freqs: []
      }
    }
  }

  var components = parseChordComponents(cleanSymbol)
  if (!components.isValid) {
    return { isValid: false, chord: null, error: components.error }
  }

  var notes = generateChordNotes(components, octave, voicing)
  return {
    isValid: true,
    chord: {
      symbol: cleanSymbol,
      root: components.root,
      accidental: components.accidental,
      quality: components.quality,
      extensions: components.extensions,
      bass: components.bass,
      notes: notes,
      noteNames: notes.map(midiToNoteName),
      freqs: notes.map(midiToHz)
    }
  }
}

function isValidChord(symbol) {
  return parseChord(symbol).isValid
}

function getChordSuggestions(partial) {
  var suggestions = []
  var partialUpper = String(partial || "").toUpperCase()
  var commonChords = [
    "C", "Cm", "C7", "Cmaj7", "Dm", "Dm7", "Em", "Em7",
    "F", "Fmaj7", "G", "G7", "Am", "Am7", "Bdim", "B7",
    "D", "D7", "E", "E7", "A", "A7", "F#m", "F#m7",
    "Bm", "Bm7", "C#dim", "C#7", "F#", "F#7", "B", "Bmaj7",
    "Bb", "Bbm", "Eb", "Ab", "Db"
  ]
  for (var i = 0; i < commonChords.length; i++) {
    if (commonChords[i].toUpperCase().indexOf(partialUpper) === 0)
      suggestions.push(commonChords[i])
  }
  return suggestions.slice(0, 10)
}

function transposeChord(symbol, semitones) {
  var parsed = parseChord(symbol)
  if (!parsed.isValid || !parsed.chord || parsed.chord.quality === "silent")
    return symbol

  var chord = parsed.chord
  var rootNote = chord.root + (chord.accidental || "")
  var rootMidi = NOTE_NUMBERS[rootNote]
  if (rootMidi === undefined)
    return symbol
  var newRootMidi = ((rootMidi - 60 + semitones) % 12 + 12) % 12
  var newRootNote = MIDI_TO_NOTE[newRootMidi]
  var newSymbol = newRootNote

  if (chord.quality === "minor")
    newSymbol += "m"
  else if (chord.quality === "diminished")
    newSymbol += "dim"
  else if (chord.quality === "augmented")
    newSymbol += "aug"
  else if (chord.quality === "sus2")
    newSymbol += "sus2"
  else if (chord.quality === "sus4")
    newSymbol += "sus4"

  for (var i = 0; i < chord.extensions.length; i++)
    newSymbol += chord.extensions[i]

  if (chord.bass) {
    var bassMidi = noteLookup(chord.bass)
    if (bassMidi !== undefined) {
      var newBass = MIDI_TO_NOTE[((bassMidi - 60 + semitones) % 12 + 12) % 12]
      newSymbol += "/" + newBass
    }
  }

  return newSymbol
}

function transposeSemitones(fromTonicIndex, toTonicIndex, pitchClass) {
  var fromPc = pitchClass[fromTonicIndex]
  var toPc = pitchClass[toTonicIndex]
  return ((toPc - fromPc) % 12 + 12) % 12
}
